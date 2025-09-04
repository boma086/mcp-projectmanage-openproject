"""
FastMCP Monitoring Package

This package provides unified monitoring capabilities for the FastMCP solution,
including Prometheus metrics collection, structured logging, and health checks.
"""

from .metrics import (
    PrometheusMetrics,
    RequestMetrics,
    RequestCorrelation,
    MonitoringMiddleware,
    get_monitoring,
    monitor_mcp_operation,
    monitor_mcp_protocol_operation,
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
    "monitor_mcp_operation",
    "monitor_mcp_protocol_operation",
    "monitor_openproject_request",
    "logger",
    
    # Health checks
    "HealthStatus",
    "HealthCheckResult",
    "HealthCheckSummary",
    "HealthChecker",
    "get_health_checker",
    "update_health_checker_config"
]
