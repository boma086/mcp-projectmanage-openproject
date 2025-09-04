"""
HTTP 解决方案专用配置 - FastAPI 同步模式
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class HTTPSolutionConfig(BaseSettings):
    """HTTP 解决方案配置类 - FastAPI 同步实现"""
    
    # 应用程序配置
    app_name: str = Field(
        default="http-mcp",
        description="应用程序名称"
    )
    app_version: str = Field(
        default="1.0.0",
        description="应用程序版本"
    )
    environment: str = Field(
        default="development",
        description="运行环境 (development, testing, production)"
    )
    debug: bool = Field(
        default=False,
        description="调试模式"
    )
    
    # OpenProject 配置
    openproject_url: str = Field(
        default="http://localhost:8090",
        description="OpenProject 服务器地址"
    )
    openproject_api_key: str = Field(
        default="",
        description="OpenProject API 密钥"
    )
    openproject_timeout: int = Field(
        default=30,
        description="OpenProject 请求超时时间（秒）"
    )
    openproject_max_retries: int = Field(
        default=3,
        description="OpenProject 请求最大重试次数"
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
    workers: int = Field(
        default=2,
        description="工作进程数"
    )
    
    # CORS 配置
    cors_allow_origins: str = Field(
        default="http://localhost,http://127.0.0.1",
        description="允许的 CORS 源，逗号分隔"
    )
    trusted_hosts: str = Field(
        default="localhost,127.0.0.1",
        description="受信任的主机，逗号分隔"
    )
    
    # 日志配置
    log_level: str = Field(
        default="INFO",
        description="日志级别"
    )
    
    # 性能配置
    request_timeout: int = Field(
        default=30,
        description="HTTP 请求超时时间（秒）"
    )
    max_connections: int = Field(
        default=100,
        description="最大并发连接数"
    )
    max_concurrent_requests: int = Field(
        default=500,
        description="最大并发请求数"
    )
    max_request_size: int = Field(
        default=10485760,
        description="最大请求大小（字节）"
    )
    
    # 缓存配置
    cache_ttl: int = Field(
        default=300,
        description="缓存过期时间（秒）"
    )
    
    # 模板配置
    templates_dir: str = Field(
        default="templates",
        description="模板目录路径"
    )
    
    # 监控配置
    enable_metrics: bool = Field(
        default=True,
        description="启用指标收集"
    )
    metrics_endpoint: str = Field(
        default="/metrics",
        description="指标端点"
    )
    health_check_interval: int = Field(
        default=30,
        description="健康检查间隔（秒）"
    )
    deep_health_check_interval: int = Field(
        default=300,
        description="深度健康检查间隔（秒）"
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """获取 CORS 源列表"""
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]
    
    @property
    def trusted_hosts_list(self) -> List[str]:
        """获取受信任主机列表"""
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]
    
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
