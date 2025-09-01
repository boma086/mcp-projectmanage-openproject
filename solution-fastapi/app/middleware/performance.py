"""
Performance Middleware for FastAPI Application

This module provides comprehensive performance monitoring, rate limiting,
caching, and optimization middleware for high-concurrency FastAPI applications.
"""
import asyncio
import time
import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass
from contextlib import asynccontextmanager
from functools import wraps
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Message, Scope, Receive, Send
from starlette.responses import Response
from starlette.concurrency import iterate_in_threadpool

from app.core.config import Settings, get_settings
from app.core.connection_pool import ConnectionPoolManager, get_connection_pool_manager, ConnectionType

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Request performance metrics"""
    request_id: str
    method: str
    path: str
    start_time: float
    end_time: Optional[float] = None
    processing_time_ms: Optional[float] = None
    status_code: Optional[int] = None
    response_size_bytes: Optional[int] = None
    cache_hit: bool = False
    rate_limited: bool = False
    error: Optional[str] = None


@dataclass
class RateLimitInfo:
    """Rate limiting information"""
    remaining: int
    reset_time: float
    limit: int
    window: int


class AsyncPerformanceMiddleware(BaseHTTPMiddleware):
    """Comprehensive async performance monitoring middleware"""
    
    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.request_metrics: Dict[str, RequestMetrics] = {}
        self._rate_limit_store: Dict[str, List[float]] = {}
        self._cache_store: Dict[str, Any] = {}
        self._active_requests: Set[str] = set()
        self._metrics_lock = asyncio.Lock()
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with comprehensive performance monitoring"""
        start_time = time.time()
        request_id = self._generate_request_id()
        
        # Add request ID to headers for tracing
        if hasattr(request.headers, '__dict__') and 'headers' in request.headers.__dict__:
            request.headers.__dict__["headers"].append((b"x-request-id", request_id.encode()))
        
        # Check rate limiting
        if self.settings.rate_limit_enabled:
            rate_limit_info = await self._check_rate_limit(request)
            if rate_limit_info.remaining <= 0:
                return self._create_rate_limit_response(rate_limit_info)
        
        # Check cache for GET requests
        cache_key = None
        if request.method == "GET" and self.settings.cache_enabled:
            cache_key = self._generate_cache_key(request)
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                metrics = RequestMetrics(
                    request_id=request_id,
                    method=request.method,
                    path=str(request.url.path),
                    start_time=start_time,
                    end_time=time.time(),
                    processing_time_ms=(time.time() - start_time) * 1000,
                    status_code=200,
                    cache_hit=True
                )
                await self._record_metrics(metrics)
                return cached_response
        
        # Process the request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000
            
            # Record metrics
            metrics = RequestMetrics(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                start_time=start_time,
                end_time=end_time,
                processing_time_ms=processing_time_ms,
                status_code=response.status_code,
                response_size_bytes=await self._get_response_size(response),
                cache_hit=False
            )
            await self._record_metrics(metrics)
            
            # Cache successful GET responses
            if (cache_key and 
                request.method == "GET" and 
                response.status_code == 200 and 
                self.settings.cache_enabled):
                await self._set_cache(cache_key, response)
            
            # Add performance headers
            response.headers["X-Process-Time"] = f"{processing_time_ms:.2f}ms"
            response.headers["X-Request-ID"] = request_id
            
            # Log slow requests
            if processing_time_ms > self.settings.slow_request_threshold * 1000:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} - "
                    f"{processing_time_ms:.2f}ms - Request ID: {request_id}"
                )
            
            return response
            
        except Exception as e:
            # Record error metrics
            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000
            
            metrics = RequestMetrics(
                request_id=request_id,
                method=request.method,
                path=str(request.url.path),
                start_time=start_time,
                end_time=end_time,
                processing_time_ms=processing_time_ms,
                status_code=500,
                error=str(e)
            )
            await self._record_metrics(metrics)
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} - "
                f"{processing_time_ms:.2f}ms - Error: {e} - Request ID: {request_id}"
            )
            
            raise
    
    async def _check_rate_limit(self, request: Request) -> RateLimitInfo:
        """Check and enforce rate limits"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # Clean up old timestamps
        window_start = current_time - self.settings.rate_limit_window
        if client_ip in self._rate_limit_store:
            self._rate_limit_store[client_ip] = [
                ts for ts in self._rate_limit_store[client_ip] 
                if ts > window_start
            ]
        else:
            self._rate_limit_store[client_ip] = []
        
        # Check current rate
        remaining = self.settings.rate_limit_requests - len(self._rate_limit_store[client_ip])
        reset_time = window_start + self.settings.rate_limit_window
        
        return RateLimitInfo(
            remaining=remaining,
            reset_time=reset_time,
            limit=self.settings.rate_limit_requests,
            window=self.settings.rate_limit_window
        )
    
    def _create_rate_limit_response(self, rate_limit_info: RateLimitInfo) -> Response:
        """Create rate limit exceeded response"""
        import math
        
        retry_after = math.ceil(rate_limit_info.reset_time - time.time())
        
        return Response(
            content=json.dumps({
                "error": "rate_limit_exceeded",
                "message": "Too many requests",
                "retry_after": retry_after,
                "limit": rate_limit_info.limit,
                "window": rate_limit_info.window
            }),
            status_code=429,
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(rate_limit_info.limit),
                "X-RateLimit-Remaining": str(max(0, rate_limit_info.remaining)),
                "X-RateLimit-Reset": str(int(rate_limit_info.reset_time))
            },
            media_type="application/json"
        )
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Response]:
        """Get response from cache"""
        try:
            if cache_key in self._cache_store:
                cached_data = self._cache_store[cache_key]
                if time.time() < cached_data["expires"]:
                    return cached_data["response"]
                else:
                    # Remove expired cache entry
                    del self._cache_store[cache_key]
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None
    
    async def _set_cache(self, cache_key: str, response: Response) -> None:
        """Store response in cache"""
        try:
            # Clone the response for caching
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            cached_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            self._cache_store[cache_key] = {
                "response": cached_response,
                "expires": time.time() + self.settings.cache_ttl,
                "created": time.time()
            }
            
            # Restore the original response
            response.body_iterator = iterate_in_threadpool(iter([response_body]))
            
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        key_parts = [
            request.method,
            str(request.url),
            request.headers.get("accept-language", ""),
            request.headers.get("authorization", "")[:20]  # Partial for key uniqueness
        ]
        return hashlib.md5(":".join(key_parts).encode()).hexdigest()
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def _get_response_size(self, response: Response) -> int:
        """Calculate response size in bytes"""
        size = 0
        if hasattr(response, "body") and response.body:
            size += len(response.body)
        elif hasattr(response, "body_iterator"):
            async for chunk in response.body_iterator:
                size += len(chunk)
            # Restore the iterator
            response.body_iterator = iterate_in_threadpool(iter([chunk]))
        return size
    
    async def _record_metrics(self, metrics: RequestMetrics) -> None:
        """Record request metrics"""
        async with self._metrics_lock:
            self.request_metrics[metrics.request_id] = metrics
            
            # Clean up old metrics (keep last 1000 requests)
            if len(self.request_metrics) > 1000:
                # Remove oldest metrics
                oldest_ids = sorted(
                    self.request_metrics.keys(), 
                    key=lambda x: self.request_metrics[x].start_time
                )[:len(self.request_metrics) - 1000]
                for old_id in oldest_ids:
                    del self.request_metrics[old_id]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self._metrics_lock:
            recent_metrics = list(self.request_metrics.values())[-100:]  # Last 100 requests
            
            if not recent_metrics:
                return {"total_requests": 0}
            
            processing_times = [m.processing_time_ms for m in recent_metrics if m.processing_time_ms]
            status_codes = [m.status_code for m in recent_metrics if m.status_code]
            
            return {
                "total_requests": len(recent_metrics),
                "avg_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0,
                "p95_processing_time_ms": sorted(processing_times)[int(len(processing_times) * 0.95)] if processing_times else 0,
                "p99_processing_time_ms": sorted(processing_times)[int(len(processing_times) * 0.99)] if processing_times else 0,
                "success_rate": sum(1 for code in status_codes if code < 400) / len(status_codes) if status_codes else 0,
                "cache_hit_rate": sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics),
                "active_requests": len(self._active_requests)
            }


class AsyncCachingMiddleware(BaseHTTPMiddleware):
    """Advanced async caching middleware with Redis support"""
    
    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self._redis_pool = None
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with advanced caching"""
        # Only cache GET requests
        if request.method != "GET" or not self.settings.cache_enabled:
            return await call_next(request)
        
        cache_key = self._generate_cache_key(request)
        
        # Try to get from cache
        cached_response = await self._get_cached_response(cache_key)
        if cached_response:
            return cached_response
        
        # Process request and cache response
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(cache_key, response)
        
        return response
    
    async def _get_cached_response(self, cache_key: str) -> Optional[Response]:
        """Get cached response from Redis or memory"""
        try:
            if self.settings.redis_url:
                # Use Redis for distributed caching
                redis = await self._get_redis_connection()
                cached_data = await redis.get(cache_key)
                if cached_data:
                    return self._deserialize_response(cached_data)
            else:
                # Fallback to in-memory cache
                # (Implementation similar to PerformanceMiddleware)
                pass
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None
    
    async def _cache_response(self, cache_key: str, response: Response) -> None:
        """Cache response in Redis or memory"""
        try:
            serialized = self._serialize_response(response)
            
            if self.settings.redis_url:
                redis = await self._get_redis_connection()
                await redis.setex(
                    cache_key, 
                    self.settings.cache_ttl, 
                    serialized
                )
            else:
                # Fallback to in-memory cache
                pass
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    async def _get_redis_connection(self):
        """Get Redis connection from pool"""
        if not self._redis_pool:
            manager = get_connection_pool_manager()
            redis_pool = await manager.get_pool(ConnectionType.REDIS)
            if redis_pool:
                self._redis_pool = await redis_pool.acquire()
        return self._redis_pool
    
    def _serialize_response(self, response: Response) -> str:
        """Serialize response for caching"""
        # Implementation for response serialization
        pass
    
    def _deserialize_response(self, data: str) -> Response:
        """Deserialize response from cache"""
        # Implementation for response deserialization
        pass
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        key_parts = [
            request.method,
            str(request.url),
            request.headers.get("accept-language", ""),
        ]
        return hashlib.md5(":".join(key_parts).encode()).hexdigest()


