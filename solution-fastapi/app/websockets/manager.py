"""
WebSocket Connection Manager for Real-time MCP Operations

This module provides a comprehensive WebSocket connection manager with:
- Connection lifecycle management
- Real-time notifications for MCP operations
- Broadcast functionality for system-wide updates
- Heartbeat mechanism for connection health
- Connection metrics and monitoring support
- Graceful error handling and degradation
"""
import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from app.core.config import get_settings

# Import logger from mcp_core (same as main.py)
from mcp_core import get_logger

logger = get_logger("websocket.manager")
settings = get_settings()


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
    Manages WebSocket connections with advanced features:
    - Connection pooling and lifecycle management
    - Real-time notifications for MCP operations
    - Broadcast and targeted messaging
    - Heartbeat and connection health monitoring
    - Subscription management for different event types
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.subscriptions: Dict[str, Set[str]] = {
            "mcp_operations": set(),
            "system_updates": set(),
            "performance_metrics": set(),
            "error_notifications": set()
        }
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._connection_lock = asyncio.Lock()
        self._subscription_lock = asyncio.Lock()
    
    async def start(self):
        """Start background tasks for heartbeat and metrics"""
        if not self._is_running:
            self._is_running = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._metrics_task = asyncio.create_task(self._metrics_loop())
            logger.info("WebSocket manager background tasks started")
    
    async def stop(self):
        """Stop background tasks and clean up"""
        self._is_running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._metrics_task:
            self._metrics_task.cancel()
        logger.info("WebSocket manager background tasks stopped")
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """Accept WebSocket connection and initialize tracking"""
        if client_id is None:
            client_id = str(uuid.uuid4())
        
        async with self._connection_lock:
            # Check connection limits
            if len(self.active_connections) >= settings.max_websocket_connections:
                raise WebSocketDisconnect(
                    code=1008,  # Policy violation
                    reason="Maximum connections reached"
                )
            
            await websocket.accept()
            self.active_connections[client_id] = websocket
            
            # Initialize metrics
            now = time.time()
            self.connection_metrics[client_id] = ConnectionMetrics(
                client_id=client_id,
                connected_at=now,
                last_activity=now
            )
        
        logger.info(f"WebSocket client {client_id} connected")
        
        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Connected to MCP WebSocket server",
            "timestamp": now,
            "server_info": {
                "name": settings.app_name,
                "version": settings.app_version,
                "max_connections": settings.max_websocket_connections
            }
        }, client_id)
        
        return client_id
    
    async def disconnect(self, client_id: str):
        """Remove connection and cleanup resources"""
        async with self._connection_lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
                
                # Remove from all subscriptions
                async with self._subscription_lock:
                    for subscription_set in self.subscriptions.values():
                        subscription_set.discard(client_id)
                
                # Cleanup metrics
                if client_id in self.connection_metrics:
                    del self.connection_metrics[client_id]
                
                logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client with error handling"""
        async with self._connection_lock:
            if client_id not in self.active_connections:
                logger.warning(f"Attempted to send message to disconnected client: {client_id}")
                return
        
        try:
            message_json = json.dumps(message)
            async with self._connection_lock:
                if client_id in self.active_connections:
                    await self.active_connections[client_id].send_text(message_json)
                    
                    # Update metrics
                    if client_id in self.connection_metrics:
                        self.connection_metrics[client_id].bytes_sent += len(message_json)
                        self.connection_metrics[client_id].message_count += 1
                        self.connection_metrics[client_id].last_activity = time.time()
                
        except WebSocketDisconnect:
            await self.disconnect(client_id)
        except Exception as e:
            logger.error(f"Failed to send message to client {client_id}: {e}")
            if client_id in self.connection_metrics:
                self.connection_metrics[client_id].error_count += 1
    
    async def broadcast(self, message: Dict[str, Any], subscription_type: Optional[str] = None):
        """Broadcast message to all connected clients or specific subscription"""
        async with self._subscription_lock:
            if subscription_type:
                # Send to specific subscription
                targets = self.subscriptions.get(subscription_type, set()).copy()
            else:
                # Send to all connected clients
                async with self._connection_lock:
                    targets = set(self.active_connections.keys())
        
        message_json = json.dumps(message)
        message_size = len(message_json)
        
        for client_id in targets:
            async with self._connection_lock:
                if client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_text(message_json)
                        
                        # Update metrics
                        if client_id in self.connection_metrics:
                            self.connection_metrics[client_id].bytes_sent += message_size
                            self.connection_metrics[client_id].message_count += 1
                            self.connection_metrics[client_id].last_activity = time.time()
                            
                    except WebSocketDisconnect:
                        await self.disconnect(client_id)
                    except Exception as e:
                        logger.error(f"Failed to broadcast to client {client_id}: {e}")
                        if client_id in self.connection_metrics:
                            self.connection_metrics[client_id].error_count += 1
    
    async def subscribe(self, client_id: str, subscription_type: str):
        """Subscribe client to specific event type"""
        async with self._subscription_lock:
            if subscription_type in self.subscriptions:
                self.subscriptions[subscription_type].add(client_id)
                if client_id in self.connection_metrics:
                    self.connection_metrics[client_id].subscriptions.add(subscription_type)
                
                logger.info(f"Client {client_id} subscribed to {subscription_type}")
                
                await self.send_personal_message({
                    "type": "subscription_added",
                    "subscription": subscription_type,
                    "message": f"Subscribed to {subscription_type} events",
                    "timestamp": time.time()
                }, client_id)
    
    async def unsubscribe(self, client_id: str, subscription_type: str):
        """Unsubscribe client from specific event type"""
        async with self._subscription_lock:
            if subscription_type in self.subscriptions:
                self.subscriptions[subscription_type].discard(client_id)
                if client_id in self.connection_metrics:
                    self.connection_metrics[client_id].subscriptions.discard(subscription_type)
                
                logger.info(f"Client {client_id} unsubscribed from {subscription_type}")
                
                await self.send_personal_message({
                    "type": "subscription_removed",
                    "subscription": subscription_type,
                    "message": f"Unsubscribed from {subscription_type} events",
                    "timestamp": time.time()
                }, client_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get comprehensive connection statistics"""
        now = time.time()
        # For synchronous access, we need to handle the lock differently
        # Since this is just reading data, we'll access it directly without locking
        active_connections = len(self.active_connections)
        
        stats = {
            "total_connections": active_connections,
            "max_connections": settings.max_websocket_connections,
            "connection_utilization": f"{(active_connections / settings.max_websocket_connections) * 100:.1f}%",
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
            ),
            "uptime_seconds": now - min(
                (metrics.connected_at for metrics in self.connection_metrics.values()),
                default=now
            )
        }
        
        return stats
    
    async def get_connection_metrics(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for specific client or all clients"""
        async with self._connection_lock:
            if client_id:
                if client_id in self.connection_metrics:
                    return self.connection_metrics[client_id].to_dict()
                return {}
            
            return {
                client_id: metrics.to_dict()
                for client_id, metrics in self.connection_metrics.items()
            }
    
    async def _heartbeat_loop(self):
        """Background task to send heartbeat messages"""
        while self._is_running:
            try:
                await asyncio.sleep(settings.websocket_heartbeat_interval)
                
                # Send heartbeat to all active connections
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": time.time(),
                    "server_time": datetime.utcnow().isoformat()
                }
                
                await self.broadcast(heartbeat_message, "system_updates")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _metrics_loop(self):
        """Background task to log connection metrics"""
        while self._is_running:
            try:
                await asyncio.sleep(60)  # Log every minute
                
                stats = self.get_connection_stats()
                logger.info(
                    f"WebSocket metrics - Connections: {stats['total_connections']}/"
                    f"{stats['max_connections']}, Messages: {stats['total_messages_sent']}, "
                    f"Bytes: {stats['total_bytes_sent']}, Errors: {stats['total_errors']}"
                )
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics loop error: {e}")
                await asyncio.sleep(30)  # Wait before retrying


# Global connection manager instance
connection_manager = ConnectionManager()