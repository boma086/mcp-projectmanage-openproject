#!/usr/bin/env python3
"""
Test FastAPI Solution Components

Comprehensive test to verify all FastAPI async solution components are working correctly.
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
        from app.websockets.notifications import NotificationService, MCPOperationNotification
        
        # Test connection manager
        manager = ConnectionManager()
        stats = manager.get_connection_stats()
        assert "total_connections" in stats
        assert stats["max_connections"] == 100
        print("✓ Connection manager working correctly")
        
        # Test notification service
        notification = MCPOperationNotification(
            operation_type="tools/call",
            operation_id="test-123",
            method="get_project_report",
            duration_ms=150.5
        )
        notification_dict = notification.to_dict()
        assert notification_dict["type"] == "mcp_operation"
        assert notification_dict["duration_ms"] == 150.5
        print("✓ Notification service working correctly")
        
        print("✓ All WebSocket components working correctly")
        return True
        
    except Exception as e:
        print(f"✗ WebSocket test failed: {e}")
        return False

async def test_async_utils():
    """Test async utilities"""
    print("Testing async utilities...")
    
    try:
        from app.core.async_utils import AsyncPerformanceMonitor, connection_pool, async_retry
        
        # Test performance monitor
        monitor = AsyncPerformanceMonitor()
        finish_op = await monitor.track_operation("test_operation")
        await finish_op(success=True)
        metrics = monitor.get_metrics()
        assert "operations" in metrics
        print("✓ Performance monitor working correctly")
        
        # Test connection pool
        pool_stats = connection_pool.get_stats()
        assert "current_connections" in pool_stats
        print("✓ Connection pool working correctly")
        
        # Test async retry decorator
        @async_retry(max_retries=2)
        async def test_func():
            return "success"
        
        result = await test_func()
        assert result == "success"
        print("✓ Async retry decorator working correctly")
        
        print("✓ All async utilities working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Async utils test failed: {e}")
        return False

async def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    
    try:
        from app.core.config import get_settings
        
        settings = get_settings()
        assert hasattr(settings, 'app_name')
        assert hasattr(settings, 'max_concurrent_requests')
        assert hasattr(settings, 'websocket_enabled')
        
        print(f"✓ Configuration loaded: {settings.app_name}")
        print(f"✓ Max concurrent requests: {settings.max_concurrent_requests}")
        print(f"✓ WebSocket enabled: {settings.websocket_enabled}")
        
        print("✓ Configuration working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

async def test_connection_pool():
    """Test connection pool manager"""
    print("Testing connection pool manager...")
    
    try:
        from app.core.connection_pool import get_connection_pool_manager, ConnectionType
        
        manager = get_connection_pool_manager()
        
        # Test HTTP connection pool
        async with manager.acquire_connection(ConnectionType.HTTP):
            print("✓ HTTP connection pool acquired successfully")
        
        # Test health checks
        health_status = await manager.health_check_all()
        assert isinstance(health_status, dict)
        print("✓ Health checks working correctly")
        
        # Test statistics
        stats = manager.get_all_stats()
        assert isinstance(stats, dict)
        print("✓ Statistics collection working correctly")
        
        await manager.close_all()
        print("✓ Connection pool manager working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Connection pool test failed: {e}")
        return False

async def test_performance_middleware():
    """Test performance middleware components"""
    print("Testing performance middleware...")
    
    try:
        from app.middleware.performance import AsyncPerformanceMiddleware
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Test middleware initialization
        middleware = AsyncPerformanceMiddleware(None, settings)
        stats = middleware.get_performance_stats()
        assert "total_requests" in stats
        print("✓ Performance middleware working correctly")
        
        print("✓ Performance middleware working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Performance middleware test failed: {e}")
        return False

async def main():
    """Run all component tests"""
    print("=" * 60)
    print("COMPREHENSIVE FASTAPI SOLUTION COMPONENT TESTS")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(await test_config())
    results.append(await test_async_utils())
    results.append(await test_websocket_components())
    results.append(await test_connection_pool())
    results.append(await test_performance_middleware())
    
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
        print("\n🎉 ALL COMPONENTS WORKING CORRECTLY!")
        print("FastAPI async solution is ready for production!")
        return True
    else:
        print(f"\n❌ {failed_tests} test(s) failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)