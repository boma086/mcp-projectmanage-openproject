"""
Error Tracking Integration for HTTP Solution

This module integrates error tracking with the HTTP solution.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

from ...monitoring.error_tracking import (
    get_error_tracker,
    ErrorSeverity,
    ErrorCategory,
    track_error,
    track_exception
)

logger = logging.getLogger(__name__)


class ErrorTrackingMiddleware:
    """Middleware for automatic error tracking"""
    
    def __init__(self, app):
        self.app = app
        self.error_tracker = get_error_tracker()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Track HTTP errors
                status_code = message["status"]
                if status_code >= 400:
                    await self._track_http_error(request, status_code)
            
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Track unhandled exceptions
            await self._track_unhandled_exception(request, e)
            raise
    
    async def _track_http_error(self, request: Request, status_code: int):
        """Track HTTP error responses"""
        try:
            # Determine severity based on status code
            if status_code >= 500:
                severity = ErrorSeverity.HIGH
                category = ErrorCategory.SYSTEM
            elif status_code >= 400:
                severity = ErrorSeverity.MEDIUM
                category = ErrorCategory.VALIDATION
            else:
                return  # Don't track successful responses
            
            # Extract context
            context = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None
            }
            
            # Track error
            track_error(
                error_type=f"HTTP_{status_code}",
                error_message=f"HTTP {status_code} error",
                service="http-solution",
                severity=severity,
                category=category,
                context=context,
                correlation_id=request.headers.get("X-Correlation-ID"),
                request_id=request.headers.get("X-Request-ID")
            )
            
        except Exception as e:
            logger.error(f"Failed to track HTTP error: {e}")
    
    async def _track_unhandled_exception(self, request: Request, exception: Exception):
        """Track unhandled exceptions"""
        try:
            context = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client": request.client.host if request.client else None
            }
            
            track_exception(
                exception=exception,
                service="http-solution",
                severity=ErrorSeverity.CRITICAL,
                context=context,
                correlation_id=request.headers.get("X-Correlation-ID"),
                request_id=request.headers.get("X-Request-ID")
            )
            
        except Exception as e:
            logger.error(f"Failed to track unhandled exception: {e}")


def get_errors(request: Request) -> JSONResponse:
    """Get filtered errors"""
    try:
        error_tracker = get_error_tracker()
        
        # Parse query parameters
        service = request.query_params.get("service")
        severity = request.query_params.get("severity")
        category = request.query_params.get("category")
        resolved = request.query_params.get("resolved")
        limit = int(request.query_params.get("limit", "100"))
        
        # Parse boolean
        if resolved is not None:
            resolved = resolved.lower() == "true"
        
        # Parse enums
        severity_enum = None
        if severity:
            try:
                severity_enum = ErrorSeverity(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        category_enum = None
        if category:
            try:
                category_enum = ErrorCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")
        
        # Get errors
        errors = error_tracker.get_errors(
            service=service,
            severity=severity_enum,
            category=category_enum,
            resolved=resolved,
            limit=limit
        )
        
        # Convert to dict
        error_data = []
        for error in errors:
            error_dict = {
                "id": error.id,
                "timestamp": error.timestamp.isoformat(),
                "service": error.service,
                "severity": error.severity.value,
                "category": error.category.value,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "resolved": error.resolved,
                "context": error.context
            }
            
            if error.stack_trace:
                error_dict["stack_trace"] = error.stack_trace
            
            if error.correlation_id:
                error_dict["correlation_id"] = error.correlation_id
            
            if error.request_id:
                error_dict["request_id"] = error.request_id
            
            if error.user_id:
                error_dict["user_id"] = error.user_id
            
            if error.resolution_time:
                error_dict["resolution_time"] = error.resolution_time.isoformat()
            
            if error.resolution_notes:
                error_dict["resolution_notes"] = error.resolution_notes
            
            error_data.append(error_dict)
        
        return JSONResponse(content={"errors": error_data, "total": len(error_data)})
        
    except Exception as e:
        logger.error(f"Error getting errors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_error_stats(request: Request) -> JSONResponse:
    """Get error statistics"""
    try:
        error_tracker = get_error_tracker()
        stats = error_tracker.get_error_stats()
        
        stats_data = {
            "total_errors": stats.total_errors,
            "error_rate": stats.error_rate,
            "resolution_rate": stats.resolution_rate,
            "avg_resolution_time": stats.avg_resolution_time,
            "errors_by_severity": {k.value: v for k, v in stats.errors_by_severity.items()},
            "errors_by_category": {k.value: v for k, v in stats.errors_by_category.items()},
            "errors_by_service": stats.errors_by_service
        }
        
        return JSONResponse(content=stats_data)
        
    except Exception as e:
        logger.error(f"Error getting error stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_error_trends(request: Request) -> JSONResponse:
    """Get error trends"""
    try:
        error_tracker = get_error_tracker()
        hours = int(request.query_params.get("hours", "24"))
        trends = error_tracker.get_error_trends(hours=hours)
        
        return JSONResponse(content=trends)
        
    except Exception as e:
        logger.error(f"Error getting error trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def resolve_error(request: Request) -> JSONResponse:
    """Resolve an error"""
    try:
        error_tracker = get_error_tracker()
        data = await request.json()
        error_id = data.get("error_id")
        resolution_notes = data.get("resolution_notes")
        
        if not error_id:
            raise HTTPException(status_code=400, detail="error_id is required")
        
        success = error_tracker.resolve_error(error_id, resolution_notes)
        
        if success:
            return JSONResponse(content={"message": "Error resolved successfully"})
        else:
            raise HTTPException(status_code=404, detail="Error not found")
        
    except Exception as e:
        logger.error(f"Error resolving error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def export_errors(request: Request) -> JSONResponse:
    """Export errors"""
    try:
        error_tracker = get_error_tracker()
        format_type = request.query_params.get("format", "json")
        
        if format_type not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        exported_data = error_tracker.export_errors(format=format_type)
        
        if format_type == "json":
            return JSONResponse(content={"data": exported_data})
        else:
            from fastapi.responses import Response
            return Response(
                content=exported_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=errors.csv"}
            )
        
    except Exception as e:
        logger.error(f"Error exporting errors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")