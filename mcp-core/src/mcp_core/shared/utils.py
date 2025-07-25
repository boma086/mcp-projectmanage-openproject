"""
通用工具函数
"""
import json
import uuid
from datetime import datetime, date
from typing import Any, Dict, Optional, Union
from pathlib import Path


def generate_request_id() -> str:
    """生成请求 ID"""
    return str(uuid.uuid4())


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的 JSON 解析"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: Any = None) -> str:
    """安全的 JSON 序列化"""
    try:
        return json.dumps(obj, ensure_ascii=False, default=json_serializer)
    except (TypeError, ValueError):
        return json.dumps(default) if default is not None else "{}"


def json_serializer(obj: Any) -> Any:
    """JSON 序列化器，处理特殊类型"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)


def validate_json_rpc_request(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """验证 JSON-RPC 请求格式"""
    # 检查必需字段
    if "jsonrpc" not in data:
        return False, "Missing 'jsonrpc' field"
    
    if data["jsonrpc"] != "2.0":
        return False, "Invalid 'jsonrpc' version, must be '2.0'"
    
    if "method" not in data:
        return False, "Missing 'method' field"
    
    if not isinstance(data["method"], str):
        return False, "'method' must be a string"
    
    # id 字段是可选的，但如果存在必须是字符串、数字或 null
    if "id" in data:
        if not isinstance(data["id"], (str, int, type(None))):
            return False, "'id' must be a string, number, or null"
    
    # params 字段是可选的
    if "params" in data:
        if not isinstance(data["params"], (dict, list)):
            return False, "'params' must be an object or array"
    
    return True, None


def create_json_rpc_response(request_id: Optional[Union[str, int]], 
                           result: Any = None, 
                           error: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """创建 JSON-RPC 响应"""
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    
    if error:
        response["error"] = error
    else:
        response["result"] = result
    
    return response


def create_json_rpc_error(code: int, message: str, 
                         data: Any = None, 
                         request_id: Optional[Union[str, int]] = None) -> Dict[str, Any]:
    """创建 JSON-RPC 错误响应"""
    error = {
        "code": code,
        "message": message
    }
    
    if data is not None:
        error["data"] = data
    
    return create_json_rpc_response(request_id, error=error)


def ensure_directory(path: Union[str, Path]) -> Path:
    """确保目录存在"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_file_safe(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """安全读取文件"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, IOError, UnicodeDecodeError):
        return None


def write_file_safe(file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
    """安全写入文件"""
    try:
        # 确保目录存在
        ensure_directory(Path(file_path).parent)
        
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except (IOError, UnicodeEncodeError):
        return False


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """截断字符串"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """格式化持续时间"""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    import re
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    # 限制长度
    return filename[:255]


def deep_merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并字典"""
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def extract_error_message(exception: Exception) -> str:
    """提取异常错误信息"""
    if hasattr(exception, 'message'):
        return str(exception.message)
    else:
        return str(exception)
