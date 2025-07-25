"""
共享异常定义
"""
from typing import Any, Optional, Dict


class MCPError(Exception):
    """MCP 协议基础异常"""
    
    def __init__(self, message: str, code: int = -32603, data: Optional[Any] = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)
    
    def __str__(self):
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result


class ParseError(MCPError):
    """JSON 解析错误"""
    
    def __init__(self, message: str = "Parse error", data: Optional[Any] = None):
        super().__init__(message, code=-32700, data=data)


class InvalidRequest(MCPError):
    """无效请求错误"""
    
    def __init__(self, message: str = "Invalid Request", data: Optional[Any] = None):
        super().__init__(message, code=-32600, data=data)


class MethodNotFound(MCPError):
    """方法未找到错误"""
    
    def __init__(self, message: str = "Method not found", data: Optional[Any] = None):
        super().__init__(message, code=-32601, data=data)


class InvalidParams(MCPError):
    """无效参数错误"""
    
    def __init__(self, message: str = "Invalid params", data: Optional[Any] = None):
        super().__init__(message, code=-32602, data=data)


class InternalError(MCPError):
    """内部错误"""
    
    def __init__(self, message: str = "Internal error", data: Optional[Any] = None):
        super().__init__(message, code=-32603, data=data)


class OpenProjectError(MCPError):
    """OpenProject API 错误"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, data: Optional[Any] = None):
        self.status_code = status_code
        super().__init__(message, code=-32000, data=data)


class AuthenticationError(OpenProjectError):
    """认证错误"""
    
    def __init__(self, message: str = "Authentication failed", data: Optional[Any] = None):
        super().__init__(message, status_code=401, data=data)


class AuthorizationError(OpenProjectError):
    """授权错误"""
    
    def __init__(self, message: str = "Authorization failed", data: Optional[Any] = None):
        super().__init__(message, status_code=403, data=data)


class NotFoundError(OpenProjectError):
    """资源未找到错误"""
    
    def __init__(self, message: str = "Resource not found", data: Optional[Any] = None):
        super().__init__(message, status_code=404, data=data)


class ValidationError(MCPError):
    """数据验证错误"""
    
    def __init__(self, message: str, field: Optional[str] = None, data: Optional[Any] = None):
        self.field = field
        super().__init__(message, code=-32602, data=data)


class ConfigurationError(MCPError):
    """配置错误"""
    
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(message, code=-32001, data=data)


class TimeoutError(MCPError):
    """超时错误"""
    
    def __init__(self, message: str = "Request timeout", data: Optional[Any] = None):
        super().__init__(message, code=-32002, data=data)


class RateLimitError(MCPError):
    """速率限制错误"""
    
    def __init__(self, message: str = "Rate limit exceeded", data: Optional[Any] = None):
        super().__init__(message, code=-32003, data=data)


class TemplateError(MCPError):
    """模板错误"""
    
    def __init__(self, message: str, template_id: Optional[str] = None, data: Optional[Any] = None):
        self.template_id = template_id
        super().__init__(message, code=-32004, data=data)


class CacheError(MCPError):
    """缓存错误"""
    
    def __init__(self, message: str = "Cache operation failed", data: Optional[Any] = None):
        super().__init__(message, code=-32005, data=data)
