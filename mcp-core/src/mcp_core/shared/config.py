"""
共享配置管理
"""
import os
from typing import Optional, List, Any, Dict
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """统一配置类"""
    
    # OpenProject 配置
    openproject_url: str = Field(..., env="OPENPROJECT_URL", description="OpenProject 实例 URL")
    openproject_api_key: str = Field(..., env="OPENPROJECT_API_KEY", description="OpenProject API 密钥")
    
    # MCP 协议配置
    mcp_version: str = Field(default="2024-11-05", env="MCP_VERSION", description="MCP 协议版本")
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE", description="最大请求大小")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT", description="请求超时时间（秒）")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL", description="日志级别")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="日志格式"
    )
    
    # 缓存配置
    cache_ttl: int = Field(default=300, env="CACHE_TTL", description="缓存过期时间（秒）")
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE", description="缓存最大条目数")
    
    # 模板配置
    templates_dir: str = Field(default="templates", env="TEMPLATES_DIR", description="模板目录")
    default_template_language: str = Field(default="zh-CN", env="DEFAULT_TEMPLATE_LANGUAGE", description="默认模板语言")
    
    # 性能配置
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS", description="最大并发请求数")
    retry_attempts: int = Field(default=3, env="RETRY_ATTEMPTS", description="重试次数")
    retry_delay: float = Field(default=1.0, env="RETRY_DELAY", description="重试延迟（秒）")
    
    # 安全配置
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS", description="允许的来源")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER", description="API 密钥头部名称")
    
    @validator('openproject_url')
    def validate_openproject_url(cls, v):
        if not v:
            raise ValueError('OpenProject URL 不能为空')
        if not v.startswith(('http://', 'https://')):
            raise ValueError('OpenProject URL 必须以 http:// 或 https:// 开头')
        return v.rstrip('/')
    
    @validator('openproject_api_key')
    def validate_openproject_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('OpenProject API 密钥无效')
        return v.strip()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'日志级别必须是: {", ".join(valid_levels)}')
        return v.upper()
    
    @validator('cache_ttl')
    def validate_cache_ttl(cls, v):
        if v < 0:
            raise ValueError('缓存过期时间不能为负数')
        return v
    
    @validator('max_concurrent_requests')
    def validate_max_concurrent_requests(cls, v):
        if v < 1:
            raise ValueError('最大并发请求数必须大于 0')
        return v
    
    @validator('retry_attempts')
    def validate_retry_attempts(cls, v):
        if v < 0:
            raise ValueError('重试次数不能为负数')
        return v
    
    def get_openproject_headers(self) -> Dict[str, str]:
        """获取 OpenProject API 请求头"""
        return {
            'Authorization': f'Bearer {self.openproject_api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置"""
        return {
            'ttl': self.cache_ttl,
            'max_size': self.cache_max_size
        }
    
    def get_retry_config(self) -> Dict[str, Any]:
        """获取重试配置"""
        return {
            'attempts': self.retry_attempts,
            'delay': self.retry_delay
        }
    
    def is_debug_mode(self) -> bool:
        """检查是否为调试模式"""
        return self.log_level == 'DEBUG'
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # 允许额外字段，支持不同解决方案的特定配置
        extra = "ignore"


# 全局配置实例
def get_config() -> Config:
    """获取配置实例"""
    return Config()


# 创建默认配置实例
_config_instance: Optional[Config] = None


def get_global_config() -> Config:
    """获取全局配置实例（单例模式）"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def set_global_config(config: Config) -> None:
    """设置全局配置实例"""
    global _config_instance
    _config_instance = config
