"""
WebSocket Tests for FastAPI Solution

Comprehensive test suite for WebSocket functionality including:
- Connection management and lifecycle
- Real-time notifications for MCP operations
- Subscription-based messaging
- Error handling and graceful degradation
- Performance metrics and monitoring
"""
import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from websockets import connect
import websockets
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'solution-fastapi'))

from app.main import app
from app.websockets.manager import ConnectionManager
from app.websockets.notifications import NotificationService, MCPOperationNotification


class TestWebSocketConnectionManager:
    """Test WebSocket connection manager functionality"""
    
    def setup_method(self):
        """Set up a fresh connection manager for each test"""
        self.manager = ConnectionManager()
    
    async def test_connection_lifecycle(self):
        """Test connection acceptance, tracking, and cleanup"""
        # Mock WebSocket connection
        class MockWebSocket:
            async def accept(self):
                pass
            async def send_text(self, text):
                pass
        
        websocket = MockWebSocket()
        
        # Test connection acceptance
        client_id = await self.manager.connect(websocket)
        assert client_id in self.manager.active_connections
        assert client_id in self.manager.connection_metrics
        
        # Test metrics tracking
        metrics = self.manager.connection_metrics[client_id]
        assert metrics.client_id == client_id
        assert metrics.message_count == 1  # Welcome message
        
        # Test disconnection
        self.manager.disconnect(client_id)
        assert client_id not in self.manager.active_connections
        assert client_id not in self.manager.connection_metrics
    
    async def test_subscription_management(self):
        """Test subscription and unsubscription functionality"""
        class MockWebSocket:
            async def accept(self):
                pass
            async def send_text(self, text):
                pass
        
        websocket = MockWebSocket()
        client_id = await self.manager.connect(websocket)
        
        # Test subscription
        await self.manager.subscribe(client_id, "mcp_operations")
        assert client_id in self.manager.subscriptions["mcp_operations"]
        assert "mcp_operations" in self.manager.connection_metrics[client_id].subscriptions
        
        # Test unsubscription
        await self.manager.unsubscribe(client_id, "mcp_operations")
        assert client_id not in self.manager.subscriptions["mcp_operations"]
        assert "mcp_operations" not in self.manager.connection_metrics[client_id].subscriptions
    
    async def test_broadcast_functionality(self):
        """Test broadcast messaging to all or specific subscribers"""
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            async def accept(self):
                pass
            async def send_text(self, text):
                self.messages.append(text)
        
        # Create multiple mock connections
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        client_id1 = await self.manager.connect(websocket1)
        client_id2 = await self.manager.connect(websocket2)
        
        # Subscribe one client to specific events
        await self.manager.subscribe(client_id1, "mcp_operations")
        
        # Test broadcast to all
        message = {"type": "test", "message": "broadcast to all"}
        await self.manager.broadcast(message)
        
        # Both clients should receive the message
        assert len(websocket1.messages) == 2  # Welcome + broadcast
        assert len(websocket2.messages) == 2  # Welcome + broadcast
        
        # Test broadcast to specific subscription
        message2 = {"type": "mcp_operation", "message": "subscription only"}
        await self.manager.broadcast(message2, "mcp_operations")
        
        # Only subscribed client should receive
        assert len(websocket1.messages) == 3  # Welcome + broadcast + subscription
        assert len(websocket2.messages) == 2  # Only welcome + broadcast (no subscription)
    
    def test_connection_stats(self):
        """Test connection statistics generation"""
        stats = self.manager.get_connection_stats()
        assert "total_connections" in stats
        assert "subscription_counts" in stats
        assert "total_messages_sent" in stats
        assert stats["total_connections"] == 0


class TestNotificationService:
    """Test WebSocket notification service functionality"""
    
    async def test_mcp_operation_notification(self):
        """Test MCP operation notification creation and sanitization"""
        notification = MCPOperationNotification(
            operation_type="tools/call",
            operation_id="test-op-123",
            method="get_project_report",
            params={
                "project_id": 123,
                "api_key": "secret-key-123",  # Should be redacted
                "large_data": "x" * 2000  # Should be truncated
            },
            result={
                "content": "x" * 6000,  # Should be truncated
                "metadata": {"size": 6000}
            },
            duration_ms=150.5
        )
        
        notification_dict = notification.to_dict()
        
        # Verify basic structure
        assert notification_dict["type"] == "mcp_operation"
        assert notification_dict["operation"] == "tools/call"
        assert notification_dict["duration_ms"] == 150.5
        
        # Verify parameter sanitization
        params = notification_dict["params"]
        assert params["api_key"] == "[REDACTED]"
        assert "..." in params["large_data"]  # Truncated
        
        # Verify result sanitization
        result = notification_dict["result"]
        assert "..." in result["content"]  # Truncated
        assert result["content_truncated"] == True
        assert result["original_length"] == 6000
    
    async def test_performance_notification(self):
        """Test performance metric notification with thresholds"""
        from app.websockets.notifications import PerformanceNotification
        
        notification = PerformanceNotification(
            metric_type="request",
            metric_name="response_time",
            value=350.75,
            unit="ms",
            thresholds={"warning": 200, "error": 500},
            context={"endpoint": "/api/reports"}
        )
        
        notification_dict = notification.to_dict()
        
        assert notification_dict["type"] == "performance_metric"
        assert notification_dict["value"] == 350.75
        assert notification_dict["status"] == "warning"  # Above warning threshold
        assert notification_dict["context"]["endpoint"] == "/api/reports"


@pytest.mark.asyncio
async def test_websocket_endpoint_integration():
    """Integration test for WebSocket endpoint using TestClient"""
    with TestClient(app) as client:
        # Test WebSocket connection
        with client.websocket_connect("/ws/test-client") as websocket:
            # Receive welcome message
            welcome_data = websocket.receive_json()
            assert welcome_data["type"] == "connection_established"
            assert "client_id" in welcome_data
            
            # Test subscription
            subscribe_message = {
                "type": "subscribe",
                "subscription": "mcp_operations"
            }
            websocket.send_json(subscribe_message)
            
            # Test ping
            ping_message = {"type": "ping"}
            websocket.send_json(ping_message)
            pong_response = websocket.receive_json()
            assert pong_response["type"] == "pong"
            
            # Test metrics request
            metrics_message = {"type": "get_metrics"}
            websocket.send_json(metrics_message)
            metrics_response = websocket.receive_json()
            assert metrics_response["type"] == "metrics"
            assert "client_metrics" in metrics_response


@pytest.mark.asyncio
async def test_websocket_real_connection():
    """Test actual WebSocket connection (requires running server)"""
    # This test requires the FastAPI server to be running
    pytest.skip("Requires running FastAPI server - run manually for integration testing")
    
    async with connect("ws://localhost:8000/ws/test-client") as websocket:
        # Receive welcome message
        welcome_data = json.loads(await websocket.recv())
        assert welcome_data["type"] == "connection_established"
        
        # Test subscription
        subscribe_message = {
            "type": "subscribe", 
            "subscription": "mcp_operations"
        }
        await websocket.send(json.dumps(subscribe_message))
        
        # Test that we can receive MCP operation notifications
        # (This would require actual MCP operations happening)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])