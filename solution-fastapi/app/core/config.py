"""
FastAPI MCP 服务器配置管理
"""
import os
from typing import Optional, List
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = Field(default="OpenProject MCP Server", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # OpenProject 配置
    openproject_url: str = Field(..., env="OPENPROJECT_URL")
    openproject_api_key: str = Field(..., env="OPENPROJECT_API_KEY")
    
    # MCP 协议配置
    mcp_version: str = Field(default="2024-11-05", env="MCP_VERSION")
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")  # 30秒
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # 缓存配置
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # 5分钟
    
    # 任务队列配置
    celery_broker_url: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    
    # 安全配置
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    # 模板配置
    templates_dir: str = Field(default="templates", env="TEMPLATES_DIR")
    default_template_language: str = Field(default="zh-CN", env="DEFAULT_TEMPLATE_LANGUAGE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
