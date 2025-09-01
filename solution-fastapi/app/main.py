"""
Async FastAPI MCP Server with Full Async Support

This module implements a high-performance async FastAPI application with:
- Full async/await patterns throughout
- Connection pooling and async database access
- Async middleware for request/response processing
- WebSocket support for real-time updates
- Performance optimizations for high concurrency
"""
import os
import time
import asyncio
import json
import uuid
import hashlib
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
import httpx
from app.adapters.async_openproject_adapter import AsyncOpenProjectClient
from app.core.config import get_settings, Settings
from app.core.connection_pool import initialize_connection_pools, close_connection_pools, get_connection_pool_manager
from app.middleware.performance import add_performance_middleware, AsyncPerformanceMiddleware
from dotenv import load_dotenv

# 导入核心库
from mcp_core import (
    MCPHandler, get_logger, Config, set_global_config,
    MCPError
)

# Load environment variables first
load_dotenv()

# Initialize settings
settings = get_settings()

# Initialize core library configuration
logger = get_logger("mcp.fastapi")
try:
    config = Config()
    set_global_config(config)
    logger.info("Core library configuration initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize core library configuration: {e}")
    raise MCPError(f"Failed to initialize core config: {e}")

# Global service instances with proper typing
mcp_handler: Optional[MCPHandler] = None

