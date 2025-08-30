"""
Base MCP Protocol Handler

Implements core Model Context Protocol functionality for standardized protocol
compliance across all solution architectures.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import inspect

from mcp_core.shared.exceptions import (
    MCPError, ParseError, InvalidRequest, MethodNotFound, InvalidParams, InternalError
)
from mcp_core.shared.utils import (
    validate_json_rpc_request, create_json_rpc_response, create_json_rpc_error,
    generate_request_id
)
from mcp_core.shared.logger import get_logger


class MCPProtocolVersion(str, Enum):
    """MCP Protocol Version Constants"""
    V_2024_11_05 = "2024-11-05"
    CURRENT = V_2024_11_05


@dataclass
class MCPServerInfo:
    """MCP Server Information"""
    name: str
    version: str
    description: Optional[str] = None
    homepage: Optional[str] = None


@dataclass 
class MCPCapabilities:
    """MCP Server Capabilities"""
    tools: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[str, Any] = field(default_factory=dict)
    prompts: Dict[str, Any] = field(default_factory=dict)
    logging: Dict[str, Any] = field(default_factory=dict)
    experimental: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPRequest:
    """MCP Request Data Structure"""
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    id: Optional[Union[str, int]] = None
    jsonrpc: str = "2.0"


@dataclass
class MCPResponse:
    """MCP Response Data Structure"""
    result: Any = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    jsonrpc: str = "2.0"


@dataclass
class MCPNotification:
    """MCP Notification Data Structure"""
    method: str
    params: Dict[str, Any] = field(default_factory=dict)
    jsonrpc: str = "2.0"


class BaseMCPHandler(ABC):
    """
    Base MCP Protocol Handler
    
    Provides standardized MCP protocol compliance with extensible hooks
    for custom implementations. Implements core protocol methods and
    routing with proper error handling and logging.
    """
    
    def __init__(self, 
                 server_info: MCPServerInfo,
                 capabilities: Optional[MCPCapabilities] = None,
                 protocol_version: MCPProtocolVersion = MCPProtocolVersion.CURRENT):
        """
        Initialize the MCP protocol handler
        
        Args:
            server_info: Server identification information
            capabilities: Server capabilities (defaults to empty capabilities)
            protocol_version: MCP protocol version to use
        """
        self.server_info = server_info
        self.capabilities = capabilities or MCPCapabilities()
        self.protocol_version = protocol_version
        self.logger = get_logger(f"mcp.protocol.{server_info.name}")
        
        # Protocol state
        self.initialized = False
        self.client_info: Dict[str, Any] = {}
        
        # Method routing
        self._method_handlers: Dict[str, Callable] = {}
        self._register_core_handlers()
    
    def _register_core_handlers(self) -> None:
        """Register core MCP protocol method handlers"""
        self._method_handlers.update({
            "initialize": self._handle_initialize,
            "initialized": self._handle_initialized,
            "ping": self._handle_ping,
            "tools/list": self._handle_tools_list,
            "tools/call": self._handle_tools_call,
            "resources/list": self._handle_resources_list,
            "resources/read": self._handle_resources_read,
            "prompts/list": self._handle_prompts_list,
            "prompts/get": self._handle_prompts_get,
        })
    
    def register_method_handler(self, method: str, handler: Callable) -> None:
        """
        Register a custom method handler
        
        Args:
            method: Method name to handle
            handler: Handler function (can be sync or async)
        """
        self._method_handlers[method] = handler
        self.logger.debug(f"Registered custom handler for method: {method}")
    
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP request
        
        Args:
            request_data: Raw JSON-RPC request data
            
        Returns:
            JSON-RPC response data
        """
        start_time = datetime.now()
        request_id = request_data.get("id")
        method = request_data.get("method", "unknown")
        
        try:
            # Validate JSON-RPC format
            is_valid, error_msg = validate_json_rpc_request(request_data)
            if not is_valid:
                raise InvalidRequest(error_msg)
            
            # Log request
            self.logger.log_mcp_request(method, str(request_id), request_data.get("params"))
            
            # Route to handler
            result = await self._route_request(request_data)
            
            # Log successful response
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_mcp_response(str(request_id), True, duration)
            
            return create_json_rpc_response(request_id, result)
            
        except MCPError as e:
            # MCP protocol error
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_mcp_response(str(request_id), False, duration)
            self.logger.error(f"MCP Error in {method}", e)
            
            return create_json_rpc_error(
                code=e.code,
                message=e.message,
                data=e.data,
                request_id=request_id
            )
            
        except Exception as e:
            # Unexpected error
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_mcp_response(str(request_id), False, duration)
            self.logger.error(f"Unexpected error in {method}", e)
            
            return create_json_rpc_error(
                code=-32603,
                message="Internal error",
                data=str(e),
                request_id=request_id
            )
    
    async def _route_request(self, request_data: Dict[str, Any]) -> Any:
        """Route request to appropriate handler"""
        method = request_data["method"]
        params = request_data.get("params", {})
        
        # Find handler
        handler = self._method_handlers.get(method)
        if not handler:
            raise MethodNotFound(f"Unknown method: {method}")
        
        # Call handler (support both sync and async)
        if inspect.iscoroutinefunction(handler):
            return await handler(params)
        else:
            return handler(params)
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        # Validate required parameters
        if "protocolVersion" not in params:
            raise InvalidParams("Missing protocolVersion")
        
        if "clientInfo" not in params:
            raise InvalidParams("Missing clientInfo")
        
        client_version = params["protocolVersion"]
        if client_version != self.protocol_version:
            self.logger.warning(
                f"Protocol version mismatch: client={client_version}, "
                f"server={self.protocol_version}"
            )
        
        # Store client information
        self.client_info = params.get("clientInfo", {})
        
        # Call custom initialization hook
        await self._on_initialize(params)
        
        # Return server capabilities
        return {
            "protocolVersion": self.protocol_version,
            "serverInfo": {
                "name": self.server_info.name,
                "version": self.server_info.version,
                **({"description": self.server_info.description} 
                   if self.server_info.description else {}),
                **({"homepage": self.server_info.homepage} 
                   if self.server_info.homepage else {})
            },
            "capabilities": {
                "tools": self.capabilities.tools,
                "resources": self.capabilities.resources,
                "prompts": self.capabilities.prompts,
                "logging": self.capabilities.logging,
                **({"experimental": self.capabilities.experimental} 
                   if self.capabilities.experimental else {})
            }
        }
    
    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialization complete notification"""
        self.initialized = True
        self.logger.info("MCP client initialized successfully")
        await self._on_initialized(params)
        return None
    
    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request"""
        custom_response = await self._on_ping(params)
        if custom_response is not None:
            return custom_response
        return {"pong": True}
    
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools list request"""
        tools = await self.list_tools()
        return {"tools": tools}
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        if "name" not in params:
            raise InvalidParams("Missing tool name")
        
        tool_name = params["name"]
        arguments = params.get("arguments", {})
        
        result = await self.call_tool(tool_name, arguments)
        return result
    
    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources list request"""
        resources = await self.list_resources()
        return {"resources": resources}
    
    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request"""
        if "uri" not in params:
            raise InvalidParams("Missing resource URI")
        
        uri = params["uri"]
        content = await self.read_resource(uri)
        return {"contents": content}
    
    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts list request"""
        prompts = await self.list_prompts()
        return {"prompts": prompts}
    
    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompt get request"""
        if "name" not in params:
            raise InvalidParams("Missing prompt name")
        
        name = params["name"]
        arguments = params.get("arguments", {})
        
        prompt = await self.get_prompt(name, arguments)
        return prompt
    
    # Abstract methods for custom implementations
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools
        
        Returns:
            List of tool definitions
        """
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool with given arguments
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """
        List available resources
        
        Returns:
            List of resource definitions
        """
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """
        Read resource content by URI
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        pass
    
    @abstractmethod
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """
        List available prompts
        
        Returns:
            List of prompt definitions
        """
        pass
    
    @abstractmethod
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get prompt with given arguments
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
            
        Returns:
            Prompt content
        """
        pass
    
    # Extension hooks
    
    async def _on_initialize(self, params: Dict[str, Any]) -> None:
        """Hook called during initialization"""
        pass
    
    async def _on_initialized(self, params: Dict[str, Any]) -> None:
        """Hook called after initialization complete"""
        pass
    
    async def _on_ping(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Hook called during ping
        
        Returns:
            Custom ping response or None for default response
        """
        return None
    
    # Utility methods
    
    def is_initialized(self) -> bool:
        """Check if handler is initialized"""
        return self.initialized
    
    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return self.client_info.copy()
    
    def get_server_info(self) -> MCPServerInfo:
        """Get server information"""
        return self.server_info
    
    def get_capabilities(self) -> MCPCapabilities:
        """Get server capabilities"""
        return self.capabilities
    
    def update_capabilities(self, **kwargs) -> None:
        """
        Update server capabilities
        
        Args:
            **kwargs: Capability updates (tools, resources, prompts, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.capabilities, key):
                setattr(self.capabilities, key, value)
                self.logger.debug(f"Updated capability: {key}")
            else:
                self.logger.warning(f"Unknown capability: {key}")