"""
Monitoring Endpoints for FastMCP Solution

This module provides HTTP endpoints for monitoring the FastMCP solution.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from aiohttp import web
from aiohttp.web import Request, Response

from .metrics import get_monitoring
from .health import get_health_checker, HealthStatus
from ..monitoring import logger


class MonitoringEndpoints:
    """Monitoring endpoints for FastMCP solution"""
    
    def __init__(self):
        self.monitoring = get_monitoring()
        self.health_checker = None
        self.logger = logger.bind(component="monitoring_endpoints")
    
    def set_health_checker(self, health_checker) -> None:
        """Set the health checker instance"""
        self.health_checker = health_checker
    
    async def liveness_check(self, request: Request) -> Response:
        """Liveness check endpoint"""
        try:
            async with self.monitoring.monitor_request("GET", "/health/live", dict(request.headers)):
                health_summary = await self.health_checker.check_liveness()
                
                status_code = 200 if health_summary.overall_status == HealthStatus.HEALTHY else 503
                
                response_data = {
                    "status": health_summary.overall_status.value,
                    "timestamp": health_summary.timestamp,
                    "service": "fastmcp-solution",
                    "checks": [
                        {
                            "name": result.name,
                            "status": result.status.value,
                            "duration_ms": result.duration_ms,
                            "message": result.message
                        }
                        for result in health_summary.results
                    ]
                }
                
                return web.json_response(
                    response_data,
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Liveness check failed", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    async def readiness_check(self, request: Request) -> Response:
        """Readiness check endpoint"""
        try:
            async with self.monitoring.monitor_request("GET", "/health/ready", dict(request.headers)):
                health_summary = await self.health_checker.check_readiness()
                
                status_code = 200 if health_summary.overall_status == HealthStatus.HEALTHY else 503
                
                response_data = {
                    "status": health_summary.overall_status.value,
                    "timestamp": health_summary.timestamp,
                    "service": "fastmcp-solution",
                    "total_checks": health_summary.total_checks,
                    "healthy_checks": health_summary.healthy_checks,
                    "degraded_checks": health_summary.degraded_checks,
                    "unhealthy_checks": health_summary.unhealthy_checks,
                    "checks": [
                        {
                            "name": result.name,
                            "status": result.status.value,
                            "duration_ms": result.duration_ms,
                            "message": result.message,
                            "details": result.details
                        }
                        for result in health_summary.results
                    ]
                }
                
                return web.json_response(
                    response_data,
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Readiness check failed", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    async def deep_health_check(self, request: Request) -> Response:
        """Deep health check endpoint"""
        try:
            async with self.monitoring.monitor_request("GET", "/health/deep", dict(request.headers)):
                health_summary = await self.health_checker.check_deep_health()
                
                status_code = 200 if health_summary.overall_status == HealthStatus.HEALTHY else 503
                
                response_data = {
                    "status": health_summary.overall_status.value,
                    "timestamp": health_summary.timestamp,
                    "service": "fastmcp-solution",
                    "total_checks": health_summary.total_checks,
                    "healthy_checks": health_summary.healthy_checks,
                    "degraded_checks": health_summary.degraded_checks,
                    "unhealthy_checks": health_summary.unhealthy_checks,
                    "checks": [
                        {
                            "name": result.name,
                            "status": result.status.value,
                            "duration_ms": result.duration_ms,
                            "message": result.message,
                            "details": result.details
                        }
                        for result in health_summary.results
                    ]
                }
                
                return web.json_response(
                    response_data,
                    status=status_code,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Deep health check failed", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    async def metrics(self, request: Request) -> Response:
        """Prometheus metrics endpoint"""
        try:
            async with self.monitoring.monitor_request("GET", "/metrics", dict(request.headers)):
                metrics_data = self.monitoring.metrics.get_metrics()
                
                return Response(
                    text=metrics_data,
                    content_type="text/plain; version=0.0.4; charset=utf-8"
                )
                
        except Exception as e:
            self.logger.error("Metrics endpoint failed", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    async def info(self, request: Request) -> Response:
        """Service information endpoint"""
        try:
            async with self.monitoring.monitor_request("GET", "/info", dict(request.headers)):
                response_data = {
                    "service": "OpenProject FastMCP Server",
                    "version": "1.0.0",
                    "architecture": "fastmcp-native",
                    "python_version": "3.11",
                    "fastmcp_version": "2.10.6",
                    "mcp_version": "1.12.1",
                    "endpoints": {
                        "mcp": "/mcp",
                        "health": {
                            "live": "/health/live",
                            "ready": "/health/ready",
                            "deep": "/health/deep"
                        },
                        "metrics": "/metrics",
                        "info": "/info"
                    },
                    "features": {
                        "prometheus_metrics": True,
                        "structured_logging": True,
                        "health_checks": True,
                        "correlation_ids": True,
                        "sse_support": True
                    },
                    "documentation": "https://github.com/modelcontextprotocol/python-sdk",
                    "timestamp": datetime.now().isoformat()
                }
                
                return web.json_response(
                    response_data,
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Info endpoint failed", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )
    
    async def ping(self, request: Request) -> Response:
        """Ping endpoint for basic connectivity test"""
        try:
            async with self.monitoring.monitor_request("GET", "/ping", dict(request.headers)):
                response_data = {
                    "message": "pong",
                    "service": "fastmcp-solution",
                    "timestamp": datetime.now().isoformat()
                }
                
                return web.json_response(
                    response_data,
                    status=200,
                    headers={"Content-Type": "application/json"}
                )
                
        except Exception as e:
            self.logger.error("Ping endpoint failed", error=str(e))
            return web.json_response(
                {"status": "error", "message": str(e)},
                status=500
            )


def create_monitoring_endpoints() -> MonitoringEndpoints:
    """Create monitoring endpoints instance"""
    return MonitoringEndpoints()
