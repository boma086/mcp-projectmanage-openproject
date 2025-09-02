"""
Comprehensive Async Connection Pooling System

This module provides production-ready connection pooling for HTTP, database,
and Redis connections with advanced monitoring, health checks, and performance
optimizations for high-concurrency scenarios (1000+ users).
"""
import asyncio
import time
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import httpx
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Types of connection pools supported"""
    HTTP = "http"
    REDIS = "redis"
    DATABASE = "database"


@dataclass
class ConnectionStats:
    """Connection pool statistics and metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    max_connections: int = 0
    connection_wait_time_ms: float = 0.0
    connection_errors: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0


@dataclass
class PoolConfig:
    """Connection pool configuration"""
    max_connections: int = 100
    max_idle_connections: int = 20
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    health_check_interval: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


class ConnectionPool:
    """Base abstract connection pool class"""
    
    def __init__(self, config: PoolConfig, pool_type: ConnectionType):
        self.config = config
        self.pool_type = pool_type
        self.stats = ConnectionStats()
        self._lock = threading.Lock()
        self._last_health_check = time.time()
        self._is_healthy = True
        self._connection_queue = asyncio.Queue()
        
    async def acquire(self) -> Any:
        """Acquire a connection from the pool"""
        raise NotImplementedError
        
    async def release(self, connection: Any) -> None:
        """Release a connection back to the pool"""
        raise NotImplementedError
        
    async def health_check(self) -> bool:
        """Perform health check on the pool"""
        raise NotImplementedError
        
    async def close(self) -> None:
        """Close all connections in the pool"""
        raise NotImplementedError
        
    def get_stats(self) -> ConnectionStats:
        """Get current pool statistics"""
        with self._lock:
            return self.stats


