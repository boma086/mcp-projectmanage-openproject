"""
自定义异常类和错误处理工具
"""
from typing import Dict, Any, Optional
import traceback
import os

class MCPError(Exception):
    """MCP协议相关错误的基类"""
    
    def __init__(self, message: str, code: int = -32603, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data or {}
    
    def to_json_rpc_error(self) -> Dict[str, Any]:
        """转换为JSON-RPC错误格式"""
        error = {
            "code": self.code,
            "message": self.message
        }
        if self.data:
            error["data"] = self.data
        return error

class ParseError(MCPError):
    """JSON解析错误"""
    def __init__(self, message: str = "Parse error", data: Optional[Dict[str, Any]] = None):
        super().__init__(message, -32700, data)

class InvalidRequest(MCPError):
    """无效请求错误"""
    def __init__(self, message: str = "Invalid Request", data: Optional[Dict[str, Any]] = None):
        super().__init__(message, -32600, data)

class MethodNotFound(MCPError):
    """方法未找到错误"""
    def __init__(self, method: str, data: Optional[Dict[str, Any]] = None):
        message = f"Method not found: {method}"
        super().__init__(message, -32601, data)

class InvalidParams(MCPError):
    """无效参数错误"""
    def __init__(self, message: str = "Invalid params", data: Optional[Dict[str, Any]] = None):
        super().__init__(message, -32602, data)

class InternalError(MCPError):
    """内部错误"""
    def __init__(self, message: str = "Internal error", data: Optional[Dict[str, Any]] = None):
        super().__init__(message, -32603, data)

class OpenProjectError(MCPError):
    """OpenProject API相关错误"""
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        data = {"status_code": status_code} if status_code else {}
        if response_data:
            data["response"] = response_data
        super().__init__(message, -32000, data)

class ConfigurationError(MCPError):
    """配置错误"""
    def __init__(self, message: str, config_key: Optional[str] = None):
        data = {"config_key": config_key} if config_key else {}
        super().__init__(message, -32001, data)

class AuthenticationError(MCPError):
    """认证错误"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, -32002)

class ToolExecutionError(MCPError):
    """工具执行错误"""
    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        data = {
            "tool_name": tool_name,
            "original_error": str(original_error) if original_error else None,
            "error_type": type(original_error).__name__ if original_error else None
        }
        super().__init__(f"Tool '{tool_name}' execution failed: {message}", -32003, data)

class ValidationError(MCPError):
    """数据验证错误"""
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        data = {}
        if field:
            data["field"] = field
        if value is not None:
            data["value"] = str(value)
        super().__init__(message, -32004, data)

def handle_exception(exception: Exception, request_id: Optional[str] = None, 
                    context: Optional[Dict[str, Any]] = None, 
                    debug_mode: Optional[bool] = None) -> Dict[str, Any]:
    """
    统一异常处理函数
    将各种异常转换为JSON-RPC错误响应
    debug_mode: 若为True则包含traceback，否则生产环境不暴露traceback
    """
    if debug_mode is None:
        debug_mode = os.environ.get('MCP_DEBUG_MODE', '').lower() in ('true', '1', 'yes')
    # 如果是已知的MCP错误，直接使用
    if isinstance(exception, MCPError):
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": exception.to_json_rpc_error()
        }
    else:
        # 未知异常，包装为内部错误
        error_data = {
            "exception_type": type(exception).__name__
        }
        if debug_mode:
            error_data["traceback"] = traceback.format_exc()
            if context:
                error_data["context"] = context
        internal_error = InternalError(
            f"Unexpected error: {str(exception)}", 
            error_data
        )
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": internal_error.to_json_rpc_error()
        }
    return error_response

def validate_json_rpc_request(data: Dict[str, Any]) -> None:
    """
    验证JSON-RPC请求格式
    """
    if not isinstance(data, dict):
        raise InvalidRequest("Request must be a JSON object")
    
    if data.get("jsonrpc") != "2.0":
        raise InvalidRequest("Missing or invalid 'jsonrpc' field")
    
    if "method" not in data:
        raise InvalidRequest("Missing 'method' field")
    
    if not isinstance(data["method"], str):
        raise InvalidRequest("'method' field must be a string")
    
    # id字段是可选的，但如果存在必须是字符串、数字或null
    if "id" in data:
        if not (isinstance(data["id"], (str, int, type(None)))):
            raise InvalidRequest("'id' field must be a string, number, or null")

def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any], 
                          required_args: list, optional_args: list = None) -> None:
    """
    验证工具参数
    """
    optional_args = optional_args or []
    
    # 检查必需参数
    for arg in required_args:
        if arg not in arguments:
            raise InvalidParams(f"Missing required argument '{arg}' for tool '{tool_name}'")
    
    # 检查未知参数
    all_valid_args = set(required_args + optional_args)
    for arg in arguments:
        if arg not in all_valid_args:
            raise InvalidParams(f"Unknown argument '{arg}' for tool '{tool_name}'")

def safe_execute(func, *args, **kwargs):
    """
    安全执行函数，捕获并包装异常
    """
    try:
        return func(*args, **kwargs)
    except MCPError:
        # MCP错误直接重新抛出
        raise
    except Exception as e:
        # 其他异常包装为内部错误
        raise InternalError(f"Execution failed: {str(e)}") from e
