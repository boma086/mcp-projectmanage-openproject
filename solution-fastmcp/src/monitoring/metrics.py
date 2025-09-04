"""
Monitoring Module for FastMCP Solution

This module provides unified monitoring capabilities for the FastMCP solution,
including Prometheus metrics collection, structured logging, and health checks.
"""

import time
import json
import uuid
import asyncio
import threading
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps
import logging

from prometheus_client import Counter, Histogram, Gauge, Summary, Info, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("mcp.fastmcp.monitoring")


@dataclass
class RequestMetrics:
    """Request metrics data structure"""
    request_id: str
    method: str
    path: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    response_size: Optional[int] = None
    error: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None


class PrometheusMetrics:
    """Prometheus metrics collection for FastMCP solution"""
    
    def __init__(self, app_name: str = "fastmcp-solution"):
        self.app_name = app_name
        self.registry = CollectorRegistry()
        
        # HTTP Request Metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code', 'service'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'service'],
            registry=self.registry
        )
        
        self.http_response_size_bytes = Histogram(
            'http_response_size_bytes',
            'HTTP response size in bytes',
            ['method', 'endpoint', 'service'],
            registry=self.registry
        )
        
        # Error Metrics
        self.http_errors_total = Counter(
            'http_errors_total',
            'Total HTTP errors',
            ['method', 'endpoint', 'status_code', 'error_type', 'service'],
            registry=self.registry
        )
        
        self.mcp_errors_total = Counter(
            'mcp_errors_total',
            'Total MCP processing errors',
            ['error_type', 'operation', 'service'],
            registry=self.registry
        )
        
        # Business Logic Metrics
        self.mcp_operations_total = Counter(
            'mcp_operations_total',
            'Total MCP operations',
            ['operation', 'tool', 'status', 'service'],
            registry=self.registry
        )
        
        self.mcp_operation_duration_seconds = Histogram(
            'mcp_operation_duration_seconds',
            'MCP operation duration in seconds',
            ['operation', 'tool', 'service'],
            registry=self.registry
        )
        
        # FastMCP Specific Metrics
        self.mcp_protocol_operations_total = Counter(
            'mcp_protocol_operations_total',
            'Total MCP protocol operations',
            ['operation', 'protocol_version', 'service'],
            registry=self.registry
        )
        
        self.mcp_sessions_total = Gauge(
            'mcp_sessions_total',
            'Total active MCP sessions',
            ['service'],
            registry=self.registry
        )
        
        self.mcp_session_duration_seconds = Histogram(
            'mcp_session_duration_seconds',
            'MCP session duration in seconds',
            ['service'],
            registry=self.registry
        )
        
        # External Service Metrics
        self.openproject_requests_total = Counter(
            'openproject_requests_total',
            'Total OpenProject API requests',
            ['method', 'endpoint', 'status_code', 'service'],
            registry=self.registry
        )
        
        self.openproject_request_duration_seconds = Histogram(
            'openproject_request_duration_seconds',
            'OpenProject API request duration in seconds',
            ['method', 'endpoint', 'service'],
            registry=self.registry
        )
        
        # SSE Metrics
        self.sse_connections_total = Gauge(
            'sse_connections_total',
            'Total SSE connections',
            ['service'],
            registry=self.registry
        )
        
        self.sse_messages_total = Counter(
            'sse_messages_total',
            'Total SSE messages',
            ['message_type', 'service'],
            registry=self.registry
        )
        
        # Health Metrics
        self.health_check_status = Gauge(
            'health_check_status',
            'Health check status (1=healthy, 0=unhealthy)',
            ['check_type', 'service'],
            registry=self.registry
        )
        
        self.openproject_connection_status = Gauge(
            'openproject_connection_status',
            'OpenProject connection status (1=connected, 0=disconnected)',
            ['service'],
            registry=self.registry
        )
        
        # Performance Metrics
        self.active_requests = Gauge(
            'active_requests',
            'Number of active requests',
            ['service'],
            registry=self.registry
        )
        
        # Application Info
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'app_name': app_name,
            'version': '1.0.0',
            'architecture': 'fastmcp-native'
        })
        
        # Thread-safe metrics storage
        self._active_requests_count = 0
        self._lock = threading.Lock()
    
    def record_request(self, metrics: RequestMetrics) -> None:
        """Record HTTP request metrics"""
        endpoint = metrics.path or 'unknown'
        
        # Record request count
        self.http_requests_total.labels(
            method=metrics.method,
            endpoint=endpoint,
            status_code=metrics.status_code or 500,
            service=self.app_name
        ).inc()
        
        # Record request duration
        if metrics.duration_ms is not None:
            duration_seconds = metrics.duration_ms / 1000.0
            self.http_request_duration_seconds.labels(
                method=metrics.method,
                endpoint=endpoint,
                service=self.app_name
            ).observe(duration_seconds)
        
        # Record response size
        if metrics.response_size is not None:
            self.http_response_size_bytes.labels(
                method=metrics.method,
                endpoint=endpoint,
                service=self.app_name
            ).observe(metrics.response_size)
        
        # Record errors
        if metrics.status_code and metrics.status_code >= 400:
            error_type = 'client_error' if metrics.status_code < 500 else 'server_error'
            self.http_errors_total.labels(
                method=metrics.method,
                endpoint=endpoint,
                status_code=metrics.status_code,
                error_type=error_type,
                service=self.app_name
            ).inc()
    
    def record_mcp_operation(self, operation: str, tool: str, status: str, duration_ms: float) -> None:
        """Record MCP operation metrics"""
        duration_seconds = duration_ms / 1000.0
        
        self.mcp_operations_total.labels(
            operation=operation,
            tool=tool,
            status=status,
            service=self.app_name
        ).inc()
        
        self.mcp_operation_duration_seconds.labels(
            operation=operation,
            tool=tool,
            service=self.app_name
        ).observe(duration_seconds)
    
    def record_mcp_protocol_operation(self, operation: str, protocol_version: str, status: str, duration_ms: float) -> None:
        """Record MCP protocol operation metrics"""
        duration_seconds = duration_ms / 1000.0
        
        self.mcp_protocol_operations_total.labels(
            operation=operation,
            protocol_version=protocol_version,
            service=self.app_name
        ).inc()
    
    def record_mcp_error(self, error_type: str, operation: str) -> None:
        """Record MCP error metrics"""
        self.mcp_errors_total.labels(
            error_type=error_type,
            operation=operation,
            service=self.app_name
        ).inc()
    
    def record_mcp_session(self, session_id: str, duration_ms: float) -> None:
        """Record MCP session metrics"""
        duration_seconds = duration_ms / 1000.0
        self.mcp_session_duration_seconds.labels(service=self.app_name).observe(duration_seconds)
    
    def update_mcp_sessions_count(self, count: int) -> None:
        """Update MCP sessions count"""
        self.mcp_sessions_total.labels(service=self.app_name).set(count)
    
    def record_openproject_request(self, method: str, endpoint: str, status_code: int, duration_ms: float) -> None:
        """Record OpenProject API request metrics"""
        duration_seconds = duration_ms / 1000.0
        
        self.openproject_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            service=self.app_name
        ).inc()
        
        self.openproject_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            service=self.app_name
        ).observe(duration_seconds)
    
    def record_sse_connection(self, client_id: str) -> None:
        """Record SSE connection metrics"""
        self.sse_connections_total.labels(service=self.app_name).inc()
    
    def record_sse_message(self, message_type: str) -> None:
        """Record SSE message metrics"""
        self.sse_messages_total.labels(
            message_type=message_type,
            service=self.app_name
        ).inc()
    
    def update_health_status(self, check_type: str, status: bool) -> None:
        """Update health check status"""
        self.health_check_status.labels(
            check_type=check_type,
            service=self.app_name
        ).set(1 if status else 0)
    
    def update_openproject_connection_status(self, connected: bool) -> None:
        """Update OpenProject connection status"""
        self.openproject_connection_status.labels(
            service=self.app_name
        ).set(1 if connected else 0)
    
    def increment_active_requests(self) -> None:
        """Increment active requests counter"""
        with self._lock:
            self._active_requests_count += 1
            self.active_requests.labels(service=self.app_name).set(self._active_requests_count)
    
    def decrement_active_requests(self) -> None:
        """Decrement active requests counter"""
        with self._lock:
            self._active_requests_count = max(0, self._active_requests_count - 1)
            self.active_requests.labels(service=self.app_name).set(self._active_requests_count)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry).decode('utf-8')


