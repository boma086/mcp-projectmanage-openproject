"""
统一日志工具
"""
import logging
import sys
from typing import Optional
from datetime import datetime

from .config import get_global_config


class MCPLogger:
    """MCP 统一日志器"""
    
    def __init__(self, name: str = "mcp"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志器"""
        config = get_global_config()
        
        # 设置日志级别
        self.logger.setLevel(getattr(logging, config.log_level))
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            # 创建控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.log_level))
            
            # 创建格式器
            formatter = logging.Formatter(config.log_format)
            console_handler.setFormatter(formatter)
            
            # 添加处理器
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, extra: Optional[dict] = None):
        """调试日志"""
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, extra: Optional[dict] = None):
        """信息日志"""
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, extra: Optional[dict] = None):
        """警告日志"""
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, exception: Optional[Exception] = None, extra: Optional[dict] = None):
        """错误日志"""
        if exception:
            self.logger.error(f"{message}: {str(exception)}", exc_info=True, extra=extra)
        else:
            self.logger.error(message, extra=extra)
    
    def critical(self, message: str, exception: Optional[Exception] = None, extra: Optional[dict] = None):
        """严重错误日志"""
        if exception:
            self.logger.critical(f"{message}: {str(exception)}", exc_info=True, extra=extra)
        else:
            self.logger.critical(message, extra=extra)
    
    def log_request(self, method: str, url: str, status_code: Optional[int] = None, 
                   duration: Optional[float] = None):
        """记录请求日志"""
        message = f"{method} {url}"
        if status_code:
            message += f" -> {status_code}"
        if duration:
            message += f" ({duration:.3f}s)"
        
        if status_code and status_code >= 400:
            self.error(message)
        else:
            self.info(message)
    
    def log_mcp_request(self, method: str, request_id: str, params: Optional[dict] = None):
        """记录 MCP 请求日志"""
        message = f"MCP {method} (ID: {request_id})"
        if params:
            message += f" params: {params}"
        self.info(message)
    
    def log_mcp_response(self, request_id: str, success: bool, duration: Optional[float] = None):
        """记录 MCP 响应日志"""
        status = "SUCCESS" if success else "ERROR"
        message = f"MCP Response (ID: {request_id}) -> {status}"
        if duration:
            message += f" ({duration:.3f}s)"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_error(self, operation: str, exception: Exception, context: Optional[dict] = None):
        """记录操作错误"""
        message = f"Operation '{operation}' failed"
        extra = {"operation": operation}
        if context:
            extra.update(context)
        
        self.error(message, exception=exception, extra=extra)


# 全局日志器实例
_logger_instance: Optional[MCPLogger] = None


def get_logger(name: str = "mcp") -> MCPLogger:
    """获取日志器实例"""
    global _logger_instance
    if _logger_instance is None or _logger_instance.name != name:
        _logger_instance = MCPLogger(name)
    return _logger_instance


# 便捷的全局日志器
mcp_logger = get_logger("mcp")
