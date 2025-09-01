#!/usr/bin/env python3
"""
Minimal WebSocket test with simplified FastAPI app

Tests WebSocket functionality without the full app middleware stack
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient

from app.websockets.manager import ConnectionManager
from app.websockets.notifications import NotificationService

# Create minimal FastAPI app for testing
app = FastAPI()

# Create connection manager instance for testing
connection_manager = ConnectionManager()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for testing"""
    try:
        # Connect and initialize client
        actual_client_id = await connection_manager.connect(websocket, client_id)
        
        # Main message processing loop
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                # Process client message
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "client_id": actual_client_id
                    }))
                elif message_type == "subscribe":
                    channel = message.get("channel")
                    await connection_manager.subscribe(actual_client_id, channel)
                    await websocket.send_text(json.dumps({
                        "type": "subscription_confirmed",
                        "channel": channel
                    }))
                elif message_type == "get_metrics":
                    await websocket.send_text(json.dumps({
                        "type": "metrics",
                        "active_connections": len(connection_manager.active_connections),
                        "subscriptions": {k: len(v) for k, v in connection_manager.subscriptions.items()}
                    }))
                elif message_type == "heartbeat":
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "client_id": actual_client_id
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "error": str(e)
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        connection_manager.disconnect(client_id)


class TestWebSocketMinimal:
    """Minimal WebSocket tests with simplified app"""
    
    @pytest.fixture(autouse=True)
    def setup_test(self):
        """Setup test environment"""
        # Clear connection manager before each test
        connection_manager.active_connections.clear()
        # Reinitialize subscriptions with predefined types
        connection_manager.subscriptions = {
            "mcp_operations": set(),
            "system_updates": set(),
            "performance_metrics": set(),
            "error_notifications": set()
        }
        
        yield
        
        # Cleanup
        connection_manager.active_connections.clear()
        connection_manager.subscriptions = {
            "mcp_operations": set(),
            "system_updates": set(),
            "performance_metrics": set(),
            "error_notifications": set()
        }
    
    @pytest.fixture
    def test_client(self):
        """Create FastAPI test client"""
        return TestClient(app)
    
    def test_websocket_connection(self, test_client):
        """Test WebSocket connection establishment"""
        with test_client.websocket_connect("/ws/test-client-123") as websocket:
            # Connection should be established
            assert "test-client-123" in connection_manager.active_connections
            
            # Receive welcome message first
            welcome = websocket.receive_text()
            welcome_data = json.loads(welcome)
            assert welcome_data["type"] == "connection_established"
            
            # Send a ping message
            websocket.send_text(json.dumps({
                "type": "ping",
                "client_id": "test-client-123"
            }))
            
            # Should receive pong response
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "pong"
            assert response_data["client_id"] == "test-client-123"
    
    def test_websocket_subscription(self, test_client):
        """Test WebSocket subscription functionality"""
        with test_client.websocket_connect("/ws/test-client-456") as websocket:
            # Receive welcome message first
            welcome = websocket.receive_text()
            welcome_data = json.loads(welcome)
            assert welcome_data["type"] == "connection_established"
            
            # Subscribe to a channel
            websocket.send_text(json.dumps({
                "type": "subscribe",
                "channel": "mcp_operations",
                "client_id": "test-client-456"
            }))
            
            # Should receive subscription confirmation (could be either subscription_confirmed from endpoint or subscription_added from manager)
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] in ["subscription_confirmed", "subscription_added"]
            if response_data["type"] == "subscription_confirmed":
                assert response_data["channel"] == "mcp_operations"
            else:
                assert response_data["subscription"] == "mcp_operations"
            
            # Verify subscription was created
            assert "test-client-456" in connection_manager.subscriptions["mcp_operations"]
    
    def test_websocket_metrics_request(self, test_client):
        """Test WebSocket metrics request"""
        with test_client.websocket_connect("/ws/test-client-789") as websocket:
            # Receive welcome message first
            welcome = websocket.receive_text()
            welcome_data = json.loads(welcome)
            assert welcome_data["type"] == "connection_established"
            
            # Request metrics
            websocket.send_text(json.dumps({
                "type": "get_metrics",
                "client_id": "test-client-789"
            }))
            
            # Should receive metrics response
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "metrics"
            assert "active_connections" in response_data
            assert "subscriptions" in response_data
    
    def test_websocket_heartbeat(self, test_client):
        """Test WebSocket heartbeat functionality"""
        with test_client.websocket_connect("/ws/heartbeat-client") as websocket:
            # Receive welcome message first
            welcome = websocket.receive_text()
            welcome_data = json.loads(welcome)
            assert welcome_data["type"] == "connection_established"
            
            # Send heartbeat ping
            websocket.send_text(json.dumps({
                "type": "heartbeat",
                "client_id": "heartbeat-client"
            }))
            
            # Should receive heartbeat response
            response = websocket.receive_text()
            response_data = json.loads(response)
            assert response_data["type"] == "heartbeat"
            assert response_data["client_id"] == "heartbeat-client"


if __name__ == "__main__":
    # Run the minimal WebSocket tests
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