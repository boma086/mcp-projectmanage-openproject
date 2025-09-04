"""
Test file for FastMCP monitoring functionality
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
import aiohttp
from prometheus_client import REGISTRY

from src.monitoring.metrics import (
    PrometheusMetrics, 
    RequestMetrics, 
    MonitoringMiddleware,
    get_monitoring
)
from src.monitoring.health import (
    HealthChecker,
    HealthStatus,
    get_health_checker
)


class TestPrometheusMetrics:
    """Test Prometheus metrics collection"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.metrics = PrometheusMetrics("test-solution")
    
    def teardown_method(self):
        """Cleanup after tests"""
        # Clear the registry to avoid conflicts between tests
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            REGISTRY.unregister(collector)
    
    def test_record_request(self):
        """Test recording HTTP request metrics"""
        request_metrics = RequestMetrics(
            request_id="test_req_1",
            method="GET",
            path="/test",
            start_time=time.time(),
            end_time=time.time() + 0.1,
            duration_ms=100.0,
            status_code=200,
            response_size=1024
        )
        
        self.metrics.record_request(request_metrics)
        
        # Verify metrics were recorded
        metrics_output = self.metrics.get_metrics()
        assert "http_requests_total" in metrics_output
        assert "http_request_duration_seconds" in metrics_output
        assert "http_response_size_bytes" in metrics_output
    
    def test_record_mcp_operation(self):
        """Test recording MCP operation metrics"""
        self.metrics.record_mcp_operation("test_operation", "test_tool", "success", 50.0)
        
        metrics_output = self.metrics.get_metrics()
        assert "mcp_operations_total" in metrics_output
        assert "mcp_operation_duration_seconds" in metrics_output
    
    def test_record_mcp_protocol_operation(self):
        """Test recording MCP protocol operation metrics"""
        self.metrics.record_mcp_protocol_operation("initialize", "2024-11-05", "success", 25.0)
        
        metrics_output = self.metrics.get_metrics()
        assert "mcp_protocol_operations_total" in metrics_output
    
    def test_record_mcp_error(self):
        """Test recording MCP error metrics"""
        self.metrics.record_mcp_error("ValidationError", "test_operation")
        
        metrics_output = self.metrics.get_metrics()
        assert "mcp_errors_total" in metrics_output
    
    def test_update_health_status(self):
        """Test updating health status"""
        self.metrics.update_health_status("service", True)
        
        metrics_output = self.metrics.get_metrics()
        assert "health_check_status" in metrics_output
    
    def test_update_openproject_connection_status(self):
        """Test updating OpenProject connection status"""
        self.metrics.update_openproject_connection_status(True)
        
        metrics_output = self.metrics.get_metrics()
        assert "openproject_connection_status" in metrics_output
    
    def test_active_requests_counter(self):
        """Test active requests counter"""
        initial_count = self.metrics._active_requests_count
        
        self.metrics.increment_active_requests()
        assert self.metrics._active_requests_count == initial_count + 1
        
        self.metrics.decrement_active_requests()
        assert self.metrics._active_requests_count == initial_count


class TestMonitoringMiddleware:
    """Test monitoring middleware"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.middleware = MonitoringMiddleware("test-solution")
    
    def test_generate_request_id(self):
        """Test request ID generation"""
        request_id = self.middleware.generate_request_id()
        assert request_id.startswith("req_")
        assert len(request_id) > 10
    
    def test_correlation_id_management(self):
        """Test correlation ID management"""
        request_id = "test_req_1"
        correlation_id = self.middleware.correlation.generate_correlation_id(request_id)
        
        assert correlation_id.startswith("corr_")
        assert len(correlation_id) == 18  # corr_ + 12 hex characters
        
        # Test retrieval
        retrieved_id = self.middleware.correlation.get_correlation_id(request_id)
        assert retrieved_id == correlation_id
        
        # Test cleanup
        self.middleware.correlation.cleanup_correlation_id(request_id)
        retrieved_id = self.middleware.correlation.get_correlation_id(request_id)
        assert retrieved_id is None


class TestHealthChecker:
    """Test health checker functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.health_checker = HealthChecker(
            "https://test.openproject.com",
            "test_api_key"
        )
    
    @pytest.mark.asyncio
    async def test_check_liveness(self):
        """Test liveness check"""
        health_summary = await self.health_checker.check_liveness()
        
        assert health_summary.overall_status == HealthStatus.HEALTHY
        assert health_summary.total_checks == 1
        assert health_summary.healthy_checks == 1
        assert len(health_summary.results) == 1
    
    @pytest.mark.asyncio
    async def test_check_readiness(self):
        """Test readiness check"""
        health_summary = await self.health_checker.check_readiness()
        
        assert health_summary.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        assert len(health_summary.results) >= 1
    
    @pytest.mark.asyncio
    async def test_check_deep_health(self):
        """Test deep health check"""
        health_summary = await self.health_checker.check_deep_health()
        
        assert health_summary.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
        assert len(health_summary.results) >= 3  # service, OpenProject, resource
    
    def test_session_management(self):
        """Test session management"""
        session_id = "test_session_1"
        
        # Register session
        self.health_checker.register_session(session_id)
        assert self.health_checker.get_active_sessions_count() == 1
        
        # Unregister session
        self.health_checker.unregister_session(session_id)
        assert self.health_checker.get_active_sessions_count() == 0
    
    def test_cache_management(self):
        """Test cache management"""
        # Add item to cache
        test_result = MagicMock()
        test_result.name = "test_check"
        test_result.status = HealthStatus.HEALTHY
        test_result.duration_ms = 10.0
        test_result.message = "Test message"
        
        self.health_checker._cache_result("test_key", test_result)
        
        # Retrieve from cache
        cached_result = self.health_checker._get_cached_result("test_key")
        assert cached_result == test_result
        
        # Clear cache
        self.health_checker.clear_cache()
        cached_result = self.health_checker._get_cached_result("test_key")
        assert cached_result is None


class TestMonitoringIntegration:
    """Test monitoring integration"""
    
    @pytest.mark.asyncio
    async def test_monitor_request_context_manager(self):
        """Test request monitoring context manager"""
        middleware = MonitoringMiddleware("test-solution")
        
        async with middleware.monitor_request("GET", "/test", {"user-agent": "test-agent"}) as metrics:
            assert metrics.request_id is not None
            assert metrics.method == "GET"
            assert metrics.path == "/test"
            assert metrics.user_agent == "test-agent"
            assert metrics.correlation_id is not None
        
        # Verify metrics were recorded
        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_monitor_mcp_operation_context_manager(self):
        """Test MCP operation monitoring context manager"""
        middleware = MonitoringMiddleware("test-solution")
        
        async with middleware.monitor_mcp_operation("test_operation", "test_tool"):
            pass  # Successful operation
        
        # Verify error handling
        with pytest.raises(Exception):
            async with middleware.monitor_mcp_operation("test_operation", "test_tool"):
                raise Exception("Test error")
    
    @pytest.mark.asyncio
    async def test_monitor_openproject_request_context_manager(self):
        """Test OpenProject request monitoring context manager"""
        middleware = MonitoringMiddleware("test-solution")
        
        async with middleware.monitor_openproject_request("GET", "/api/v3/projects"):
            pass  # Successful request
        
        # Verify error handling
        with pytest.raises(Exception):
            async with middleware.monitor_openproject_request("GET", "/api/v3/projects"):
                raise Exception("Test error")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
