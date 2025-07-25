"""
MCP 协议处理器
负责处理 MCP (Model Context Protocol) 请求和响应
"""
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, Union
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import MCPError, ParseError, InvalidRequest, MethodNotFound
from app.services.openproject_service import OpenProjectService
from app.services.tool_service import ToolService
from app.services.resource_service import ResourceService
from app.services.prompt_service import PromptService
from app.services.report_service import ReportService
from app.services.template_service import TemplateService
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class MCPHandler:
    """MCP 协议处理器"""
    
    def __init__(self):
        self.openproject_service: Optional[OpenProjectService] = None
        self.tool_service: Optional[ToolService] = None
        self.resource_service: Optional[ResourceService] = None
        self.prompt_service: Optional[PromptService] = None
        self.report_service: Optional[ReportService] = None
        self.template_service: Optional[TemplateService] = None
        self.initialized = False
        self.server_info = {
            "name": settings.app_name,
            "version": settings.app_version,
            "protocol_version": settings.mcp_version
        }
    
    async def initialize(self):
        """初始化 MCP 处理器"""
        try:
            logger.info("正在初始化 MCP 处理器...")
            
            # 初始化 OpenProject 服务
            self.openproject_service = OpenProjectService(
                url=settings.openproject_url,
                api_key=settings.openproject_api_key
            )
            await self.openproject_service.initialize()
            
            # 初始化其他服务
            self.template_service = TemplateService()
            self.tool_service = ToolService(self.openproject_service)
            self.resource_service = ResourceService(self.openproject_service)
            self.prompt_service = PromptService(self.openproject_service)
            self.report_service = ReportService(self.openproject_service)

            # 创建默认模板
            await self.template_service.create_default_templates()
            
            self.initialized = True
            logger.info("MCP 处理器初始化成功")
            
        except Exception as e:
            logger.error(f"MCP 处理器初始化失败: {e}")
            raise MCPError(f"Failed to initialize MCP handler: {str(e)}")
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.openproject_service:
                await self.openproject_service.cleanup()
            self.initialized = False
            logger.info("MCP 处理器清理完成")
        except Exception as e:
            logger.error(f"MCP 处理器清理失败: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        if not self.initialized:
            return {
                "status": "unhealthy",
                "message": "MCP handler not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 检查 OpenProject 连接
            openproject_status = await self.openproject_service.check_connection()
            
            return {
                "status": "healthy" if openproject_status else "degraded",
                "services": {
                    "openproject": "healthy" if openproject_status else "unhealthy",
                    "mcp_handler": "healthy"
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def handle_request(self, body: bytes, content_type: str) -> Dict[str, Any]:
        """处理 MCP 请求"""
        if not self.initialized:
            raise MCPError("MCP handler not initialized")
        
        try:
            # 解析请求
            if content_type.startswith("application/json"):
                request_data = json.loads(body.decode('utf-8'))
            else:
                raise ParseError(f"Unsupported content type: {content_type}")
            
            # 验证 JSON-RPC 格式
            self._validate_jsonrpc_request(request_data)
            
            # 提取请求信息
            method = request_data.get("method")
            params = request_data.get("params", {})
            request_id = request_data.get("id")
            
            logger.debug(f"处理 MCP 请求: {method}")
            
            # 路由到相应的处理方法
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_list_tools()
            elif method == "tools/call":
                result = await self._handle_call_tool(params)
            elif method == "resources/list":
                result = await self._handle_list_resources()
            elif method == "resources/read":
                result = await self._handle_read_resource(params)
            elif method == "prompts/list":
                result = await self._handle_list_prompts()
            elif method == "prompts/get":
                result = await self._handle_get_prompt(params)
            else:
                raise MethodNotFound(f"Unknown method: {method}")
            
            # 构建响应
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
            
            return response
            
        except MCPError as e:
            # MCP 协议错误
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id") if 'request_data' in locals() else None,
                "error": {
                    "code": e.code,
                    "message": str(e),
                    "data": getattr(e, 'data', None)
                }
            }
            return error_response
            
        except Exception as e:
            # 未知错误
            logger.error(f"处理 MCP 请求时发生未知错误: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id") if 'request_data' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            return error_response
    
    def _validate_jsonrpc_request(self, request_data: Dict[str, Any]):
        """验证 JSON-RPC 请求格式"""
        if not isinstance(request_data, dict):
            raise ParseError("Request must be a JSON object")
        
        if request_data.get("jsonrpc") != "2.0":
            raise InvalidRequest("Invalid JSON-RPC version")
        
        if "method" not in request_data:
            raise InvalidRequest("Missing method field")
        
        if not isinstance(request_data["method"], str):
            raise InvalidRequest("Method must be a string")
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        return {
            "protocolVersion": settings.mcp_version,
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "serverInfo": self.server_info
        }
    
    async def _handle_list_tools(self) -> Dict[str, Any]:
        """处理工具列表请求"""
        tools = await self.tool_service.list_tools()
        return {"tools": tools}
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not tool_name:
            raise InvalidRequest("Missing tool name")
        
        result = await self.tool_service.call_tool(tool_name, arguments)
        return result
    
    async def _handle_list_resources(self) -> Dict[str, Any]:
        """处理资源列表请求"""
        resources = await self.resource_service.list_resources()
        return {"resources": resources}
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理资源读取请求"""
        uri = params.get("uri")
        
        if not uri:
            raise InvalidRequest("Missing resource URI")
        
        result = await self.resource_service.read_resource(uri)
        return result
    
    async def _handle_list_prompts(self) -> Dict[str, Any]:
        """处理提示列表请求"""
        prompts = await self.prompt_service.list_prompts()
        return {"prompts": prompts}
    
    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取提示请求"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise InvalidRequest("Missing prompt name")
        
        result = await self.prompt_service.get_prompt(name, arguments)
        return result
