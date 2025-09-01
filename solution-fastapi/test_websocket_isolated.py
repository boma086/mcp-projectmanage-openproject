#!/usr/bin/env python3
"""
Isolated WebSocket component tests

Tests WebSocket components without external dependencies
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.websockets.manager import ConnectionManager
from app.websockets.notifications import NotificationService


class TestWebSocketIsolated:
    """Isolated WebSocket component tests"""
    
    @pytest.fixture
    def connection_manager(self):
        """Create WebSocket connection manager"""
        return ConnectionManager()
    
    @pytest.fixture
    def notification_service(self):
        """Create WebSocket notification service"""
        return NotificationService()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        mock_ws = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect_disconnect(self, connection_manager, mock_websocket):
        """Test connection manager connect and disconnect"""
        # Test connection
        client_id = await connection_manager.connect(mock_websocket, "test-client")
        assert client_id == "test-client"
        assert len(connection_manager.active_connections) == 1
        assert "test-client" in connection_manager.active_connections
        
        # Test disconnect
        await connection_manager.disconnect("test-client")
        assert len(connection_manager.active_connections) == 0
        assert "test-client" not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_connection_manager_subscribe_unsubscribe(self, connection_manager, mock_websocket):
        """Test subscription management"""
        await connection_manager.connect(mock_websocket, "test-client")
        
        # Test subscribe
        await connection_manager.subscribe("test-client", "mcp_operations")
        assert "test-client" in connection_manager.subscriptions["mcp_operations"]
        
        # Test unsubscribe
        await connection_manager.unsubscribe("test-client", "mcp_operations")
        assert "test-client" not in connection_manager.subscriptions["mcp_operations"]
        
        await connection_manager.disconnect("test-client")
    
    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self, connection_manager, mock_websocket):
        """Test broadcast functionality"""
        await connection_manager.connect(mock_websocket, "test-client")
        
        # Reset mock to ignore the welcome message
        mock_websocket.send_text.reset_mock()
        
        # Test broadcast to all
        await connection_manager.broadcast({"type": "test_message", "content": "test"})
        mock_websocket.send_text.assert_called_once()
        
        await connection_manager.disconnect("test-client")
    
    @pytest.mark.asyncio
    async def test_notification_service_send_notification(self, notification_service):
        """Test notification service"""
        # Mock connection manager
        mock_manager = AsyncMock()
        
        # Patch the global connection_manager
        with patch('app.websockets.notifications.connection_manager', mock_manager):
            # Test send notification
            await notification_service.notify_mcp_operation(
                operation_type="tools/call",
                operation_id="test-123",
                method="get_projects",
                params={},
                result={"projects": []},
                duration_ms=100.0
            )
            
            # Verify broadcast was called
            mock_manager.broadcast.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_notification_service_sanitize_data(self):
        """Test data sanitization"""
        from app.websockets.notifications import MCPOperationNotification
        
        # Test with sensitive data in params (top-level only)
        notification = MCPOperationNotification(
            operation_type="tools/call",
            operation_id="test-123",
            method="get_projects",
            params={
                "api_key": "secret-key-123",
                "password": "mypassword", 
                "message": "normal message",
                "token": "bearer-token",
                "safe_data": "ok"
            }
        )
        
        sanitized = notification.to_dict()
        
        # Verify sensitive data is masked in params (top-level only)
        assert sanitized["params"]["api_key"] == "[REDACTED]"
        assert sanitized["params"]["password"] == "[REDACTED]"
        assert sanitized["params"]["token"] == "[REDACTED]"
        assert sanitized["params"]["message"] == "normal message"
        assert sanitized["params"]["safe_data"] == "ok"


if __name__ == "__main__":
    # Run the isolated WebSocket tests
    import pytest
    import sys
    
    # Add the solution-fastapi directory to Python path
    sys.path.insert(0, '/Users/mabo/developer/repository/git/mcp-projectmanage-openproject/solution-fastapi')
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])
    
    sys.exit(exit_code)