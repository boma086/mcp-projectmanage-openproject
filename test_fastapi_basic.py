#!/usr/bin/env python3
"""
Basic FastAPI Solution Component Tests

Test core components without external dependencies.
"""
import asyncio
import sys
import os

# Add solution-fastapi to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'solution-fastapi'))

async def test_websocket_components():
    """Test WebSocket manager and notification components"""
    print("Testing WebSocket components...")
    
    try:
        from app.websockets.manager import ConnectionManager
        from app.websockets.notifications import MCPOperationNotification
        
        # Test connection manager
        manager = ConnectionManager()
        stats = manager.get_connection_stats()
        assert "total_connections" in stats
        assert stats["max_connections"] == 100
        print("✓ Connection manager working correctly")
        
        # Test notification data class
        notification = MCPOperationNotification(
            operation_type="tools/call",
            operation_id="test-123",
            method="get_project_report",
            duration_ms=150.5
        )
        notification_dict = notification.to_dict()
        assert notification_dict["type"] == "mcp_operation"
        assert notification_dict["duration_ms"] == 150.5
        print("✓ Notification data class working correctly")
        
        print("✓ WebSocket components working correctly")
        return True
        
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

async def test_async_utils():
    """Test async utilities"""
    print("Testing async utilities...")
    
    try:
        from app.core.async_utils import AsyncPerformanceMonitor, async_retry
        
        # Test performance monitor
        monitor = AsyncPerformanceMonitor()
        finish_op = await monitor.track_operation("test_operation")
        await finish_op(success=True)
        metrics = monitor.get_metrics()
        assert "operations" in metrics
        print("✓ Performance monitor working correctly")
        
        # Test async retry decorator
        @async_retry(max_retries=2)
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
        print("✓ Async retry decorator working correctly")
        
        print("✓ Async utilities working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Async utils test failed: {e}")
        return False

async def test_middleware_components():
    """Test middleware components"""
    print("Testing middleware components...")
    
    try:
        from app.middleware.performance import AsyncPerformanceMiddleware
        
        # Create mock settings
        class MockSettings:
            rate_limit_enabled = False
            cache_enabled = False
            slow_request_threshold = 5.0
            debug = False
        
        # Test middleware initialization
        middleware = AsyncPerformanceMiddleware(None, MockSettings())
        stats = middleware.get_performance_stats()
        assert "total_requests" in stats
        print("✓ Performance middleware working correctly")
        
        print("✓ Middleware components working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Middleware test failed: {e}")
        return False

async def test_config_structure():
    """Test configuration structure"""
    print("Testing configuration structure...")
    
    try:
        # Test that config module can be imported
        import app.core.config
        
        # Check that settings class exists
        assert hasattr(app.core.config, 'Settings')
        print("✓ Configuration module structure correct")
        
        # Check expected settings attributes
        settings_class = app.core.config.Settings
        expected_attrs = ['app_name', 'max_concurrent_requests', 'websocket_enabled', 
                         'request_timeout', 'debug']
        
        for attr in expected_attrs:
            assert hasattr(settings_class, attr), f"Missing attribute: {attr}"
        
        print("✓ Configuration class structure correct")
        print("✓ Configuration structure working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Config structure test failed: {e}")
        return False

async def main():
    """Run all basic component tests"""
    print("=" * 60)
    print("BASIC FASTAPI SOLUTION COMPONENT TESTS")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(await test_config_structure())
    results.append(await test_async_utils())
    results.append(await test_websocket_components())
    results.append(await test_middleware_components())
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ALL CORE COMPONENTS WORKING CORRECTLY!")
        print("FastAPI async solution core components are functional!")
        return True
    else:
        print(f"\n❌ {failed_tests} test(s) failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)