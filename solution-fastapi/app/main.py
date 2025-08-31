
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
openproject_client: Optional[AsyncOpenProjectClient] = None
mcp_handler: Optional[MCPHandler] = None
httpx_client: Optional[httpx.AsyncClient] = None

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket client {client_id} connected")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send broadcast message: {e}")

connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management with async resource initialization"""
    global openproject_client, mcp_handler, httpx_client
    
    # Startup initialization
    try:
        logger.info("Initializing FastAPI MCP Server with async optimizations...")
        
        # Create HTTP client with connection pooling for external calls
        httpx_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=50,
                max_connections=100,
                keepalive_expiry=30
            ),
            timeout=httpx.Timeout(30.0, connect=10.0)
        )
        
        # Create async OpenProject client with connection pooling
        openproject_client = AsyncOpenProjectClient()
        await openproject_client.initialize()
        
        # Create MCP handler with async support
        mcp_handler = MCPHandler(openproject_client)
        
        # Perform health check to ensure all services are ready
        connection_ok = await openproject_client.check_connection()
        if not connection_ok:
            logger.warning("OpenProject connection check failed during startup")
        
        logger.info("FastAPI MCP Server initialized successfully")
        logger.info(f"Server running with {settings.app_name} v{settings.app_version}")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    finally:
        # Cleanup on shutdown
        logger.info("Shutting down FastAPI MCP Server...")
        
        # Close HTTP client
        if httpx_client:
            await httpx_client.aclose()
        
        # Cleanup OpenProject client
        if openproject_client:
            await openproject_client.cleanup()
        
        logger.info("Application shutdown complete")


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
    expose_headers=["X-Process-Time", "X-Request-ID"]
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


@app.get("/")
async def root(settings: Settings = Depends(get_app_settings)):
    """Root endpoint - returns async service information"""
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
            "performance_monitoring": True
        },
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
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
        
        # Check HTTP client
        http_client_status = "ready" if httpx_client and not httpx_client.is_closed else "not_ready"
        
        # Calculate total health check time
        total_time = time.time() - start_time
        
        health_data = {
            "status": "healthy" if openproject_status == "connected" else "degraded",
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
            "performance": {
                "async_support": True,
                "connection_pooling": True
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
        
        # Broadcast update to WebSocket clients if applicable
        if request_data.get("method") in ["tools/call", "resources/read"]:
            await connection_manager.broadcast(
                f"MCP operation completed: {request_data.get('method')}"
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


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates and notifications"""
    await connection_manager.connect(websocket, client_id)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection",
            "message": f"Connected to MCP server as {client_id}",
            "timestamp": time.time()
        })
        
        while True:
            try:
                # Wait for messages from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                
                # Echo back or process the message
                await websocket.send_json({
                    "type": "echo",
                    "message": f"Received: {data}",
                    "timestamp": time.time()
                })
                
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({
                    "type": "ping",
                    "timestamp": time.time()
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        connection_manager.disconnect(client_id)

# Performance monitoring endpoint
@app.get("/metrics")
async def get_metrics():
    """Get performance metrics for monitoring"""
    return {
        "websocket_connections": len(connection_manager.active_connections),
        "http_client_status": "ready" if httpx_client and not httpx_client.is_closed else "not_ready",
        "openproject_status": "ready" if openproject_client else "not_ready",
        "mcp_handler_status": "ready" if mcp_handler else "not_ready",
        "server_info": {
            "name": settings.app_name,
            "version": settings.app_version,
            "debug": settings.debug
        }
    }

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
    logger.info(f"  - MCP endpoint: http://{settings.host}:{settings.port}/mcp")
    logger.info(f"  - Metrics: http://{settings.host}:{settings.port}/metrics")
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
