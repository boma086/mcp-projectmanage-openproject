"""
Error Tracking and Reporting System

This module provides centralized error tracking, aggregation, and reporting
across all MCP OpenProject solutions.
"""

import json
import time
import threading
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import traceback
import uuid


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""
    NETWORK = "network"
    API = "api"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    DATABASE = "database"
    MCP_PROTOCOL = "mcp_protocol"
    EXTERNAL_SERVICE = "external_service"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Error event data structure"""
    id: str
    timestamp: datetime
    service: str
    severity: ErrorSeverity
    category: ErrorCategory
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    resolution_notes: Optional[str] = None


@dataclass
class ErrorStats:
    """Error statistics"""
    total_errors: int
    errors_by_severity: Dict[ErrorSeverity, int]
    errors_by_category: Dict[ErrorCategory, int]
    errors_by_service: Dict[str, int]
    error_rate: float  # errors per minute
    resolution_rate: float  # percentage of resolved errors
    avg_resolution_time: float  # average time to resolution in minutes


class ErrorTracker:
    """Centralized error tracking system"""
    
    def __init__(self, max_events: int = 10000, retention_hours: int = 168):
        self.max_events = max_events
        self.retention_hours = retention_hours
        self.events: Dict[str, ErrorEvent] = {}
        self.service_events: Dict[str, List[str]] = defaultdict(list)
        self.severity_events: Dict[ErrorSeverity, List[str]] = defaultdict(list)
        self.category_events: Dict[ErrorCategory, List[str]] = defaultdict(list)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics cache
        self._stats_cache: Optional[ErrorStats] = None
        self._stats_cache_time: Optional[datetime] = None
        self._stats_cache_ttl = timedelta(seconds=30)
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def track_error(
        self,
        error_type: str,
        error_message: str,
        service: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Track a new error event"""
        with self._lock:
            error_id = str(uuid.uuid4())
            event = ErrorEvent(
                id=error_id,
                timestamp=datetime.utcnow(),
                service=service,
                severity=severity,
                category=category,
                error_type=error_type,
                error_message=error_message,
                stack_trace=stack_trace,
                context=context or {},
                correlation_id=correlation_id,
                request_id=request_id,
                user_id=user_id
            )
            
            self.events[error_id] = event
            self.service_events[service].append(error_id)
            self.severity_events[severity].append(error_id)
            self.category_events[category].append(error_id)
            
            # Maintain max events limit
            if len(self.events) > self.max_events:
                self._cleanup_old_events()
            
            # Invalidate stats cache
            self._stats_cache = None
            self._stats_cache_time = None
            
            return error_id
    
    def track_exception(
        self,
        exception: Exception,
        service: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
        category: Optional[ErrorCategory] = None,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Track an exception"""
        if category is None:
            category = self._categorize_exception(exception)
        
        stack_trace = traceback.format_exc()
        
        return self.track_error(
            error_type=type(exception).__name__,
            error_message=str(exception),
            service=service,
            severity=severity,
            category=category,
            stack_trace=stack_trace,
            context=context,
            correlation_id=correlation_id,
            request_id=request_id,
            user_id=user_id
        )
    
    def resolve_error(
        self,
        error_id: str,
        resolution_notes: Optional[str] = None
    ) -> bool:
        """Mark an error as resolved"""
        with self._lock:
            if error_id not in self.events:
                return False
            
            event = self.events[error_id]
            event.resolved = True
            event.resolution_time = datetime.utcnow()
            event.resolution_notes = resolution_notes
            
            # Invalidate stats cache
            self._stats_cache = None
            self._stats_cache_time = None
            
            return True
    
    def get_error(self, error_id: str) -> Optional[ErrorEvent]:
        """Get a specific error event"""
        with self._lock:
            return self.events.get(error_id)
    
    def get_errors(
        self,
        service: Optional[str] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        resolved: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ErrorEvent]:
        """Get filtered error events"""
        with self._lock:
            events = list(self.events.values())
            
            # Apply filters
            if service:
                events = [e for e in events if e.service == service]
            
            if severity:
                events = [e for e in events if e.severity == severity]
            
            if category:
                events = [e for e in events if e.category == category]
            
            if resolved is not None:
                events = [e for e in events if e.resolved == resolved]
            
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]
            
            if end_time:
                events = [e for e in events if e.timestamp <= end_time]
            
            # Sort by timestamp (newest first)
            events.sort(key=lambda x: x.timestamp, reverse=True)
            
            return events[:limit]
    
    def get_error_stats(self) -> ErrorStats:
        """Get error statistics"""
        with self._lock:
            # Check cache
            if (self._stats_cache and 
                self._stats_cache_time and 
                datetime.utcnow() - self._stats_cache_time < self._stats_cache_ttl):
                return self._stats_cache
            
            # Calculate statistics
            events = list(self.events.values())
            total_errors = len(events)
            
            # Count by severity
            errors_by_severity = defaultdict(int)
            for event in events:
                errors_by_severity[event.severity] += 1
            
            # Count by category
            errors_by_category = defaultdict(int)
            for event in events:
                errors_by_category[event.category] += 1
            
            # Count by service
            errors_by_service = defaultdict(int)
            for event in events:
                errors_by_service[event.service] += 1
            
            # Calculate error rate (errors per minute in last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_errors = [e for e in events if e.timestamp >= one_hour_ago]
            error_rate = len(recent_errors) / 60.0  # errors per minute
            
            # Calculate resolution rate
            resolved_errors = [e for e in events if e.resolved]
            resolution_rate = (len(resolved_errors) / total_errors * 100) if total_errors > 0 else 0
            
            # Calculate average resolution time
            resolution_times = []
            for event in resolved_errors:
                if event.resolution_time:
                    resolution_time = (event.resolution_time - event.timestamp).total_seconds() / 60
                    resolution_times.append(resolution_time)
            
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            stats = ErrorStats(
                total_errors=total_errors,
                errors_by_severity=dict(errors_by_severity),
                errors_by_category=dict(errors_by_category),
                errors_by_service=dict(errors_by_service),
                error_rate=error_rate,
                resolution_rate=resolution_rate,
                avg_resolution_time=avg_resolution_time
            )
            
            # Cache result
            self._stats_cache = stats
            self._stats_cache_time = datetime.utcnow()
            
            return stats
    
    def get_error_trends(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get error trends over time"""
        with self._lock:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Group by hour
            hourly_data = defaultdict(lambda: defaultdict(int))
            
            for event in self.events.values():
                if event.timestamp >= start_time:
                    hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
                    hourly_data[hour_key][event.severity.value] += 1
                    hourly_data[hour_key]["total"] += 1
            
            # Convert to sorted list
            trends = []
            for hour in sorted(hourly_data.keys()):
                trends.append({
                    "hour": hour,
                    **hourly_data[hour]
                })
            
            return {"trends": trends}
    
    def export_errors(self, format: str = "json") -> str:
        """Export errors in specified format"""
        with self._lock:
            events = [self._event_to_dict(event) for event in self.events.values()]
            
            if format.lower() == "json":
                return json.dumps(events, indent=2, default=str)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if events:
                    writer = csv.DictWriter(output, fieldnames=events[0].keys())
                    writer.writeheader()
                    writer.writerows(events)
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def _event_to_dict(self, event: ErrorEvent) -> Dict[str, Any]:
        """Convert error event to dictionary"""
        data = asdict(event)
        data["severity"] = event.severity.value
        data["category"] = event.category.value
        data["timestamp"] = event.timestamp.isoformat()
        if event.resolution_time:
            data["resolution_time"] = event.resolution_time.isoformat()
        return data
    
    def _categorize_exception(self, exception: Exception) -> ErrorCategory:
        """Automatically categorize exceptions"""
        exception_type = type(exception).__name__.lower()
        
        if any(keyword in exception_type for keyword in ["connection", "timeout", "network"]):
            return ErrorCategory.NETWORK
        elif any(keyword in exception_type for keyword in ["auth", "permission", "unauthorized"]):
            return ErrorCategory.AUTHENTICATION
        elif any(keyword in exception_type for keyword in ["validation", "value", "type"]):
            return ErrorCategory.VALIDATION
        elif any(keyword in exception_type for keyword in ["database", "sql", "query"]):
            return ErrorCategory.DATABASE
        elif "api" in exception_type:
            return ErrorCategory.API
        elif "mcp" in exception_type:
            return ErrorCategory.MCP_PROTOCOL
        else:
            return ErrorCategory.UNKNOWN
    
    def _cleanup_old_events(self):
        """Remove old events beyond retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        old_events = [
            error_id for error_id, event in self.events.items()
            if event.timestamp < cutoff_time
        ]
        
        for error_id in old_events:
            event = self.events[error_id]
            
            # Remove from events dict
            del self.events[error_id]
            
            # Remove from service events
            if error_id in self.service_events[event.service]:
                self.service_events[event.service].remove(error_id)
            
            # Remove from severity events
            if error_id in self.severity_events[event.severity]:
                self.severity_events[event.severity].remove(error_id)
            
            # Remove from category events
            if error_id in self.category_events[event.category]:
                self.category_events[event.category].remove(error_id)
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                time.sleep(3600)  # Run every hour
                try:
                    with self._lock:
                        self._cleanup_old_events()
                except Exception:
                    pass  # Ignore cleanup errors
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()


# Global error tracker instance
_error_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    """Get the global error tracker instance"""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker


def track_error(
    error_type: str,
    error_message: str,
    service: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    **kwargs
) -> str:
    """Track an error (convenience function)"""
    return get_error_tracker().track_error(
        error_type=error_type,
        error_message=error_message,
        service=service,
        severity=severity,
        category=category,
        **kwargs
    )


def track_exception(
    exception: Exception,
    service: str,
    severity: ErrorSeverity = ErrorSeverity.HIGH,
    category: Optional[ErrorCategory] = None,
    **kwargs
) -> str:
    """Track an exception (convenience function)"""
    return get_error_tracker().track_exception(
        exception=exception,
        service=service,
        severity=severity,
        category=category,
        **kwargs
    )


def resolve_error(error_id: str, resolution_notes: Optional[str] = None) -> bool:
    """Resolve an error (convenience function)"""
    return get_error_tracker().resolve_error(error_id, resolution_notes)