def add_performance_middleware(app: FastAPI, settings: Settings) -> None:
    """Add performance middleware to FastAPI application"""
    # Add performance monitoring middleware
    app.add_middleware(AsyncPerformanceMiddleware, settings=settings)
    
    # Add caching middleware if enabled
    if settings.cache_enabled:
        app.add_middleware(AsyncCachingMiddleware, settings=settings)
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time", "X-Request-ID", "X-RateLimit-Limit", 
                       "X-RateLimit-Remaining", "X-RateLimit-Reset"]
    )
    
    # Add security middleware in production
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.trusted_hosts
        )


def performance_monitor(func: Callable) -> Callable:
    """Decorator for performance monitoring of specific functions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            processing_time = (time.time() - start_time) * 1000
            
            # Log performance
            logger.debug(
                f"Function {func.__name__} executed in {processing_time:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(
                f"Function {func.__name__} failed after {processing_time:.2f}ms: {e}"
            )
            raise
    
    return wrapper


# Dependency for getting performance stats
async def get_performance_stats(
    middleware: AsyncPerformanceMiddleware = Depends(lambda: None)
) -> Dict[str, Any]:
    """Dependency to get performance statistics"""
    if middleware:
        return middleware.get_performance_stats()
    return {"error": "performance_middleware_not_available"}
