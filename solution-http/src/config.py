"""
HTTP 解决方案专用配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class HTTPSolutionConfig(BaseSettings):
    """HTTP 解决方案配置类"""
    
    # OpenProject 配置
    openproject_url: str = Field(
        default="http://localhost:8090",
        description="OpenProject 服务器地址"
    )
    openproject_api_key: str = Field(
        default="",
        description="OpenProject API 密钥"
    )
    
    # HTTP 服务器配置
    host: str = Field(
        default="0.0.0.0",
        description="HTTP 服务器监听地址"
    )
    port: int = Field(
        default=8010,
        description="HTTP 服务器端口"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    
    # 模板配置
    templates_dir: str = Field(
        default="templates",
        description="模板目录路径"
    )
    
    # 缓存配置
    cache_ttl: int = Field(
        default=300,
        description="缓存过期时间（秒）"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # 允许额外字段，向前兼容
        extra = "ignore"


# 全局配置实例
_http_config_instance: Optional[HTTPSolutionConfig] = None


def get_http_config() -> HTTPSolutionConfig:
    """获取 HTTP 解决方案配置实例"""
    global _http_config_instance
    if _http_config_instance is None:
        _http_config_instance = HTTPSolutionConfig()
    return _http_config_instance


def set_http_config(config: HTTPSolutionConfig) -> None:
    """设置 HTTP 解决方案配置实例"""
    global _http_config_instance
    _http_config_instance = config
