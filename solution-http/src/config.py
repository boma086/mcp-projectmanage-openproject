"""
HTTP 解决方案专用配置 - FastAPI 同步模式
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class HTTPSolutionConfig(BaseSettings):
    """HTTP 解决方案配置类 - FastAPI 同步实现"""
    
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
    
    # CORS 配置
    cors_allow_origins: str = Field(
        default="http://localhost,http://127.0.0.1",
        description="允许的 CORS 源，逗号分隔"
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
    
    # 请求超时配置
    request_timeout: int = Field(
        default=30,
        description="HTTP 请求超时时间（秒）"
    )
    
    # 最大连接数
    max_connections: int = Field(
        default=100,
        description="最大并发连接数"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS 源列表"""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
    
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


def reset_http_config() -> None:
    """重置配置实例（主要用于测试）"""
    global _http_config_instance
    _http_config_instance = None
