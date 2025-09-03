#!/usr/bin/env python3
"""
WebSocket integration tests with FastAPI TestClient

Tests WebSocket integration with the main FastAPI application
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from app.main import app, lifespan
from app.core.config import get_settings
from app.websockets.manager import connection_manager
from fastapi import FastAPI


class TestWebSocketIntegration:
    """WebSocket integration tests with FastAPI"""
    
    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test environment"""
        # Mock settings to enable WebSocket
        self.original_settings = get_settings()
        
        # Create test settings with WebSocket enabled
        test_settings = MagicMock()
        test_settings.websocket_enabled = True
        test_settings.max_websocket_connections = 100
        test_settings.websocket_heartbeat_interval = 30
        test_settings.openproject_url = "https://demo.openproject.org"
        test_settings.openproject_api_key = "test-api-key"
        test_settings.debug = True  # Disable host validation for tests
        test_settings.trusted_hosts = ["testserver", "localhost", "127.0.0.1"]
        
        # Patch settings
        self.settings_patch = patch('app.main.settings', test_settings)
        self.settings_patch.start()
        
        # Disable TrustedHostMiddleware by ensuring debug mode is True
        test_settings.debug = True
        
        # Clear connection manager before each test
        connection_manager.active_connections.clear()
        connection_manager.subscriptions.clear()
        
        yield
        
        # Cleanup
        self.settings_patch.stop()
        connection_manager.active_connections.clear()
        connection_manager.subscriptions.clear()
    
    @pytest.fixture
    def test_client(self):
        """Create FastAPI test client with test-specific app"""
        # Create test app without security middleware
        test_app = FastAPI(
            title="Test MCP Server",
            description="Test FastAPI MCP server without security middleware",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Only add essential middleware for testing
        from fastapi.middleware.cors import CORSMiddleware
        test_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Copy the WebSocket endpoint
        test_app.websocket_route("/ws/{client_id}", app.routes[0].endpoint)
        
        return TestClient(test_app)
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, test_client):
        """Test WebSocket connection establishment"""
        with test_client.websocket_connect("/ws/test-client-123") as websocket:
            # Connection should be established
            assert "test-client-123" in connection_manager.active_connections
            
            # Send a ping message
            await websocket.send_text(json.dumps({
                "type": "ping",
                "client_id": "test-client-123"
            }))
            
            # Should receive pong response
            response = await websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "pong"
            assert response_data["client_id"] == "test-client-123"
    
    @pytest.mark.asyncio
    async def test_websocket_subscription(self, test_client):
        """Test WebSocket subscription functionality"""
        with test_client.websocket_connect("/ws/test-client-456") as websocket:
            # Subscribe to a channel
            await websocket.send_text(json.dumps({
                "type": "subscribe",
                "channel": "mcp_operations",
                "client_id": "test-client-456"
            }))
            
            # Should receive subscription confirmation
            response = await websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "subscription_confirmed"
            assert response_data["channel"] == "mcp_operations"
            
            # Verify subscription was created
            assert "mcp_operations" in connection_manager.get_subscriptions("test-client-456")
    
    @pytest.mark.asyncio
    async def test_websocket_metrics_request(self, test_client):
        """Test WebSocket metrics request"""
        with test_client.websocket_connect("/ws/test-client-789") as websocket:
            # Request metrics
            await websocket.send_text(json.dumps({
                "type": "get_metrics",
                "client_id": "test-client-789"
            }))
            
            # Should receive metrics response
            response = await websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "metrics"
            assert "active_connections" in response_data
            assert "subscriptions" in response_data
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast_notification(self, test_client):
        """Test WebSocket broadcast notification"""
        # Connect two clients
        with test_client.websocket_connect("/ws/client-1") as ws1, \
             test_client.websocket_connect("/ws/client-2") as ws2:
            
            # Both clients subscribe to same channel
            for ws, client_id in [(ws1, "client-1"), (ws2, "client-2")]:
                await ws.send_text(json.dumps({
                    "type": "subscribe",
                    "channel": "project_updates",
                    "client_id": client_id
                }))
                # Consume subscription confirmation
                await ws.receive_text()
            
            # Broadcast notification to the channel
            from app.websockets.notifications import notification_service
            await notification_service.send_notification(
                "project_updates",
                "project_created",
                {"project_id": "test-project", "name": "Test Project"}
            )
            
            # Both clients should receive the notification
            for ws in [ws1, ws2]:
                response = await ws.receive_text()
                response_data = json.loads(response)
                assert response_data["type"] == "notification"
                assert response_data["channel"] == "project_updates"
                assert response_data["event"] == "project_created"
                assert response_data["data"]["project_id"] == "test-project"
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_message(self, test_client):
        """Test handling of invalid WebSocket messages"""
        with test_client.websocket_connect("/ws/test-client-999") as websocket:
            # Send invalid JSON
            await websocket.send_text("invalid json")
            
            # Should receive error response
            response = await websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "error"
            assert "error" in response_data
    
    @pytest.mark.asyncio
    async def test_websocket_heartbeat(self, test_client):
        """Test WebSocket heartbeat functionality"""
        with test_client.websocket_connect("/ws/heartbeat-client") as websocket:
            # Send heartbeat ping
            await websocket.send_text(json.dumps({
                "type": "heartbeat",
                "client_id": "heartbeat-client"
            }))
            
            # Should receive heartbeat response
            response = await websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "heartbeat"
            assert response_data["client_id"] == "heartbeat-client"


if __name__ == "__main__":
    # Run the WebSocket integration tests
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