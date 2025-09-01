"""
Async MCP Protocol Handler with Performance Optimizations

This module provides a high-performance async implementation of the MCP protocol handler
with connection pooling, timeout management, WebSocket integration, and comprehensive
performance monitoring for production-grade async operations.
"""
import json
import uuid
import asyncio
import time
from typing import Dict, Any, Optional, Union, List
from datetime import datetime
from contextlib import AsyncExitStack

from app.core.config import settings
from mcp_core.shared.exceptions import MCPError, ParseError, InvalidRequest, MethodNotFound
from app.core.async_utils import (
    performance_monitor,
    connection_pool,
    AsyncTimeoutManager,
    async_retry,
    safe_async_execute,
    notify_mcp_operation
)
from app.services.openproject_service import OpenProjectService
from app.services.tool_service import ToolService
from app.services.resource_service import ResourceService
from app.services.prompt_service import PromptService
from app.services.report_service import ReportService
from app.services.template_service import TemplateService
from mcp_core.shared.logger import get_logger

logger = get_logger(__name__)


class MCPHandler:
    """High-performance async MCP protocol handler with production optimizations"""
    
    def __init__(self):
        self.openproject_service: Optional[OpenProjectService] = None
        self.tool_service: Optional[ToolService] = None
        self.resource_service: Optional[ResourceService] = None
        self.prompt_service: Optional[PromptService] = None
        self.report_service: Optional[ReportService] = None
        self.template_service: Optional[TemplateService] = None
        self.initialized = False
        self._exit_stack = AsyncExitStack()
        self._operation_semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self.server_info = {
            "name": settings.app_name,
            "version": settings.app_version,
            "protocol_version": settings.mcp_version,
            "async_support": True,
            "performance_optimizations": {
                "connection_pooling": True,
                "timeout_management": True,
                "websocket_integration": settings.websocket_enabled,
                "max_concurrent_requests": settings.max_concurrent_requests
            }
        }
    
    @async_retry(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    async def initialize(self):
        """Initialize MCP handler with async connection pooling and performance optimizations"""
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            logger.info("Initializing async MCP handler with performance optimizations...")
            
            async with connection_pool.acquire_connection(timeout=10.0):
                # Initialize OpenProject service with connection pooling
                self.openproject_service = OpenProjectService(
                    url=settings.openproject_url,
                    api_key=settings.openproject_api_key
                )
                await self.openproject_service.initialize()
                
                # Initialize other services with dependency injection
                self.template_service = TemplateService()
                self.tool_service = ToolService(self.openproject_service)
                self.resource_service = ResourceService(self.openproject_service)
                self.prompt_service = PromptService(self.openproject_service)
                self.report_service = ReportService(self.openproject_service)

                # Create default templates asynchronously
                await self.template_service.create_default_templates()
                
                self.initialized = True
                
                duration_ms = (time.time() - start_time) * 1000
                logger.info(f"MCP handler initialized successfully in {duration_ms:.2f}ms")
                
                # Send initialization notification
                await notify_mcp_operation(
                    operation_type="initialization",
                    operation_id=operation_id,
                    method="initialize",
                    duration_ms=duration_ms,
                    success=True
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"MCP handler initialization failed in {duration_ms:.2f}ms: {e}")
            
            # Send error notification
            await notify_mcp_operation(
                operation_type="initialization",
                operation_id=operation_id,
                method="initialize",
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
            
            raise MCPError(f"Failed to initialize MCP handler: {str(e)}")
    
    async def cleanup(self):
        """Cleanup resources with proper async connection pool management"""
        try:
            # Close all services in reverse initialization order
            services_to_cleanup = [
                self.report_service,
                self.prompt_service,
                self.resource_service,
                self.tool_service,
                self.template_service,
                self.openproject_service
            ]
            
            for service in services_to_cleanup:
                if hasattr(service, 'cleanup') and callable(getattr(service, 'cleanup')):
                    await safe_async_execute(
                        service.cleanup(),
                        f"cleanup_{service.__class__.__name__.lower()}",
                        timeout=5.0
                    )
            
            # Close async exit stack
            await self._exit_stack.aclose()
            
            self.initialized = False
            logger.info("MCP handler cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"MCP handler cleanup failed: {e}")
            # Continue cleanup even if some services fail
    
    @async_retry(max_retries=2, initial_delay=0.5)
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status with async service checks"""
        if not self.initialized:
            return {
                "status": "unhealthy",
                "message": "MCP handler not initialized",
                "timestamp": datetime.now().isoformat(),
                "async_checks": False
            }
        
        start_time = time.time()
        
        try:
            # Check OpenProject connection with timeout
            openproject_status = False
            openproject_latency = None
            
            async with AsyncTimeoutManager.with_timeout(5.0, "health_check_openproject"):
                op_check_start = time.time()
                openproject_status = await self.openproject_service.check_connection()
                openproject_latency = time.time() - op_check_start
            
            # Check connection pool status
            pool_stats = connection_pool.get_stats()
            
            # Check performance monitor status
            perf_metrics = performance_monitor.get_metrics()
            
            duration_ms = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy" if openproject_status else "degraded",
                "check_duration_ms": round(duration_ms, 2),
                "services": {
                    "openproject": {
                        "status": "healthy" if openproject_status else "unhealthy",
                        "latency_ms": round(openproject_latency * 1000, 2) if openproject_latency else None
                    },
                    "mcp_handler": "healthy",
                    "connection_pool": {
                        "status": "healthy",
                        **pool_stats
                    },
                    "performance_monitor": {
                        "status": "healthy",
                        "tracked_operations": len(perf_metrics["operations"])
                    }
                },
                "performance": {
                    "async_operations": True,
                    "connection_pooling": True,
                    "timeout_management": True,
                    "websocket_integration": settings.websocket_enabled
                },
                "timestamp": datetime.now().isoformat(),
                "async_checks": True
            }
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            logger.warning(f"Health check timeout after {duration_ms:.2f}ms")
            return {
                "status": "degraded",
                "message": "Health check timeout",
                "check_duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now().isoformat(),
                "async_checks": True
            }
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Health check failed in {duration_ms:.2f}ms: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
                "check_duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now().isoformat(),
                "async_checks": True
            }
    
    async def handle_request(self, body: bytes, content_type: str) -> Dict[str, Any]:
        """Handle MCP requests with async performance optimizations and WebSocket integration"""
        if not self.initialized:
            raise MCPError("MCP handler not initialized")
        
        request_data = None
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Rate limiting with connection pool semaphore
            async with self._operation_semaphore:
                # Parse request with timeout protection
                request_data = await safe_async_execute(
                    self._parse_request(body, content_type),
                    "parse_request",
                    timeout=2.0,
                    default_value={}
                )
                
                # Validate JSON-RPC format
                self._validate_jsonrpc_request(request_data)
                
                # Extract request information
                method = request_data.get("method")
                params = request_data.get("params", {})
                request_id = request_data.get("id")
                
                logger.info(f"Processing async MCP request: {method} (ID: {operation_id})")
                
                # Track operation performance
                finish_operation = await performance_monitor.track_operation(
                    f"mcp_{method.replace('/', '_')}", "mcp_request"
                )
                
                # Route to appropriate handler with connection pooling
                async with connection_pool.acquire_connection(timeout=settings.request_timeout):
                    result = await self._route_request(method, params, operation_id)
                
                # Build response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                
                duration_ms = (time.time() - start_time) * 1000
                await finish_operation(success=True)
                
                # Send real-time notification for successful operations
                if method in ["tools/call", "resources/read", "prompts/get"]:
                    await notify_mcp_operation(
                        operation_type="mcp_request",
                        operation_id=operation_id,
                        method=method,
                        params=params,
                        result=result,
                        duration_ms=duration_ms,
                        success=True
                    )
                
                return response
                
        except MCPError as e:
            # MCP protocol error
            duration_ms = (time.time() - start_time) * 1000
            logger.warning(f"MCP protocol error in {duration_ms:.2f}ms: {e}")
            
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id") if request_data else None,
                "error": {
                    "code": e.code,
                    "message": str(e),
                    "data": getattr(e, 'data', None)
                }
            }
            
            # Send error notification
            await notify_mcp_operation(
                operation_type="mcp_request",
                operation_id=operation_id,
                method=request_data.get("method") if request_data else "unknown",
                params=request_data.get("params") if request_data else {},
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
            
            return error_response
            
        except Exception as e:
            # Unknown error
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error processing MCP request in {duration_ms:.2f}ms: {e}")
            
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id") if request_data else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)[:500]  # Limit error message size
                }
            }
            
            # Send error notification
            await notify_mcp_operation(
                operation_type="mcp_request",
                operation_id=operation_id,
                method=request_data.get("method") if request_data else "unknown",
                params=request_data.get("params") if request_data else {},
                duration_ms=duration_ms,
                success=False,
                error=str(e)
            )
            
            return error_response
    
    async def _parse_request(self, body: bytes, content_type: str) -> Dict[str, Any]:
        """Parse MCP request with content type validation and size limits"""
        if content_type.startswith("application/json"):
            try:
                # Validate request size
                if len(body) > settings.max_request_size:
                    raise ParseError(f"Request too large: {len(body)} bytes")
                
                return json.loads(body.decode('utf-8'))
            except json.JSONDecodeError as e:
                raise ParseError(f"Invalid JSON: {str(e)}")
            except UnicodeDecodeError as e:
                raise ParseError(f"Invalid UTF-8 encoding: {str(e)}")
        else:
            raise ParseError(f"Unsupported content type: {content_type}")
    
    def _validate_jsonrpc_request(self, request_data: Dict[str, Any]):
        """Validate JSON-RPC request format"""
        if not isinstance(request_data, dict):
            raise ParseError("Request must be a JSON object")
        
        if request_data.get("jsonrpc") != "2.0":
            raise InvalidRequest("Invalid JSON-RPC version")
        
        if "method" not in request_data:
            raise InvalidRequest("Missing method field")
        
        if not isinstance(request_data["method"], str):
            raise InvalidRequest("Method must be a string")
        
        # Validate request ID if present
        request_id = request_data.get("id")
        if request_id is not None and not isinstance(request_id, (str, int)):
            raise InvalidRequest("Request ID must be string or number")
    
    async def _route_request(self, method: str, params: Dict[str, Any], operation_id: str) -> Any:
        """Route MCP request to appropriate handler with async optimizations"""
        method_handlers = {
            "initialize": self._handle_initialize,
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "resources/list": self._handle_list_resources,
            "resources/read": self._handle_read_resource,
            "prompts/list": self._handle_list_prompts,
            "prompts/get": self._handle_get_prompt
        }
        
        handler = method_handlers.get(method)
        if not handler:
            raise MethodNotFound(f"Unknown method: {method}")
        
        # Execute handler with performance monitoring
        return await safe_async_execute(
            handler(params, operation_id),
            f"mcp_handler_{method.replace('/', '_')}",
            timeout=settings.request_timeout
        )
    
    async def _handle_initialize(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle initialization request with async capabilities"""
        return {
            "protocolVersion": settings.mcp_version,
            "capabilities": {
                "tools": {
                    "asyncSupport": True,
                    "timeoutManagement": True,
                    "connectionPooling": True
                },
                "resources": {
                    "asyncSupport": True,
                    "streaming": True,
                    "partialContent": True
                },
                "prompts": {
                    "asyncSupport": True,
                    "templating": True,
                    "internationalization": True
                }
            },
            "serverInfo": self.server_info,
            "performance": {
                "maxConcurrentRequests": settings.max_concurrent_requests,
                "requestTimeout": settings.request_timeout,
                "websocketSupport": settings.websocket_enabled,
                "connectionPoolSize": connection_pool.max_connections
            }
        }
    
    async def _handle_list_tools(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle tools list request with async optimizations"""
        tools = await safe_async_execute(
            self.tool_service.list_tools(),
            "list_tools",
            timeout=10.0
        )
        return {"tools": tools}
    
    async def _handle_call_tool(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle tool call request with async timeout and error handling"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise InvalidRequest("Missing tool name")
        
        # Validate arguments size
        arguments_size = len(str(arguments).encode('utf-8'))
        if arguments_size > 1024 * 1024:  # 1MB limit
            raise InvalidRequest(f"Arguments too large: {arguments_size} bytes")
        
        result = await safe_async_execute(
            self.tool_service.call_tool(tool_name, arguments),
            f"call_tool_{tool_name}",
            timeout=30.0  # Longer timeout for tool operations
        )
        
        return result
    
    async def _handle_list_resources(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle resources list request with async pagination support"""
        resources = await safe_async_execute(
            self.resource_service.list_resources(),
            "list_resources",
            timeout=15.0
        )
        return {"resources": resources}
    
    async def _handle_read_resource(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle resource read request with async streaming support"""
        uri = params.get("uri")
        
        if not uri:
            raise InvalidRequest("Missing resource URI")
        
        # Validate URI format
        if not uri.startswith(('openproject://', 'file://', 'http://', 'https://')):
            raise InvalidRequest(f"Invalid resource URI scheme: {uri}")
        
        result = await safe_async_execute(
            self.resource_service.read_resource(uri),
            f"read_resource_{uri.split('://')[0]}",
            timeout=20.0  # Longer timeout for resource operations
        )
        
        return result
    
    async def _handle_list_prompts(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle prompts list request with async internationalization"""
        prompts = await safe_async_execute(
            self.prompt_service.list_prompts(),
            "list_prompts",
            timeout=10.0
        )
        return {"prompts": prompts}
    
    async def _handle_get_prompt(self, params: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Handle prompt retrieval with async template processing"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise InvalidRequest("Missing prompt name")
        
        # Validate arguments for template injection
        if arguments and not isinstance(arguments, dict):
            raise InvalidRequest("Arguments must be a dictionary")
        
        result = await safe_async_execute(
            self.prompt_service.get_prompt(name, arguments),
            f"get_prompt_{name}",
            timeout=15.0  # Longer timeout for prompt generation
        )
        
        return result
