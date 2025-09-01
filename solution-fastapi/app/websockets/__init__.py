"""
WebSocket Module for Real-time MCP Operations

This module provides WebSocket support for real-time notifications, updates,
and live data streaming in the FastAPI MCP server.
"""

from app.websockets.manager import ConnectionManager, connection_manager
from app.websockets.notifications import (
    NotificationService,
    notification_service,
    MCPOperationNotification,
    SystemNotification,
    PerformanceNotification
)

__all__ = [
    "ConnectionManager",
    "connection_manager",
    "NotificationService", 
    "notification_service",
    "MCPOperationNotification",
    "SystemNotification",
    "PerformanceNotification"
]