# Import WebSocket modules
from app.websockets.manager import connection_manager
from app.websockets.notifications import notification_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management with async resource initialization"""
    global mcp_handler
    
    # Import dependencies here to avoid circular imports
    from app.dependencies import get_openproject_client, close_http_client_pool
    
    # Startup initialization
    try:
        logger.info("Initializing FastAPI MCP Server with async optimizations...")
        
        # Initialize connection pools first
        await initialize_connection_pools()
        logger.info("Connection pools initialized successfully")
        
        # Initialize OpenProject client using dependency injection
        from app.dependencies import get_http_client_pool
        http_client = get_http_client_pool()
        openproject_client = await get_openproject_client(settings, http_client)
        
        # Create MCP handler with async support
        mcp_handler = MCPHandler(openproject_client)
        
        # Start WebSocket connection manager
        if settings.websocket_enabled:
            await connection_manager.start()
            logger.info("WebSocket connection manager started")
        
        # Perform health check to ensure all services are ready
        connection_ok = await openproject_client.check_connection()
        if not connection_ok:
            logger.warning("OpenProject connection check failed during startup")
        
        # Check connection pool health
        pool_manager = get_connection_pool_manager()
        pool_health = await pool_manager.health_check_all()
        for pool_type, is_healthy in pool_health.items():
            status = "healthy" if is_healthy else "unhealthy"
            logger.info(f"Connection pool {pool_type.value}: {status}")
        
        logger.info("FastAPI MCP Server initialized successfully")
        logger.info(f"Server running with {settings.app_name} v{settings.app_version}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down FastAPI MCP Server...")
        
        # Stop WebSocket connection manager
        if settings.websocket_enabled:
            await connection_manager.stop()
            logger.info("WebSocket connection manager stopped")
        
        # Close connection pools and cleanup resources
        await close_connection_pools()
        logger.info("Connection pools closed")
        
        # Close HTTP client pool
        await close_http_client_pool()
        
        logger.info("Application shutdown complete")


# Async middleware for request timing and logging
class AsyncRequestTimingMiddleware(BaseHTTPMiddleware):
    """Async middleware for request timing and performance monitoring"""
    
    async def dispatch(self, request: StarletteRequest, call_next):
        start_time = time.time()
        
        # Add request ID for tracing
        request_id = f"{int(start_time * 1000000)}"
        
        try:
            response: Response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # Log slow requests
            if process_time > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request detected - {request.method} {request.url.path} - "
                    f"{process_time:.3f}s - Request ID: {request_id}"
                )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed - {request.method} {request.url.path} - "
                f"{process_time:.3f}s - Request ID: {request_id} - Error: {e}"
            )
            raise


# Create FastAPI application with async optimizations
app = FastAPI(
    title=settings.app_name,
    description="High-performance async FastAPI MCP OpenProject server with WebSocket support",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None
)

# Add comprehensive performance middleware
add_performance_middleware(app, settings)

# Add security middleware
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
    )

# Add timing middleware
app.add_middleware(AsyncRequestTimingMiddleware)

# Add CORS middleware with settings-based configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time", "X-Request-ID", "X-RateLimit-Limit", 
                   "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Mount static files (from shared web directory)
if os.path.exists("../shared-web"):
    app.mount("/web", StaticFiles(directory="../shared-web"), name="web")

# Dependency for getting async HTTP client
async def get_http_client() -> httpx.AsyncClient:
    """Dependency to get the shared async HTTP client"""
    if not httpx_client:
        raise HTTPException(status_code=503, detail="HTTP client not initialized")
    return httpx_client

# Dependency for getting settings
def get_app_settings() -> Settings:
    """Dependency to get application settings"""
    return settings

# Dependency for getting connection pool manager
async def get_connection_pool_manager_dep():
    """Dependency to get connection pool manager"""
    return get_connection_pool_manager()


@app.get("/")
async def root(settings: Settings = Depends(get_app_settings)):
    """Root endpoint - returns async service information"""
    pool_manager = get_connection_pool_manager()
    pool_stats = pool_manager.get_all_stats()
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "framework": "FastAPI",
        "async_support": True,
        "status": "running",
        "features": {
            "websockets": True,
            "connection_pooling": True,
            "async_middleware": True,
            "performance_monitoring": True,
            "rate_limiting": settings.rate_limit_enabled,
            "caching": settings.cache_enabled
        },
        "connection_pools": {
            pool_type.value: {
                "total_connections": stats.total_connections,
                "active_connections": stats.active_connections,
                "max_connections": stats.max_connections
            } for pool_type, stats in pool_stats.items()
        },
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
            "performance": "/performance",
            "websocket": "/ws/{client_id}",
            "docs": "/docs" if settings.debug else "disabled",
            "openapi": "/openapi.json" if settings.debug else "disabled"
        }
    }


@app.get("/health")
async def health_check():
    """Comprehensive async health check endpoint"""
    start_time = time.time()
    
    try:
        # Check OpenProject connection with timeout
        openproject_status = "disconnected"
        openproject_latency = None
        
        if openproject_client:
            op_start = time.time()
            try:
                connection_ok = await asyncio.wait_for(
                    openproject_client.check_connection(),
                    timeout=5.0
                )
                openproject_latency = time.time() - op_start
                openproject_status = "connected" if connection_ok else "disconnected"
            except asyncio.TimeoutError:
                openproject_status = "timeout"
                openproject_latency = 5.0
            except Exception as e:
                openproject_status = f"error: {str(e)[:100]}"
        
        # Check HTTP client status (now managed by dependency injection)
        http_client_status = "managed_by_di"
        
        # Check connection pool health
        pool_manager = get_connection_pool_manager()
        pool_health = await pool_manager.health_check_all()
        pool_statuses = {}
        for pool_type, is_healthy in pool_health.items():
            pool_statuses[pool_type.value] = "healthy" if is_healthy else "unhealthy"
        
        # Calculate total health check time
        total_time = time.time() - start_time
        
        health_data = {
            "status": "healthy" if (openproject_status == "connected" and 
                                  all(status == "healthy" for status in pool_statuses.values())) else "degraded",
            "timestamp": time.time(),
            "check_duration_ms": round(total_time * 1000, 2),
            "services": {
                "openproject": {
                    "status": openproject_status,
                    "latency_ms": round(openproject_latency * 1000, 2) if openproject_latency else None
                },
                "mcp_handler": "ready" if mcp_handler else "not_ready",
                "http_client": http_client_status,
                "websocket_connections": len(connection_manager.active_connections)
            },
            "connection_pools": pool_statuses,
            "performance": {
                "async_support": True,
                "connection_pooling": True,
                "caching": settings.cache_enabled,
                "rate_limiting": settings.rate_limit_enabled
            }
        }
        
        # Return appropriate HTTP status
        status_code = 200 if health_data["status"] == "healthy" else 503
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        logger.error("Health check failed", exc_info=True)
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            },
            status_code=500
        )


@app.get("/performance")
async def performance_stats():
    """Get comprehensive performance statistics"""
    pool_manager = get_connection_pool_manager()
    pool_stats = pool_manager.get_all_stats()
    
    websocket_stats = connection_manager.get_connection_stats()
    
    return {
        "connection_pools": {
            pool_type.value: {
                "total_connections": stats.total_connections,
                "active_connections": stats.active_connections,
                "idle_connections": stats.idle_connections,
                "max_connections": stats.max_connections,
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "avg_response_time_ms": stats.avg_response_time_ms,
                "p95_response_time_ms": stats.p95_response_time_ms,
                "p99_response_time_ms": stats.p99_response_time_ms
            } for pool_type, stats in pool_stats.items()
        },
        "websocket": {
            **websocket_stats,
            "enabled": settings.websocket_enabled,
            "max_connections": settings.max_websocket_connections,
            "heartbeat_interval": settings.websocket_heartbeat_interval
        },
        "http_client": {
            "status": "managed_by_di",
            "max_connections": settings.http_client_max_connections,
            "timeout": settings.http_client_timeout
        },
        "services": {
            "openproject": "ready" if mcp_handler else "not_ready",
            "mcp_handler": "ready" if mcp_handler else "not_ready",
            "websocket_manager": "running" if settings.websocket_enabled else "disabled"
        },
        "server_info": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug,
            "environment": settings.environment
        },
        "performance_limits": {
            "max_concurrent_requests": settings.max_concurrent_requests,
            "request_timeout": settings.request_timeout,
            "max_request_size": settings.max_request_size,
            "rate_limit_requests": settings.rate_limit_requests,
            "rate_limit_window": settings.rate_limit_window
        }
    }


@app.post("/mcp")
async def handle_mcp_request(
    request: Request,
    settings: Settings = Depends(get_app_settings)
):
    """Handle MCP requests with async processing and proper error handling"""
    request_data = None
    
    try:
        # Ensure service is initialized
        if not mcp_handler:
            raise HTTPException(status_code=503, detail="MCP service not initialized")
        
        # Read request body with size limit
        try:
            request_data = await asyncio.wait_for(
                request.json(),
                timeout=settings.request_timeout
            )
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="Request timeout")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
        
        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.max_request_size:
            raise HTTPException(status_code=413, detail="Request too large")
        
        # Process MCP request asynchronously
        response = await asyncio.wait_for(
            mcp_handler.handle_request(request_data),
            timeout=settings.request_timeout
        )
        
        # Send real-time notification for MCP operations
        if request_data.get("method") in ["tools/call", "resources/read"]:
            operation_id = request_data.get("id", str(uuid.uuid4()))
            await notification_service.notify_mcp_operation(
                operation_type="mcp_request",
                operation_id=operation_id,
                method=request_data.get("method"),
                params=request_data.get("params"),
                result=response if isinstance(response, dict) else None,
                duration_ms=(time.time() - start_time) * 1000
            )
        
        return JSONResponse(content=response)
        
    except asyncio.TimeoutError:
        logger.error("MCP request timeout")
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if request_data else None,
            "error": {
                "code": -32603,
                "message": "Request timeout",
                "data": "The request took too long to process"
            }
        }
        return JSONResponse(content=error_response, status_code=408)
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"MCP request processing failed: {e}", exc_info=True)
        
        # Return JSON-RPC error response
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if request_data else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)[:500]  # Limit error message size
            }
        }
        return JSONResponse(content=error_response, status_code=500)


# WebSocket endpoint for real-time updates and notifications
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time MCP operations, notifications, and live data streaming.
    Supports subscription-based messaging and connection lifecycle management.
    """
    try:
        # Connect and initialize client
        actual_client_id = await connection_manager.connect(websocket, client_id)
        
        # Notify about new connection
        await notification_service.notify_connection_status(
            actual_client_id, 
            "connected",
            {"connection_count": len(connection_manager.active_connections)}
        )
        
        # Main message processing loop
        while True:
            try:
                # Wait for messages from client with timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_text(), 
                    timeout=settings.websocket_heartbeat_interval
                )
                
                # Process client message
                await _process_websocket_message(data, actual_client_id)
                
            except asyncio.TimeoutError:
                # Connection is alive, continue waiting
                continue
                
    except WebSocketDisconnect:
        # Handle graceful disconnect
        connection_manager.disconnect(actual_client_id)
        await notification_service.notify_connection_status(
            actual_client_id, 
            "disconnected",
            {"reason": "client_disconnect"}
        )
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"WebSocket error for client {actual_client_id}: {e}")
        connection_manager.disconnect(actual_client_id)
        await notification_service.notify_connection_status(
            actual_client_id, 
            "disconnected", 
            {"reason": "error", "error": str(e)}
        )


