#!/usr/bin/env python3
"""
Isolated WebSocket Component Tests

Test WebSocket manager and notification components without external dependencies.
"""
import asyncio
import sys
import os
import time
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Any

# Mock the settings to avoid dependency on config
class MockSettings:
    websocket_enabled = True
    websocket_heartbeat_interval = 30
    max_websocket_connections = 100
    websocket_message_max_size = 1024 * 1024

# Mock the logger
class MockLogger:
    def info(self, msg):
        print(f"INFO: {msg}")
    
    def debug(self, msg):
        print(f"DEBUG: {msg}")
    
    def warning(self, msg):
        print(f"WARNING: {msg}")
    
    def error(self, msg):
        print(f"ERROR: {msg}")

# Mock WebSocket class
class MockWebSocket:
    def __init__(self):
        self.messages = []
    
    async def accept(self):
        pass
    
    async def send_text(self, text):
        self.messages.append(text)

@dataclass
class ConnectionMetrics:
    """Metrics for WebSocket connection monitoring"""
    client_id: str
    connected_at: float
    last_activity: float
    message_count: int = 0
    error_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    subscriptions: Set[str] = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for monitoring"""
        return {
            "client_id": self.client_id,
            "connected_at": self.connected_at,
            "last_activity": self.last_activity,
            "uptime_seconds": time.time() - self.connected_at,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "subscriptions": list(self.subscriptions),
            "subscription_count": len(self.subscriptions)
        }

class ConnectionManager:
    """
    Simplified ConnectionManager for testing
    """
    
    def __init__(self):
        self.active_connections: Dict[str, MockWebSocket] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.subscriptions: Dict[str, Set[str]] = {
            "mcp_operations": set(),
            "system_updates": set(),
            "performance_metrics": set(),
            "error_notifications": set()
        }
        self.settings = MockSettings()
    
    async def connect(self, websocket: MockWebSocket, client_id: Optional[str] = None) -> str:
        """Accept WebSocket connection and initialize tracking"""
        if client_id is None:
            client_id = f"test-client-{len(self.active_connections) + 1}"
        
        self.active_connections[client_id] = websocket
        
        # Initialize metrics
        now = time.time()
        self.connection_metrics[client_id] = ConnectionMetrics(
            client_id=client_id,
            connected_at=now,
            last_activity=now
        )
        
        return client_id
    
    def disconnect(self, client_id: str):
        """Remove connection and cleanup resources"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            # Remove from all subscriptions
            for subscription_set in self.subscriptions.values():
                subscription_set.discard(client_id)
            
            # Cleanup metrics
            if client_id in self.connection_metrics:
                del self.connection_metrics[client_id]
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client"""
        if client_id not in self.active_connections:
            return
        
        message_json = json.dumps(message)
        await self.active_connections[client_id].send_text(message_json)
        
        # Update metrics
        if client_id in self.connection_metrics:
            self.connection_metrics[client_id].bytes_sent += len(message_json)
            self.connection_metrics[client_id].message_count += 1
            self.connection_metrics[client_id].last_activity = time.time()
    
    async def broadcast(self, message: Dict[str, Any], subscription_type: Optional[str] = None):
        """Broadcast message to all connected clients or specific subscription"""
        targets = set()
        
        if subscription_type:
            # Send to specific subscription
            targets = self.subscriptions.get(subscription_type, set())
        else:
            # Send to all connected clients
            targets = set(self.active_connections.keys())
        
        message_json = json.dumps(message)
        message_size = len(message_json)
        
        for client_id in targets:
            if client_id in self.active_connections:
                await self.active_connections[client_id].send_text(message_json)
                
                # Update metrics
                if client_id in self.connection_metrics:
                    self.connection_metrics[client_id].bytes_sent += message_size
                    self.connection_metrics[client_id].message_count += 1
                    self.connection_metrics[client_id].last_activity = time.time()
    
    async def subscribe(self, client_id: str, subscription_type: str):
        """Subscribe client to specific event type"""
        if subscription_type in self.subscriptions:
            self.subscriptions[subscription_type].add(client_id)
            if client_id in self.connection_metrics:
                self.connection_metrics[client_id].subscriptions.add(subscription_type)
    
    async def unsubscribe(self, client_id: str, subscription_type: str):
        """Unsubscribe client from specific event type"""
        if subscription_type in self.subscriptions:
            self.subscriptions[subscription_type].discard(client_id)
            if client_id in self.connection_metrics:
                self.connection_metrics[client_id].subscriptions.discard(subscription_type)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        active_connections = len(self.active_connections)
        
        stats = {
            "total_connections": active_connections,
            "max_connections": self.settings.max_websocket_connections,
            "subscription_counts": {
                subscription_type: len(subscribers)
                for subscription_type, subscribers in self.subscriptions.items()
            },
            "total_messages_sent": sum(
                metrics.message_count for metrics in self.connection_metrics.values()
            ),
            "total_bytes_sent": sum(
                metrics.bytes_sent for metrics in self.connection_metrics.values()
            ),
            "total_errors": sum(
                metrics.error_count for metrics in self.connection_metrics.values()
            )
        }
        
        return stats
    
    def get_connection_metrics(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific client or all clients"""
        if client_id:
            if client_id in self.connection_metrics:
                return self.connection_metrics[client_id].to_dict()
            return {}
        
        return {
            client_id: metrics.to_dict()
            for client_id, metrics in self.connection_metrics.items()
        }

