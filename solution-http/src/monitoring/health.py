"""
Health Check Module for HTTP Solution

This module provides comprehensive health checks for the HTTP solution,
including service health, dependency health, and resource utilization.
"""

import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import psutil
import requests

from .metrics import get_monitoring, logger


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    name: str
    status: HealthStatus
    duration_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class HealthCheckSummary:
    """Health check summary data structure"""
    overall_status: HealthStatus
    total_checks: int
    healthy_checks: int
    degraded_checks: int
    unhealthy_checks: int
    results: List[HealthCheckResult]
    timestamp: float = field(default_factory=time.time)


class HealthChecker:
    """Comprehensive health checker for HTTP solution"""
    
    def __init__(self, openproject_url: str, openproject_api_key: str):
        self.openproject_url = openproject_url.rstrip('/')
        self.openproject_api_key = openproject_api_key
        self.logger = logger.bind(component="health_checker")
        self.monitoring = get_monitoring()
        
        # Cache for health check results
        self._cache: Dict[str, Tuple[HealthCheckResult, float]] = {}
        self._cache_ttl = 30  # 30 seconds
        self._lock = threading.Lock()
    
    def check_liveness(self) -> HealthCheckSummary:
        """Basic liveness check - is the service running?"""
        start_time = time.time()
        
        results = []
        
        # Basic service check
        result = HealthCheckResult(
            name="service_liveness",
            status=HealthStatus.HEALTHY,
            duration_ms=(time.time() - start_time) * 1000,
            message="Service is running"
        )
        results.append(result)
        
        return HealthCheckSummary(
            overall_status=HealthStatus.HEALTHY,
            total_checks=1,
            healthy_checks=1,
            degraded_checks=0,
            unhealthy_checks=0,
            results=results
        )
    
    def check_readiness(self) -> HealthCheckSummary:
        """Readiness check - is the service ready to handle traffic?"""
        start_time = time.time()
        
        results = []
        
        # Check if we can process basic requests
        try:
            # This is a basic check - in a real scenario, you might check
            # if internal services are initialized
            result = HealthCheckResult(
                name="service_readiness",
                status=HealthStatus.HEALTHY,
                duration_ms=(time.time() - start_time) * 1000,
                message="Service is ready to handle traffic"
            )
            results.append(result)
        except Exception as e:
            result = HealthCheckResult(
                name="service_readiness",
                status=HealthStatus.UNHEALTHY,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Service not ready: {str(e)}"
            )
            results.append(result)
        
        return self._summarize_results(results)
    
    def check_deep_health(self) -> HealthCheckSummary:
        """Comprehensive health check including all dependencies"""
        start_time = time.time()
        
        results = []
        
        # Service health
        results.append(self._check_service_health())
        
        # OpenProject connection
        results.append(self._check_openproject_connection())
        
        # Resource health
        results.append(self._check_resource_health())
        
        # Database health (if applicable)
        results.append(self._check_database_health())
        
        # Cache health (if applicable)
        results.append(self._check_cache_health())
        
        return self._summarize_results(results)
    
    def _check_service_health(self) -> HealthCheckResult:
        """Check basic service health"""
        start_time = time.time()
        
        try:
            # Check if monitoring is working
            monitoring = get_monitoring()
            if monitoring:
                status = HealthStatus.HEALTHY
                message = "Service monitoring is active"
            else:
                status = HealthStatus.DEGRADED
                message = "Service monitoring not available"
            
            result = HealthCheckResult(
                name="service_health",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                message=message
            )
            
            # Update Prometheus metrics
            monitoring.metrics.update_health_status("service", status == HealthStatus.HEALTHY)
            
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                name="service_health",
                status=HealthStatus.UNHEALTHY,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Service health check failed: {str(e)}"
            )
            
            # Update Prometheus metrics
            try:
                get_monitoring().metrics.update_health_status("service", False)
            except:
                pass
            
            return result
    
    def _check_openproject_connection(self) -> HealthCheckResult:
        """Check OpenProject API connection"""
        start_time = time.time()
        cache_key = "openproject_connection"
        
        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Test API connection
            headers = {
                "Authorization": f"Bearer {self.openproject_api_key}",
                "Content-Type": "application/json"
            }
            
            # Try to get API status or projects
            response = requests.get(
                f"{self.openproject_url}/api/v3/projects",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY
                message = "OpenProject API connection successful"
                details = {
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "status_code": response.status_code,
                    "projects_count": len(response.json().get("_embedded", {}).get("elements", []))
                }
            elif response.status_code == 401:
                status = HealthStatus.UNHEALTHY
                message = "OpenProject API authentication failed"
                details = {
                    "status_code": response.status_code,
                    "error": "Invalid API key"
                }
            else:
                status = HealthStatus.DEGRADED
                message = f"OpenProject API returned status {response.status_code}"
                details = {
                    "status_code": response.status_code,
                    "response_time_ms": (time.time() - start_time) * 1000
                }
            
            result = HealthCheckResult(
                name="openproject_connection",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                message=message,
                details=details
            )
            
            # Update Prometheus metrics
            connected = status == HealthStatus.HEALTHY
            try:
                get_monitoring().metrics.update_openproject_connection_status(connected)
            except:
                pass
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except requests.exceptions.Timeout:
            result = HealthCheckResult(
                name="openproject_connection",
                status=HealthStatus.UNHEALTHY,
                duration_ms=(time.time() - start_time) * 1000,
                message="OpenProject API connection timeout",
                details={"error": "timeout"}
            )
            
            # Update Prometheus metrics
            try:
                get_monitoring().metrics.update_openproject_connection_status(False)
            except:
                pass
            
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                name="openproject_connection",
                status=HealthStatus.UNHEALTHY,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"OpenProject API connection failed: {str(e)}",
                details={"error": str(e)}
            )
            
            # Update Prometheus metrics
            try:
                get_monitoring().metrics.update_openproject_connection_status(False)
            except:
                pass
            
            return result
    
    def _check_resource_health(self) -> HealthCheckResult:
        """Check system resource health"""
        start_time = time.time()
        cache_key = "resource_health"
        
        # Check cache first
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Get system resource usage
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Determine health status based on resource usage
            status = HealthStatus.HEALTHY
            issues = []
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                issues.append(f"Elevated memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 95:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 85:
                if status != HealthStatus.UNHEALTHY:
                    status = HealthStatus.DEGRADED
                issues.append(f"Elevated disk usage: {disk.percent:.1f}%")
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                if status != HealthStatus.UNHEALTHY:
                    status = HealthStatus.DEGRADED
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            message = "Resource usage normal" if not issues else f"Resource issues: {'; '.join(issues)}"
            
            details = {
                "memory_percent": round(memory.percent, 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "disk_percent": round(disk.percent, 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "cpu_percent": round(cpu_percent, 2)
            }
            
            result = HealthCheckResult(
                name="resource_health",
                status=status,
                duration_ms=(time.time() - start_time) * 1000,
                message=message,
                details=details
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                name="resource_health",
                status=HealthStatus.UNKNOWN,
                duration_ms=(time.time() - start_time) * 1000,
                message=f"Resource health check failed: {str(e)}"
            )
            
            return result
    
    def _check_database_health(self) -> HealthCheckResult:
        """Check database health (placeholder for future implementation)"""
        start_time = time.time()
        
        # For now, return healthy status
        # In a real implementation, you would check database connectivity
        result = HealthCheckResult(
            name="database_health",
            status=HealthStatus.HEALTHY,
            duration_ms=(time.time() - start_time) * 1000,
            message="Database health check not implemented",
            details={"note": "Database health monitoring not yet implemented"}
        )
        
        return result
    
    def _check_cache_health(self) -> HealthCheckResult:
        """Check cache health (placeholder for future implementation)"""
        start_time = time.time()
        
        # For now, return healthy status
        # In a real implementation, you would check cache connectivity
        result = HealthCheckResult(
            name="cache_health",
            status=HealthStatus.HEALTHY,
            duration_ms=(time.time() - start_time) * 1000,
            message="Cache health check not implemented",
            details={"note": "Cache health monitoring not yet implemented"}
        )
        
        return result
    
    def _summarize_results(self, results: List[HealthCheckResult]) -> HealthCheckSummary:
        """Summarize health check results"""
        healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        
        # Determine overall status
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return HealthCheckSummary(
            overall_status=overall_status,
            total_checks=len(results),
            healthy_checks=healthy_count,
            degraded_checks=degraded_count,
            unhealthy_checks=unhealthy_count,
            results=results
        )
    
    def _get_cached_result(self, cache_key: str) -> Optional[HealthCheckResult]:
        """Get cached health check result"""
        with self._lock:
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    return result
                else:
                    # Remove expired cache entry
                    del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: HealthCheckResult) -> None:
        """Cache health check result"""
        with self._lock:
            self._cache[cache_key] = (result, time.time())
    
    def clear_cache(self) -> None:
        """Clear health check cache"""
        with self._lock:
            self._cache.clear()


# Global health checker instance
_health_checker_instance = None
_health_checker_lock = threading.Lock()


def get_health_checker(openproject_url: str, openproject_api_key: str) -> HealthChecker:
    """Get global health checker instance"""
    global _health_checker_instance
    
    if _health_checker_instance is None:
        with _health_checker_lock:
            if _health_checker_instance is None:
                _health_checker_instance = HealthChecker(openproject_url, openproject_api_key)
    
    return _health_checker_instance


def update_health_checker_config(openproject_url: str, openproject_api_key: str) -> None:
    """Update health checker configuration"""
    global _health_checker_instance
    
    with _health_checker_lock:
        _health_checker_instance = HealthChecker(openproject_url, openproject_api_key)