class HTTPConnectionPool(ConnectionPool):
    """Async HTTP connection pool using httpx"""
    
    def __init__(self, config: PoolConfig):
        super().__init__(config, ConnectionType.HTTP)
        self._client: Optional[httpx.AsyncClient] = None
        
    async def acquire(self) -> httpx.AsyncClient:
        """Acquire an HTTP client from the pool"""
        start_time = time.time()
        
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=self.config.max_connections,
                    max_connections=self.config.max_connections,
                    keepalive_expiry=self.config.idle_timeout
                ),
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.config.connection_timeout,
                    write=10.0,
                    pool=5.0
                ),
                http2=True,
                follow_redirects=True
            )
        
        with self._lock:
            self.stats.total_connections = 1  # Single client with connection pooling
            self.stats.active_connections += 1
            self.stats.total_requests += 1
            self.stats.connection_wait_time_ms = (time.time() - start_time) * 1000
            
        return self._client
        
    async def release(self, client: httpx.AsyncClient) -> None:
        """Release HTTP client (no-op for single client pool)"""
        with self._lock:
            self.stats.active_connections = max(0, self.stats.active_connections - 1)
            
    async def health_check(self) -> bool:
        """Check if HTTP client is healthy"""
        try:
            if self._client is None:
                # Client hasn't been used yet, but that's okay - it will be created on demand
                self._is_healthy = True
            elif not self._client.is_closed:
                # Client exists and is not closed
                self._is_healthy = True
            else:
                # Client exists but is closed
                self._is_healthy = False
        except Exception as e:
            logger.warning(f"HTTP connection pool health check failed: {e}")
            self._is_healthy = False
            
        self._last_health_check = time.time()
        return self._is_healthy
        
    async def close(self) -> None:
        """Close the HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


class RedisConnectionPool(ConnectionPool):
    """Async Redis connection pool using aioredis"""
    
    def __init__(self, config: PoolConfig, redis_url: str):
        super().__init__(config, ConnectionType.REDIS)
        self.redis_url = redis_url
        self._pool: Optional[Any] = None
        self._redis: Optional[Any] = None
        
    async def acquire(self) -> Any:
        """Acquire a Redis connection from the pool"""
        start_time = time.time()
        
        try:
            import aioredis
            if self._redis is None:
                self._pool = aioredis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.config.max_connections,
                    timeout=self.config.connection_timeout,
                    retry_on_timeout=True,
                    health_check_interval=self.config.health_check_interval
                )
                self._redis = aioredis.Redis(connection_pool=self._pool)
        except ImportError:
            logger.warning("aioredis not installed, Redis connection pool disabled")
            return None
        
        with self._lock:
            self.stats.total_connections = self.config.max_connections
            self.stats.connection_wait_time_ms = (time.time() - start_time) * 1000
            
        return self._redis
        
    async def release(self, redis: Any) -> None:
        """Release Redis connection (managed by aioredis pool)"""
        # aioredis connection pool handles release automatically
        pass
        
    async def health_check(self) -> bool:
        """Check if Redis connection is healthy"""
        try:
            import aioredis
            if self._redis:
                result = await self._redis.ping()
                self._is_healthy = result == b"PONG"
            else:
                self._is_healthy = False
        except Exception as e:
            logger.warning(f"Redis connection pool health check failed: {e}")
            self._is_healthy = False
            
        self._last_health_check = time.time()
        return self._is_healthy
        
    async def close(self) -> None:
        """Close the Redis connection pool"""
        try:
            import aioredis
            if self._redis:
                await self._redis.close()
            if self._pool:
                await self._pool.disconnect()
        except ImportError:
            pass


class DatabaseConnectionPool(ConnectionPool):
    """Async database connection pool using SQLAlchemy"""
    
    def __init__(self, config: PoolConfig, database_url: str):
        super().__init__(config, ConnectionType.DATABASE)
        self.database_url = database_url
        self._engine: Optional[Any] = None
        self._async_session: Optional[Any] = None
        
    async def acquire(self) -> Any:
        """Acquire a database session from the pool"""
        start_time = time.time()
        
        try:
            from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
            from sqlalchemy.orm import sessionmaker
            from sqlalchemy.pool import AsyncAdaptedQueuePool
            
            if self._engine is None:
                self._engine = create_async_engine(
                    self.database_url,
                    poolclass=AsyncAdaptedQueuePool,
                    pool_size=self.config.max_connections,
                    max_overflow=self.config.max_idle_connections,
                    pool_timeout=self.config.connection_timeout,
                    pool_recycle=self.config.idle_timeout,
                    echo=False
                )
                self._async_session = sessionmaker(
                    self._engine, class_=AsyncSession, expire_on_commit=False
                )
            
            session = self._async_session()
            
            with self._lock:
                self.stats.total_connections = self.config.max_connections
                self.stats.active_connections += 1
                self.stats.connection_wait_time_ms = (time.time() - start_time) * 1000
                
            return session
            
        except ImportError:
            logger.warning("SQLAlchemy not installed, database connection pool disabled")
            return None
        
    async def release(self, session: Any) -> None:
        """Release a database session back to the pool"""
        try:
            await session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {e}")
        finally:
            with self._lock:
                self.stats.active_connections = max(0, self.stats.active_connections - 1)
        
    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            from sqlalchemy.ext.asyncio import AsyncEngine
            if self._engine:
                async with self._engine.connect() as conn:
                    result = await conn.scalar("SELECT 1")
                    self._is_healthy = result == 1
            else:
                self._is_healthy = False
        except Exception as e:
            logger.warning(f"Database connection pool health check failed: {e}")
            self._is_healthy = False
            
        self._last_health_check = time.time()
        return self._is_healthy
        
    async def close(self) -> None:
        """Close the database connection pool"""
        try:
            from sqlalchemy.ext.asyncio import AsyncEngine
            if self._engine:
                await self._engine.dispose()
        except ImportError:
            pass


class ConnectionPoolManager:
    """Central manager for all connection pools with monitoring and health checks"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._pools: Dict[ConnectionType, ConnectionPool] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False
        
    async def initialize(self) -> None:
        """Initialize all connection pools"""
        logger.info("Initializing connection pools...")
        
        # HTTP connection pool
        http_config = PoolConfig(
            max_connections=self.settings.http_client_max_connections,
            max_idle_connections=self.settings.http_client_max_keepalive,
            connection_timeout=self.settings.http_client_timeout,
            idle_timeout=self.settings.http_client_keepalive_expiry,
            health_check_interval=30.0
        )
        self._pools[ConnectionType.HTTP] = HTTPConnectionPool(http_config)
        
        # Redis connection pool (if configured)
        if self.settings.redis_url and self.settings.cache_enabled:
            redis_config = PoolConfig(
                max_connections=self.settings.cache_max_connections,
                connection_timeout=self.settings.cache_timeout,
                health_check_interval=30.0
            )
            self._pools[ConnectionType.REDIS] = RedisConnectionPool(redis_config, self.settings.redis_url)
        
        # Database connection pool (if configured)
        if self.settings.database_url:
            db_config = PoolConfig(
                max_connections=self.settings.database_pool_size,
                max_idle_connections=self.settings.database_max_overflow,
                connection_timeout=self.settings.database_pool_timeout,
                idle_timeout=300.0,
                health_check_interval=60.0
            )
            self._pools[ConnectionType.DATABASE] = DatabaseConnectionPool(db_config, self.settings.database_url)
        
        # Start monitoring task
        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitor_pools())
        
        logger.info(f"Connection pools initialized: {list(self._pools.keys())}")
    
    async def get_pool(self, pool_type: ConnectionType) -> Optional[ConnectionPool]:
        """Get a specific connection pool"""
        return self._pools.get(pool_type)
    
    @asynccontextmanager
    async def acquire_connection(self, pool_type: ConnectionType):
        """Context manager for acquiring and releasing connections"""
        pool = self._pools.get(pool_type)
        if not pool:
            raise ValueError(f"Connection pool not available: {pool_type}")
        
        connection = None
        try:
            connection = await pool.acquire()
            yield connection
        finally:
            if connection:
                await pool.release(connection)
    
    async def health_check_all(self) -> Dict[ConnectionType, bool]:
        """Perform health check on all pools"""
        results = {}
        for pool_type, pool in self._pools.items():
            try:
                results[pool_type] = await pool.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {pool_type}: {e}")
                results[pool_type] = False
        return results
    
    def get_all_stats(self) -> Dict[ConnectionType, ConnectionStats]:
        """Get statistics for all pools"""
        return {pool_type: pool.get_stats() for pool_type, pool in self._pools.items()}
    
    async def _monitor_pools(self) -> None:
        """Background task to monitor pool health and collect metrics"""
        while self._is_running:
            try:
                # Perform periodic health checks
                health_status = await self.health_check_all()
                
                # Log unhealthy pools
                for pool_type, is_healthy in health_status.items():
                    if not is_healthy:
                        logger.warning(f"Connection pool {pool_type} is unhealthy")
                
                # Collect and log statistics
                stats = self.get_all_stats()
                for pool_type, pool_stats in stats.items():
                    logger.debug(f"Pool {pool_type} stats: {pool_stats}")
                
                # Wait before next check
                await asyncio.sleep(30.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Pool monitoring task failed: {e}")
                await asyncio.sleep(10.0)
    
    async def close_all(self) -> None:
        """Close all connection pools"""
        self._is_running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        for pool_type, pool in self._pools.items():
            try:
                await pool.close()
                logger.info(f"Closed {pool_type} connection pool")
            except Exception as e:
                logger.error(f"Error closing {pool_type} pool: {e}")
        
        logger.info("All connection pools closed")


# Global connection pool manager instance
_connection_pool_manager: Optional[ConnectionPoolManager] = None


def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager instance"""
    global _connection_pool_manager
    if _connection_pool_manager is None:
        settings = get_settings()
        _connection_pool_manager = ConnectionPoolManager(settings)
    return _connection_pool_manager


async def initialize_connection_pools() -> None:
    """Initialize all connection pools (call during application startup)"""
    manager = get_connection_pool_manager()
    await manager.initialize()


async def close_connection_pools() -> None:
    """Close all connection pools (call during application shutdown)"""
    global _connection_pool_manager
    if _connection_pool_manager:
        await _connection_pool_manager.close_all()
        _connection_pool_manager = None


# Dependency for FastAPI
async def get_connection_pool_manager_dep() -> ConnectionPoolManager:
    """Dependency to get connection pool manager"""
    return get_connection_pool_manager()
