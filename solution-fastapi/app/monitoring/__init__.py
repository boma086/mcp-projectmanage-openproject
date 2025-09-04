"""
Monitoring Package for FastAPI Solution

This package provides unified monitoring capabilities including:
- Prometheus metrics collection
- Structured logging with correlation IDs
- Health checks and readiness probes
- Performance monitoring
"""

from .metrics import (
    PrometheusMetrics,
    RequestMetrics,
    RequestCorrelation,
    MonitoringMiddleware,
    get_monitoring,
    monitor_http_request,
    monitor_mcp_operation,
    monitor_openproject_request,
    logger
)

from .health import (
    HealthStatus,
    HealthCheckResult,
    HealthCheckSummary,
    HealthChecker,
    get_health_checker,
    update_health_checker_config
)

__all__ = [
    # Metrics
    "PrometheusMetrics",
    "RequestMetrics", 
    "RequestCorrelation",
    "MonitoringMiddleware",
    "get_monitoring",
    "monitor_http_request",
    "monitor_mcp_operation",
    "monitor_openproject_request",
    "logger",
    
    # Health
    "HealthStatus",
    "HealthCheckResult",
    "HealthCheckSummary", 
    "HealthChecker",
    "get_health_checker",
    "update_health_checker_config"
]