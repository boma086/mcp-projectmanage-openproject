"""
WebSocket Notifications for MCP Operations

This module provides real-time notifications for MCP operations including:
- tools/call operations with detailed execution results
- resources/read operations with metadata and content
- System-wide updates and performance metrics
- Error notifications and connection status updates
"""
import time
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from app.websockets.manager import connection_manager

# Import logger from mcp_core (same as main.py)
from mcp_core import get_logger

logger = get_logger("websocket.notifications")


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
            "timestamp": self.timestamp,
            "server_time": datetime.utcfromtimestamp(self.timestamp).isoformat()
        }
        
        if self.params:
            notification["params"] = self._sanitize_params(self.params)
        
        if self.result:
            notification["result"] = self._sanitize_result(self.result)
        
        if self.error:
            notification["error"] = self.error
        
        if self.duration_ms is not None:
            notification["duration_ms"] = round(self.duration_ms, 2)
            notification["performance"] = {
                "fast": self.duration_ms < 100,
                "moderate": 100 <= self.duration_ms < 500,
                "slow": self.duration_ms >= 500
            }
        
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
        
        # Add metadata for large results
        result_size = len(json.dumps(sanitized, ensure_ascii=False))
        if result_size > 10000:
            sanitized["result_size_bytes"] = result_size
            sanitized["result_summary"] = f"Large result ({result_size} bytes)"
        
        return sanitized


@dataclass
class SystemNotification:
    """Data class for system-wide notifications"""
    notification_type: str  # "system_update", "maintenance", "error", "info"
    message: str
    severity: str = "info"  # "info", "warning", "error", "critical"
    details: Optional[Dict[str, Any]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system notification to dictionary"""
        notification = {
            "type": "system_notification",
            "notification_type": self.notification_type,
            "message": self.message,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "server_time": datetime.utcfromtimestamp(self.timestamp).isoformat()
        }
        
        if self.details:
            notification["details"] = self.details
        
        return notification


@dataclass
class PerformanceNotification:
    """Data class for performance metrics notifications"""
    metric_type: str  # "request", "database", "cache", "websocket"
    metric_name: str
    value: float
    unit: str = "ms"
    thresholds: Optional[Dict[str, float]] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance notification to dictionary"""
        notification = {
            "type": "performance_metric",
            "metric_type": self.metric_type,
            "metric_name": self.metric_name,
            "value": round(self.value, 2),
            "unit": self.unit,
            "timestamp": self.timestamp,
            "server_time": datetime.utcfromtimestamp(self.timestamp).isoformat()
        }
        
        if self.thresholds:
            notification["thresholds"] = self.thresholds
            notification["status"] = self._get_status()
        
        if self.context:
            notification["context"] = self.context
        
        return notification
    
    def _get_status(self) -> str:
        """Get status based on thresholds"""
        if not self.thresholds:
            return "normal"
        
        warning_threshold = self.thresholds.get("warning")
        error_threshold = self.thresholds.get("error")
        
        if error_threshold and self.value >= error_threshold:
            return "error"
        elif warning_threshold and self.value >= warning_threshold:
            return "warning"
        else:
            return "normal"


class NotificationService:
    """Service for sending real-time notifications via WebSocket"""
    
    @staticmethod
    async def notify_mcp_operation(
        operation_type: str,
        operation_id: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """Send notification for MCP operation completion"""
        try:
            notification = MCPOperationNotification(
                operation_type=operation_type,
                operation_id=operation_id,
                method=method,
                params=params,
                result=result,
                error=error,
                duration_ms=duration_ms
            )
            
            await connection_manager.broadcast(
                notification.to_dict(),
                "mcp_operations"
            )
            
            logger.debug(
                f"MCP operation notification sent: {operation_type} {method} "
                f"(duration: {duration_ms}ms)"
            )
            
        except Exception as e:
            logger.error(f"Failed to send MCP operation notification: {e}")
    
    @staticmethod
    async def notify_system_update(
        message: str,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None
    ):
        """Send system-wide notification"""
        try:
            notification = SystemNotification(
                notification_type="system_update",
                message=message,
                severity=severity,
                details=details
            )
            
            await connection_manager.broadcast(
                notification.to_dict(),
                "system_updates"
            )
            
            logger.info(f"System notification sent: {message} (severity: {severity})")
            
        except Exception as e:
            logger.error(f"Failed to send system notification: {e}")
    
    @staticmethod
    async def notify_performance_metric(
        metric_type: str,
        metric_name: str,
        value: float,
        unit: str = "ms",
        thresholds: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Send performance metric notification"""
        try:
            notification = PerformanceNotification(
                metric_type=metric_type,
                metric_name=metric_name,
                value=value,
                unit=unit,
                thresholds=thresholds,
                context=context
            )
            
            await connection_manager.broadcast(
                notification.to_dict(),
                "performance_metrics"
            )
            
            logger.debug(
                f"Performance metric notification sent: {metric_type}.{metric_name} = "
                f"{value}{unit}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send performance notification: {e}")
    
    @staticmethod
    async def notify_error(
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Send error notification"""
        try:
            notification = SystemNotification(
                notification_type="error",
                message=message,
                severity="error",
                details={
                    "error_type": error_type,
                    "context": context or {}
                }
            )
            
            await connection_manager.broadcast(
                notification.to_dict(),
                "error_notifications"
            )
            
            logger.warning(f"Error notification sent: {error_type} - {message}")
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    @staticmethod
    async def notify_connection_status(
        client_id: str,
        status: str,  # "connected", "disconnected", "reconnected"
        details: Optional[Dict[str, Any]] = None
    ):
        """Send connection status notification"""
        try:
            notification = SystemNotification(
                notification_type="connection_status",
                message=f"Client {client_id} {status}",
                severity="info",
                details={
                    "client_id": client_id,
                    "status": status,
                    ** (details or {})
                }
            )
            
            await connection_manager.broadcast(
                notification.to_dict(),
                "system_updates"
            )
            
            logger.info(f"Connection status notification sent: {client_id} {status}")
            
        except Exception as e:
            logger.error(f"Failed to send connection status notification: {e}")


# Global notification service instance
notification_service = NotificationService()