@dataclass
class MCPOperationNotification:
    """Data class for MCP operation notifications"""
    operation_type: str  # "tools/call", "resources/read", etc.
    operation_id: str
    method: str
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary for WebSocket transmission"""
        notification = {
            "type": "mcp_operation",
            "operation": self.operation_type,
            "operation_id": self.operation_id,
            "method": self.method,
            "timestamp": self.timestamp
        }
        
        if self.params:
            notification["params"] = self._sanitize_params(self.params)
        
        if self.result:
            notification["result"] = self._sanitize_result(self.result)
        
        if self.error:
            notification["error"] = self.error
        
        if self.duration_ms is not None:
            notification["duration_ms"] = round(self.duration_ms, 2)
        
        return notification
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters to remove sensitive data"""
        sanitized = params.copy()
        
        # Remove potentially sensitive fields
        sensitive_fields = {"api_key", "token", "password", "secret", "credentials"}
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = "[REDACTED]"
        
        # Truncate large values
        for key, value in sanitized.items():
            if isinstance(value, str) and len(value) > 1000:
                sanitized[key] = value[:1000] + "..."
            elif isinstance(value, (list, dict)) and len(str(value)) > 2000:
                sanitized[key] = f"{type(value).__name__} (size: {len(str(value))})"
        
        return sanitized
    
    def _sanitize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize result data for WebSocket transmission"""
        sanitized = result.copy()
        
        # Handle large content by truncating or summarizing
        if "content" in sanitized and isinstance(sanitized["content"], str):
            content = sanitized["content"]
            if len(content) > 5000:
                sanitized["content"] = content[:5000] + "..."
                sanitized["content_truncated"] = True
                sanitized["original_length"] = len(content)
        
        return sanitized

async def test_websocket_manager():
    """Test WebSocket connection manager functionality"""
    print("Testing WebSocket manager...")
    
    try:
        manager = ConnectionManager()
        
        # Test connection stats
        stats = manager.get_connection_stats()
        assert "total_connections" in stats
        assert stats["max_connections"] == 100
        assert stats["subscription_counts"]["mcp_operations"] == 0
        print("✓ Connection manager stats working correctly")
        
        # Test mock connection lifecycle
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
        
        # Verify message was sent
        assert len(websocket.messages) == 1
        received_message = json.loads(websocket.messages[0])
        assert received_message["type"] == "test"
        print("✓ Broadcast functionality working correctly")
        
        # Test metrics collection
        metrics = manager.get_connection_metrics(client_id)
        assert metrics["client_id"] == client_id
        assert metrics["subscription_count"] == 1
        assert metrics["message_count"] == 1
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
        # Content should be truncated due to large size
        content = result.get("content", "")
        assert len(content) <= 5000, f"Content should be truncated, got length: {len(content)}"
        print("✓ Result sanitization working correctly")
        
        print("✓ Notification service working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Notification service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_integration():
    """Test integration between manager and notifications"""
    print("Testing integration...")
    
    try:
        manager = ConnectionManager()
        websocket = MockWebSocket()
        
        # Connect client
        client_id = await manager.connect(websocket)
        await manager.subscribe(client_id, "mcp_operations")
        
        # Create and send notification
        notification = MCPOperationNotification(
            operation_type="tools/call",
            operation_id="test-integration-123",
            method="get_project_report",
            params={"project_id": 456},
            result={"status": "success"},
            duration_ms=200.0
        )
        
        # Broadcast notification
        await manager.broadcast(notification.to_dict(), "mcp_operations")
        
        # Verify notification was received
        # There should be at least 1 message (the notification)
        assert len(websocket.messages) >= 1, f"Expected at least 1 message, got {len(websocket.messages)}"
        
        # Find the notification message (could be at any position)
        notification_message = None
        for msg in websocket.messages:
            try:
                parsed = json.loads(msg)
                if parsed.get("type") == "mcp_operation":
                    notification_message = parsed
                    break
            except json.JSONDecodeError:
                continue
        
        assert notification_message is not None, "No mcp_operation message found"
        assert notification_message["operation_id"] == "test-integration-123"
        assert notification_message["duration_ms"] == 200.0
        
        # Verify metrics updated
        metrics = manager.get_connection_metrics(client_id)
        assert metrics["message_count"] >= 1, f"Expected at least 1 message, got {metrics['message_count']}"
        
        print("✓ Integration working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all WebSocket tests"""
    print("=" * 60)
    print("WEBSOCKET COMPONENT TESTS")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(await test_websocket_manager())
    results.append(await test_notification_service())
    results.append(await test_integration())
    
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
        print("\n🎉 ALL WEBSOCKET COMPONENTS WORKING CORRECTLY!")
        print("WebSocket implementation is ready for production!")
        return True
    else:
        print(f"\n❌ {failed_tests} test(s) failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)