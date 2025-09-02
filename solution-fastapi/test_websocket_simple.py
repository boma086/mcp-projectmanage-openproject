#!/usr/bin/env python3
"""
Simple WebSocket tests focusing on core functionality
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.websockets.manager import ConnectionManager


class TestWebSocketSimple:
    """Simple WebSocket tests focusing on core functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test environment"""
        self.manager = ConnectionManager()
        
        # Mock WebSocket connection
        self.mock_websocket = AsyncMock()
        self.mock_websocket.send_text = AsyncMock()
        
        yield
        
        # Cleanup
        self.manager.active_connections.clear()
        self.manager.connection_metrics.clear()
        self.manager.subscriptions.clear()
    
    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test basic connection management"""
        # Connect a client
        client_id = await self.manager.connect(self.mock_websocket, "test-client-123")
        assert client_id == "test-client-123"
        assert client_id in self.manager.active_connections
        
        # Verify metrics were created
        assert client_id in self.manager.connection_metrics
        metrics = self.manager.connection_metrics[client_id]
        assert metrics.client_id == "test-client-123"
        assert metrics.message_count == 1  # Welcome message
        
        # Disconnect
        await self.manager.disconnect(client_id)
        assert client_id not in self.manager.active_connections
        assert client_id not in self.manager.connection_metrics
    
    @pytest.mark.asyncio
    async def test_subscription_management(self):
        """Test subscription functionality"""
        # Connect a client
        client_id = await self.manager.connect(self.mock_websocket, "test-client-456")
        
        # Subscribe to a channel
        await self.manager.subscribe(client_id, "mcp_operations")
        assert "mcp_operations" in self.manager.subscriptions
        assert client_id in self.manager.subscriptions["mcp_operations"]
        
        # Verify metrics were updated
        metrics = self.manager.connection_metrics[client_id]
        assert "mcp_operations" in metrics.subscriptions
        
        # Unsubscribe
        await self.manager.unsubscribe(client_id, "mcp_operations")
        assert client_id not in self.manager.subscriptions["mcp_operations"]
        assert "mcp_operations" not in metrics.subscriptions
    
    @pytest.mark.asyncio
    async def test_message_sending(self):
        """Test message sending functionality"""
        # Connect a client
        client_id = await self.manager.connect(self.mock_websocket, "test-client-789")
        
        # Send a message
        test_message = {"type": "test", "data": "hello"}
        await self.manager.send_personal_message(test_message, client_id)
        
        # Verify message was sent
        self.mock_websocket.send_text.assert_called_with(json.dumps(test_message))
        
        # Verify metrics were updated
        metrics = self.manager.connection_metrics[client_id]
        assert metrics.message_count == 2  # Welcome message + test message
    
    @pytest.mark.asyncio
    async def test_broadcast_functionality(self):
        """Test broadcast functionality"""
        # Connect multiple clients
        mock_websocket2 = AsyncMock()
        mock_websocket2.send_text = AsyncMock()
        
        client1 = await self.manager.connect(self.mock_websocket, "client-1")
        client2 = await self.manager.connect(mock_websocket2, "client-2")
        
        # Subscribe both to same channel
        await self.manager.subscribe(client1, "system_updates")
        await self.manager.subscribe(client2, "system_updates")
        
        # Broadcast message
        broadcast_msg = {"type": "broadcast", "message": "test"}
        await self.manager.broadcast(broadcast_msg, "system_updates")
        
        # Verify both clients received the message
        self.mock_websocket.send_text.assert_called_with(json.dumps(broadcast_msg))
        mock_websocket2.send_text.assert_called_with(json.dumps(broadcast_msg))


if __name__ == "__main__":
    # Run the simple WebSocket tests
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