async def _process_websocket_message(data: str, client_id: str):
    """Process incoming WebSocket messages from clients"""
    try:
        message = json.loads(data)
        message_type = message.get("type")
        
        if message_type == "subscribe":
            # Handle subscription requests
            subscription_type = message.get("subscription")
            if subscription_type:
                await connection_manager.subscribe(client_id, subscription_type)
                
        elif message_type == "unsubscribe":
            # Handle unsubscription requests
            subscription_type = message.get("subscription")
            if subscription_type:
                await connection_manager.unsubscribe(client_id, subscription_type)
                
        elif message_type == "ping":
            # Respond to ping requests
            await connection_manager.send_personal_message({
                "type": "pong",
                "timestamp": time.time(),
                "client_id": client_id
            }, client_id)
            
        elif message_type == "get_metrics":
            # Provide connection metrics to client
            metrics = connection_manager.get_connection_metrics(client_id)
            await connection_manager.send_personal_message({
                "type": "metrics",
                "client_metrics": metrics,
                "timestamp": time.time()
            }, client_id)
            
        else:
            # Echo unknown message types
            await connection_manager.send_personal_message({
                "type": "echo",
                "message": f"Received: {data}",
                "timestamp": time.time()
            }, client_id)
            
    except json.JSONDecodeError:
        # Handle invalid JSON
        await connection_manager.send_personal_message({
            "type": "error",
            "message": "Invalid JSON message",
            "timestamp": time.time()
        }, client_id)
        
    except Exception as e:
        # Handle processing errors
        logger.error(f"Failed to process WebSocket message from {client_id}: {e}")
        await connection_manager.send_personal_message({
            "type": "error",
            "message": f"Message processing failed: {str(e)}",
            "timestamp": time.time()
        }, client_id)


