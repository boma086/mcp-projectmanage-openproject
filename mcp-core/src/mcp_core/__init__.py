"""
MCP Core Library

共享核心库：MCP (Model Context Protocol) 项目管理系统
"""

__version__ = "0.1.0"
__author__ = "MCP Project Team"
__email__ = "team@mcp-project.com"

# 导出主要组件
from mcp_core.domain.models import Project, WorkPackage, User, Report, ReportSection
from mcp_core.shared.exceptions import MCPError, OpenProjectError, ValidationError
from mcp_core.shared.config import Config, set_global_config
from mcp_core.shared.logger import get_logger, mcp_logger
from mcp_core.shared.utils import generate_request_id, validate_json_rpc_request
from mcp_core.application.mcp import MCPHandler, MCPToolManager, MCPResourceManager

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__email__",

    # 核心模型
    "Project",
    "WorkPackage",
    "User",
    "Report",
    "ReportSection",

    # 异常类
    "MCPError",
    "OpenProjectError",
    "ValidationError",

    # 配置和工具
    "Config",
    "set_global_config",
    "get_logger",
    "mcp_logger",
    "generate_request_id",
    "validate_json_rpc_request",

    # MCP 组件
    "MCPHandler",
    "MCPToolManager",
    "MCPResourceManager",
]
