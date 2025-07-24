"""
日志配置模块
提供结构化日志记录功能
"""
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """结构化日志格式化器，增强序列化健壮性"""
    
    def _safe_serialize(self, obj):
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: self._safe_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [self._safe_serialize(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            try:
                return str(obj)
            except Exception:
                return f"<Unserializable: {type(obj).__name__}>"

    def format(self, record: logging.LogRecord) -> str:
        # 基础日志信息
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外的上下文信息
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
            
        # 添加请求相关信息
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'client_ip'):
            log_data["client_ip"] = record.client_ip
        if hasattr(record, 'method'):
            log_data["http_method"] = record.method
        if hasattr(record, 'path'):
            log_data["path"] = record.path
            
        try:
            return json.dumps(log_data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            try:
                safe_data = self._safe_serialize(log_data)
                safe_data["_serialization_warning"] = f"Partial serialization: {str(e)}"
                return json.dumps(safe_data, ensure_ascii=False)
            except Exception as fallback_error:
                return json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "level": "ERROR",
                    "logger": __name__,
                    "message": f"Critical log serialization failure: {str(fallback_error)}",
                    "original_message": str(getattr(record, 'msg', 'N/A'))
                }, ensure_ascii=False)

def setup_logging(log_level: str = "INFO"):
    """配置日志处理器，支持动态级别和格式"""
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    level = log_level.upper()
    if level not in valid_levels:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {valid_levels}")
    numeric_level = getattr(logging, level)

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    if os.getenv("LOG_FORMAT", "simple").lower() == "json":
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

    # 根日志器配置
    logging.basicConfig(
        level=numeric_level,
        handlers=[console_handler],
        force=True  # 覆盖现有配置
    )

class MCPLogger:
    """MCP服务器日志管理器"""
    
    def __init__(self, name: str = "mcp-server", log_level: str = "INFO"):
        setup_logging(log_level)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        
        # 根据环境选择格式化器
        if os.getenv("LOG_FORMAT", "simple").lower() == "json":
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        self.logger.addHandler(console_handler)
        
        # 文件处理器（如果配置了日志文件）
        log_file = os.getenv("LOG_FILE")
        if log_file:
            self._setup_file_handler(log_file)
    
    def _setup_file_handler(self, log_file: str):
        """设置文件日志处理器"""
        try:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(StructuredFormatter())
            
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"无法设置文件日志处理器: {e}")
    
    def log_request(self, method: str, path: str, client_ip: str, 
                   request_id: str, extra_data: Optional[Dict[str, Any]] = None):
        """记录请求日志"""
        self.logger.info(
            f"收到请求: {method} {path}",
            extra={
                'request_id': request_id,
                'client_ip': client_ip,
                'method': method,
                'path': path,
                'extra_data': extra_data or {}
            }
        )
    
    def log_response(self, request_id: str, status_code: int, 
                    response_time: float, extra_data: Optional[Dict[str, Any]] = None):
        """记录响应日志"""
        self.logger.info(
            f"响应完成: {status_code} ({response_time:.3f}s)",
            extra={
                'request_id': request_id,
                'status_code': status_code,
                'response_time': response_time,
                'extra_data': extra_data or {}
            }
        )
    
    def log_error(self, message: str, error: Exception, 
                 request_id: Optional[str] = None, extra_data: Optional[Dict[str, Any]] = None):
        """记录错误日志"""
        self.logger.error(
            message,
            exc_info=error,
            extra={
                'request_id': request_id,
                'error_type': type(error).__name__,
                'extra_data': extra_data or {}
            }
        )
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive values in arguments dict (e.g., password, token, api_key).
        """
        SENSITIVE_KEYS = ["password", "token", "api_key"]
        sanitized = {}
        for k, v in arguments.items():
            if any(sens in k.lower() for sens in SENSITIVE_KEYS):
                sanitized[k] = "***REDACTED***"
            else:
                sanitized[k] = v
        return sanitized

    def log_tool_call(self, tool_name: str, arguments: Dict[str, Any], 
                     request_id: str, success: bool, execution_time: float):
        """记录工具调用日志"""
        level = logging.INFO if success else logging.ERROR
        status = "成功" if success else "失败"
        sanitized_arguments = self._sanitize_arguments(arguments)
        self.logger.log(
            level,
            f"工具调用{status}: {tool_name} ({execution_time:.3f}s)",
            extra={
                'request_id': request_id,
                'tool_name': tool_name,
                'arguments': sanitized_arguments,
                'success': success,
                'execution_time': execution_time,
                'extra_data': {'type': 'tool_call'}
            }
        )
    
    def log_openproject_api(self, endpoint: str, method: str, 
                           success: bool, response_time: float, 
                           request_id: Optional[str] = None):
        """记录OpenProject API调用日志"""
        level = logging.INFO if success else logging.ERROR
        status = "成功" if success else "失败"
        
        self.logger.log(
            level,
            f"OpenProject API调用{status}: {method} {endpoint} ({response_time:.3f}s)",
            extra={
                'request_id': request_id,
                'api_endpoint': endpoint,
                'api_method': method,
                'success': success,
                'response_time': response_time,
                'extra_data': {'type': 'openproject_api'}
            }
        )

# 全局日志实例
mcp_logger = MCPLogger(
    name="mcp-openproject",
    log_level=os.getenv("LOG_LEVEL", "INFO")
)