# Exception handlers with async support
@app.exception_handler(MCPError)
async def mcp_error_handler(request: Request, exc: MCPError):
    """Async MCP error handler"""
    logger.error(f"MCP Error: {exc.message} (code: {exc.code})")
    
    return JSONResponse(
        status_code=400,
        content={
            "jsonrpc": "2.0",
            "error": {
                "code": exc.code,
                "message": exc.message,
                "data": exc.data
            }
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Async HTTP exception handler with enhanced logging"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail} - {request.method} {request.url}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Async general exception handler"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": type(exc).__name__
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Server configuration:")
    logger.info(f"  - Host: {settings.host}:{settings.port}")
    logger.info(f"  - Debug mode: {settings.debug}")
    logger.info(f"  - Request timeout: {settings.request_timeout}s")
    logger.info(f"  - Max request size: {settings.max_request_size} bytes")
    logger.info(f"")
    logger.info(f"Available endpoints:")
    logger.info(f"  - API docs: http://{settings.host}:{settings.port}/docs")
    logger.info(f"  - Health check: http://{settings.host}:{settings.port}/health")
    logger.info(f"  - Performance stats: http://{settings.host}:{settings.port}/performance")
    logger.info(f"  - MCP endpoint: http://{settings.host}:{settings.port}/mcp")
    logger.info(f"  - WebSocket: ws://{settings.host}:{settings.port}/ws/{{client_id}}")
    if os.path.exists("../shared-web"):
        logger.info(f"  - Web interface: http://{settings.host}:{settings.port}/web/template_editor.html")
    
    # Configure uvicorn for optimal async performance
    uvicorn_config = {
        "app": "app.main:app",
        "host": settings.host,
        "port": settings.port,
        "log_level": settings.log_level.lower(),
        "reload": settings.debug,
        "workers": 1,  # Single worker for development, adjust for production
        "loop": "uvloop" if not settings.debug else "asyncio",  # Use uvloop for better performance
        "http": "httptools" if not settings.debug else "h11",  # Use httptools for better performance
        "ws": "websockets",  # WebSocket implementation
        "lifespan": "on",  # Enable lifespan events
        "access_log": settings.debug,
        "use_colors": True
    }
    
    logger.info("Starting async ASGI server with performance optimizations...")
    uvicorn.run(**uvicorn_config)