class RequestCorrelation:
    """Request correlation ID management"""
    
    def __init__(self):
        self._correlation_map: Dict[str, str] = {}
        self._lock = threading.Lock()
    
    def generate_correlation_id(self, request_id: str) -> str:
        """Generate correlation ID for request"""
        correlation_id = f"corr_{uuid.uuid4().hex[:12]}"
        
        with self._lock:
            self._correlation_map[request_id] = correlation_id
        
        return correlation_id
    
    def get_correlation_id(self, request_id: str) -> Optional[str]:
        """Get correlation ID for request"""
        with self._lock:
            return self._correlation_map.get(request_id)
    
    def cleanup_correlation_id(self, request_id: str) -> None:
        """Clean up correlation ID"""
        with self._lock:
            self._correlation_map.pop(request_id, None)


class MonitoringMiddleware:
    """Monitoring middleware for FastMCP solution"""
    
    def __init__(self, app_name: str = "fastmcp-solution"):
        self.metrics = PrometheusMetrics(app_name)
        self.correlation = RequestCorrelation()
        self.logger = logger.bind(service=app_name)
    
    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        return f"req_{int(time.time() * 1000000)}_{uuid.uuid4().hex[:8]}"
    
    def log_request(self, metrics: RequestMetrics) -> None:
        """Log request with structured logging"""
        log_data = {
            "request_id": metrics.request_id,
            "method": metrics.method,
            "path": metrics.path,
            "duration_ms": metrics.duration_ms,
            "status_code": metrics.status_code,
            "user_agent": metrics.user_agent,
            "correlation_id": metrics.correlation_id
        }
        
        if metrics.error:
            log_data["error"] = metrics.error
            self.logger.error("Request failed", **log_data)
        else:
            self.logger.info("Request completed", **log_data)
    
    @asynccontextmanager
    async def monitor_request(self, method: str, path: str, headers: Dict[str, str] = None):
        """Context manager for monitoring HTTP requests"""
        request_id = self.generate_request_id()
        correlation_id = self.correlation.generate_correlation_id(request_id)
        
        metrics = RequestMetrics(
            request_id=request_id,
            method=method,
            path=path,
            start_time=time.time(),
            user_agent=headers.get("user-agent") if headers else None,
            correlation_id=correlation_id
        )
        
        # Increment active requests
        self.metrics.increment_active_requests()
        
        try:
            yield metrics
            
            # Record successful request
            if metrics.end_time is None:
                metrics.end_time = time.time()
                metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
            
            self.metrics.record_request(metrics)
            self.log_request(metrics)
            
        except Exception as e:
            # Record failed request
            metrics.end_time = time.time()
            metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
            metrics.error = str(e)
            metrics.status_code = 500
            
            self.metrics.record_request(metrics)
            self.log_request(metrics)
            
            raise
        finally:
            # Decrement active requests and clean up
            self.metrics.decrement_active_requests()
            self.correlation.cleanup_correlation_id(request_id)
    
    @asynccontextmanager
    async def monitor_mcp_operation(self, operation: str, tool: str = "unknown"):
        """Context manager for monitoring MCP operations"""
        start_time = time.time()
        status = "success"
        error = None
        
        try:
            yield
        except Exception as e:
            status = "error"
            error = str(e)
            self.metrics.record_mcp_error(type(e).__name__, operation)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_mcp_operation(operation, tool, status, duration_ms)
    
    @asynccontextmanager
    async def monitor_mcp_protocol_operation(self, operation: str, protocol_version: str = "2024-11-05"):
        """Context manager for monitoring MCP protocol operations"""
        start_time = time.time()
        status = "success"
        error = None
        
        try:
            yield
        except Exception as e:
            status = "error"
            error = str(e)
            self.metrics.record_mcp_error(type(e).__name__, operation)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_mcp_protocol_operation(operation, protocol_version, status, duration_ms)
    
    @asynccontextmanager
    async def monitor_openproject_request(self, method: str, endpoint: str):
        """Context manager for monitoring OpenProject API requests"""
        start_time = time.time()
        status_code = 200
        
        try:
            yield
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.metrics.record_openproject_request(method, endpoint, status_code, duration_ms)


# Global monitoring instance
_monitoring_instance = None
_monitoring_lock = threading.Lock()


def get_monitoring() -> MonitoringMiddleware:
    """Get global monitoring instance"""
    global _monitoring_instance
    
    if _monitoring_instance is None:
        with _monitoring_lock:
            if _monitoring_instance is None:
                _monitoring_instance = MonitoringMiddleware()
    
    return _monitoring_instance


def monitor_mcp_operation(operation: str, tool: str = "unknown"):
    """Decorator for monitoring MCP operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with get_monitoring().monitor_mcp_operation(operation, tool):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_mcp_protocol_operation(operation: str, protocol_version: str = "2024-11-05"):
    """Decorator for monitoring MCP protocol operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with get_monitoring().monitor_mcp_protocol_operation(operation, protocol_version):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


def monitor_openproject_request(method: str, endpoint: str):
    """Decorator for monitoring OpenProject API requests"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with get_monitoring().monitor_openproject_request(method, endpoint):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
