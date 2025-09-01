"""
Async Utilities for MCP Protocol Handler with Performance Optimizations

This module provides high-performance async utilities for the MCP protocol handler,
including connection pooling, timeout management, error handling, and performance
monitoring optimized for high-concurrency scenarios.
"""
import asyncio
import time
import functools
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from contextlib import asynccontextmanager
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_settings
from mcp_core.shared.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

T = TypeVar('T')


class AsyncPerformanceMonitor:
    """Performance monitoring for async MCP operations with real-time metrics"""
    
    def __init__(self):
        self.operation_metrics: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def track_operation(
        self,
        operation_name: str,
        operation_type: str = "mcp_operation"
    ) -> Callable[[], None]:
        """Track async operation performance with context manager pattern"""
        start_time = time.time()
        
        async def finish_operation(success: bool = True, error: Optional[str] = None):
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            async with self._lock:
                if operation_name not in self.operation_metrics:
                    self.operation_metrics[operation_name] = {
                        "total_count": 0,
                        "success_count": 0,
                        "error_count": 0,
                        "total_duration_ms": 0.0,
                        "min_duration_ms": float('inf'),
                        "max_duration_ms": 0.0,
                        "last_executed": None
                    }
                
                metrics = self.operation_metrics[operation_name]
                metrics["total_count"] += 1
                metrics["total_duration_ms"] += duration_ms
                metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
                metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
                metrics["last_executed"] = datetime.now().isoformat()
                
                if success:
                    metrics["success_count"] += 1
                else:
                    metrics["error_count"] += 1
                
                # Log performance metrics for slow operations
                if duration_ms > settings.slow_request_threshold * 1000:
                    logger.warning(
                        f"Slow {operation_type} detected: {operation_name} - "
                        f"{duration_ms:.2f}ms (threshold: {settings.slow_request_threshold * 1000:.0f}ms)"
                    )
                
                # Log detailed metrics for debugging
                if settings.debug:
                    logger.debug(
                        f"{operation_type} '{operation_name}' completed in {duration_ms:.2f}ms - "
                        f"Success: {success}, Error: {error}"
                    )
        
        return finish_operation
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "operations": self.operation_metrics,
            "timestamp": datetime.now().isoformat(),
            "settings": {
                "slow_request_threshold_ms": settings.slow_request_threshold * 1000,
                "request_timeout": settings.request_timeout
            }
        }
    
    def reset_metrics(self):
        """Reset all performance metrics"""
        self.operation_metrics.clear()


class AsyncTimeoutManager:
    """Advanced timeout management for async MCP operations"""
    
    @staticmethod
    def with_timeout(
        timeout: float,
        operation_name: str,
        raise_on_timeout: bool = True
    ):
        """Async context manager for timeout handling with proper cleanup"""
        return asyncio.timeout(timeout)


class AsyncConnectionPool:
    """Connection pooling for async MCP operations with intelligent management"""
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self._semaphore = asyncio.Semaphore(max_connections)
        self._active_connections = 0
        self._connection_stats = {
            "total_acquired": 0,
            "total_released": 0,
            "max_concurrent": 0,
            "timeout_count": 0
        }
    
    @asynccontextmanager
    async def acquire_connection(self, timeout: Optional[float] = None):
        """Acquire a connection from the pool with optional timeout"""
        acquire_time = time.time()
        
        try:
            if timeout is not None:
                async with asyncio.timeout(timeout):
                    await self._semaphore.acquire()
            else:
                await self._semaphore.acquire()
            
            self._active_connections += 1
            self._connection_stats["total_acquired"] += 1
            self._connection_stats["max_concurrent"] = max(
                self._connection_stats["max_concurrent"], self._active_connections
            )
            
            acquire_duration = time.time() - acquire_time
            if acquire_duration > 0.1:  # Log slow acquisitions
                logger.warning(f"Slow connection acquisition: {acquire_duration:.3f}s")
            
            yield
            
        except asyncio.TimeoutError:
            self._connection_stats["timeout_count"] += 1
            logger.error(f"Connection acquisition timeout after {timeout}s")
            raise
            
        finally:
            self._active_connections -= 1
            self._connection_stats["total_released"] += 1
            self._semaphore.release()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            **self._connection_stats,
            "current_connections": self._active_connections,
            "max_connections": self.max_connections,
            "available_connections": self.max_connections - self._active_connections,
            "utilization_percentage": (self._active_connections / self.max_connections) * 100
        }


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retry_on: Union[type, tuple] = Exception
):
    """Decorator for async function retry with exponential backoff"""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            delay = initial_delay
            
            while True:
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    retries += 1
                    
                    if retries > max_retries:
                        logger.error(
                            f"Operation '{func.__name__}' failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    logger.warning(
                        f"Operation '{func.__name__}' failed (attempt {retries}/{max_retries}). "
                        f"Retrying in {delay:.1f}s: {e}"
                    )
                    
                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
                
        return wrapper
    return decorator


def run_in_threadpool(func: Callable[..., T]) -> Callable[..., Any]:
    """Run synchronous function in thread pool for async compatibility"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        loop = asyncio.get_event_loop()
        
        # Use default thread pool executor
        return await loop.run_in_executor(
            None, functools.partial(func, *args, **kwargs)
        )
    
    return wrapper


# Global instances for performance monitoring and connection management
performance_monitor = AsyncPerformanceMonitor()
connection_pool = AsyncConnectionPool(max_connections=settings.max_concurrent_requests)


async def notify_mcp_operation(
    operation_type: str,
    operation_id: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None
):
    """Send real-time notification for MCP operations via WebSocket"""
    try:
        from app.websockets.notifications import notification_service
        
        await notification_service.notify_mcp_operation(
            operation_type=operation_type,
            operation_id=operation_id,
            method=method,
            params=params,
            result=result,
            duration_ms=duration_ms,
            success=success,
            error=error
        )
    except ImportError:
        # WebSocket notifications not available
        pass
    except Exception as e:
        logger.warning(f"Failed to send MCP operation notification: {e}")


async def safe_async_execute(
    coroutine,
    operation_name: str,
    timeout: Optional[float] = None,
    default_value: Any = None
) -> Any:
    """Execute async operation safely with timeout and error handling"""
    if timeout is None:
        timeout = settings.request_timeout
    
    finish_operation = await performance_monitor.track_operation(operation_name)
    
    try:
        async with AsyncTimeoutManager.with_timeout(timeout, operation_name):
            result = await coroutine
            await finish_operation(success=True)
            return result
            
    except asyncio.TimeoutError:
        await finish_operation(success=False, error="timeout")
        logger.error(f"Operation '{operation_name}' timed out after {timeout}s")
        return default_value
        
    except Exception as e:
        await finish_operation(success=False, error=str(e))
        logger.error(f"Operation '{operation_name}' failed: {e}")
        return default_value