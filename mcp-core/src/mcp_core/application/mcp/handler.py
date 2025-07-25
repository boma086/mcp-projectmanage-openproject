"""
MCP 协议处理器
"""
from typing import Dict, Any, Optional, Union
from datetime import datetime

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import (
    MCPError, ParseError, InvalidRequest, MethodNotFound, InvalidParams
)
from mcp_core.shared.utils import (
    validate_json_rpc_request, create_json_rpc_response, create_json_rpc_error,
    generate_request_id
)
from mcp_core.shared.logger import get_logger

from .tools import MCPToolManager
from .resources import MCPResourceManager


class MCPHandler:
    """MCP 协议处理器"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
        self.tool_manager = MCPToolManager(openproject_client)
        self.resource_manager = MCPResourceManager(openproject_client)
        self.logger = get_logger("mcp.handler")
        self.initialized = False
        self.client_info = {}
        
    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        start_time = datetime.now()
        request_id = request_data.get("id")
        method = request_data.get("method", "unknown")
        
        try:
            # 验证 JSON-RPC 格式
            is_valid, error_msg = validate_json_rpc_request(request_data)
            if not is_valid:
                raise InvalidRequest(error_msg)
            
            # 记录请求
            self.logger.log_mcp_request(method, str(request_id), request_data.get("params"))
            
            # 路由到具体处理方法
            result = await self._route_request(request_data)
            
            # 记录成功响应
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.log_mcp_response(str(request_id), True, duration)
            
            return create_json_rpc_response(request_id, result)
            
        except MCPError as e:
            # MCP 协议错误
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
            # 未预期的错误
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
        """路由请求到具体处理方法"""
        method = request_data["method"]
        params = request_data.get("params", {})
        
        # 核心协议方法
        if method == "initialize":
            return await self._handle_initialize(params)
        elif method == "initialized":
            return await self._handle_initialized(params)
        elif method == "ping":
            return await self._handle_ping(params)
        
        # 工具相关方法
        elif method == "tools/list":
            return await self.tool_manager.list_tools()
        elif method == "tools/call":
            return await self.tool_manager.call_tool(params)
        
        # 资源相关方法
        elif method == "resources/list":
            return await self.resource_manager.list_resources()
        elif method == "resources/read":
            return await self.resource_manager.read_resource(params)
        
        # 提示相关方法
        elif method == "prompts/list":
            return await self._handle_prompts_list()
        elif method == "prompts/get":
            return await self._handle_prompts_get(params)
        
        else:
            raise MethodNotFound(f"Unknown method: {method}")
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        # 验证参数
        if "protocolVersion" not in params:
            raise InvalidParams("Missing protocolVersion")
        
        if "clientInfo" not in params:
            raise InvalidParams("Missing clientInfo")
        
        # 保存客户端信息
        self.client_info = params.get("clientInfo", {})
        
        # 返回服务器能力
        return {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "mcp-openproject-server",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {},
                "logging": {}
            }
        }
    
    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """处理初始化完成通知"""
        self.initialized = True
        self.logger.info("MCP client initialized successfully")
        return None
    
    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理 ping 请求"""
        return {"pong": True}
    
    async def _handle_prompts_list(self) -> Dict[str, Any]:
        """处理提示列表请求"""
        prompts = [
            {
                "name": "project_analysis",
                "description": "分析项目状态和进展",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "项目 ID",
                        "required": True
                    }
                ]
            },
            {
                "name": "task_prioritization", 
                "description": "任务优先级建议",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "项目 ID",
                        "required": True
                    }
                ]
            }
        ]
        
        return {"prompts": prompts}
    
    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取提示请求"""
        name = params.get("name")
        if not name:
            raise InvalidParams("Missing prompt name")
        
        arguments = params.get("arguments", {})
        
        if name == "project_analysis":
            project_id = arguments.get("project_id")
            if not project_id:
                raise InvalidParams("Missing project_id argument")
            
            # 获取项目信息生成提示
            project = await self.client.get_project(project_id)
            if not project:
                raise InvalidParams(f"Project not found: {project_id}")
            
            prompt = f"""请分析项目 "{project.name}" 的当前状态：

项目信息：
- 名称：{project.name}
- 标识符：{project.identifier}
- 状态：{project.status or '未知'}
- 描述：{project.description or '无描述'}

请从以下角度进行分析：
1. 项目整体进展情况
2. 存在的风险和问题
3. 改进建议
4. 下一步行动计划
"""
            
            return {
                "description": f"分析项目 {project.name} 的状态",
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt
                        }
                    }
                ]
            }
        
        elif name == "task_prioritization":
            project_id = arguments.get("project_id")
            if not project_id:
                raise InvalidParams("Missing project_id argument")
            
            # 获取工作包信息生成提示
            work_packages = await self.client.get_work_packages(project_id)
            
            prompt = f"""请为项目的任务提供优先级建议：

当前有 {len(work_packages)} 个工作包需要处理。

请根据以下标准提供优先级建议：
1. 紧急程度（截止日期）
2. 重要程度（业务价值）
3. 依赖关系
4. 资源可用性
5. 风险评估

请提供具体的优先级排序和理由。
"""
            
            return {
                "description": f"为项目任务提供优先级建议",
                "messages": [
                    {
                        "role": "user", 
                        "content": {
                            "type": "text",
                            "text": prompt
                        }
                    }
                ]
            }
        
        else:
            raise InvalidParams(f"Unknown prompt: {name}")
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self.initialized
    
    def get_client_info(self) -> Dict[str, Any]:
        """获取客户端信息"""
        return self.client_info.copy()
