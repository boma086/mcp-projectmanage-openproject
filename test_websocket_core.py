#!/usr/bin/env python3
"""
Core WebSocket Component Tests

Test WebSocket manager and notification components without external dependencies.
"""
import asyncio
import sys
import os

# Add solution-fastapi to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'solution-fastapi'))

async def test_websocket_manager():
    """Test WebSocket connection manager functionality"""
    print("Testing WebSocket manager...")
    
    try:
        from app.websockets.manager import ConnectionManager
        
        # Test connection manager initialization
        manager = ConnectionManager()
        
        # Test connection stats
        stats = manager.get_connection_stats()
        assert "total_connections" in stats
        assert stats["max_connections"] == 100  # Default from config
        assert stats["subscription_counts"]["mcp_operations"] == 0
        print("✓ Connection manager stats working correctly")
        
        # Test mock connection lifecycle
        class MockWebSocket:
            async def accept(self):
                pass
            async def send_text(self, text):
                pass
        
        websocket = MockWebSocket()
        client_id = await manager.connect(websocket)
        
        # Verify connection tracking
        assert client_id in manager.active_connections
        assert client_id in manager.connection_metrics
        print("✓ Connection lifecycle working correctly")
        
        # Test subscription management
        await manager.subscribe(client_id, "mcp_operations")
        assert client_id in manager.subscriptions["mcp_operations"]
        print("✓ Subscription management working correctly")
        
        # Test broadcast functionality
        test_message = {"type": "test", "message": "test broadcast"}
        await manager.broadcast(test_message, "mcp_operations")
        print("✓ Broadcast functionality working correctly")
        
        # Test metrics collection
        metrics = manager.get_connection_metrics(client_id)
        assert metrics["client_id"] == client_id
        assert metrics["subscription_count"] == 1
        print("✓ Metrics collection working correctly")
        
        # Test disconnection
        manager.disconnect(client_id)
        assert client_id not in manager.active_connections
        print("✓ Disconnection working correctly")
        
        print("✓ WebSocket manager working correctly")
        return True
        
    except Exception as e:
        print(f"✗ WebSocket manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_notification_service():
    """Test notification service functionality"""
    print("Testing notification service...")
    
    try:
        from app.websockets.notifications import MCPOperationNotification, NotificationService
        
        # Test MCP operation notification
        notification = MCPOperationNotification(
            operation_type="tools/call",
            operation_id="test-123",
            method="get_project_report",
            params={"project_id": 123, "api_key": "secret-123"},
            result={"content": "test content" * 100},  # Large content
            duration_ms=150.5
        )
        
        notification_dict = notification.to_dict()
        
        # Verify basic structure
        assert notification_dict["type"] == "mcp_operation"
        assert notification_dict["operation"] == "tools/call"
        assert notification_dict["duration_ms"] == 150.5
        print("✓ MCP operation notification working correctly")
        
        # Verify parameter sanitization
        params = notification_dict["params"]
        assert params["api_key"] == "[REDACTED]"
        print("✓ Parameter sanitization working correctly")
        
        # Verify result sanitization for large content
        result = notification_dict["result"]
        assert "content_truncated" in result
        assert result["content_truncated"] == True
        print("✓ Result sanitization working correctly")
        
        print("✓ Notification service working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Notification service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all WebSocket core tests"""
    print("=" * 60)
    print("WEBSOCKET CORE COMPONENT TESTS")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(await test_websocket_manager())
    results.append(await test_notification_service())
    
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
        print("\n🎉 ALL WEBSOCKET CORE COMPONENTS WORKING CORRECTLY!")
        print("WebSocket implementation is ready for integration!")
        return True
    else:
        print(f"\n❌ {failed_tests} test(s) failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)