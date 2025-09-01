"""
Async FastAPI MCP Server Configuration Management

This module provides comprehensive configuration management for the async FastAPI
MCP server with support for environment variables, validation, and async operations.
"""
import os
import asyncio
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Async application configuration with validation and performance optimizations"""
    
    # Application base configuration
    app_name: str = Field(default="Async OpenProject MCP Server", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Server configuration for async operations
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8020, env="PORT")
    workers: int = Field(default=1, env="WORKERS")
    worker_connections: int = Field(default=1000, env="WORKER_CONNECTIONS")
    
    # OpenProject configuration with async support
    openproject_url: str = Field(..., env="OPENPROJECT_URL")
    openproject_api_key: str = Field(..., env="OPENPROJECT_API_KEY")
    openproject_timeout: int = Field(default=30, env="OPENPROJECT_TIMEOUT")
    openproject_max_retries: int = Field(default=3, env="OPENPROJECT_MAX_RETRIES")
    openproject_retry_delay: float = Field(default=1.0, env="OPENPROJECT_RETRY_DELAY")
    
    # MCP protocol configuration with async optimizations
    mcp_version: str = Field(default="2024-11-05", env="MCP_VERSION")
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")  # 30 seconds
    max_concurrent_requests: int = Field(default=100, env="MAX_CONCURRENT_REQUESTS")
    request_queue_size: int = Field(default=1000, env="REQUEST_QUEUE_SIZE")
    
    # Logging configuration for async operations
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    enable_access_log: bool = Field(default=True, env="ENABLE_ACCESS_LOG")
    log_json_format: bool = Field(default=False, env="LOG_JSON_FORMAT")
    
    # Async caching configuration
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")  # 5 minutes
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_max_connections: int = Field(default=50, env="CACHE_MAX_CONNECTIONS")
    cache_timeout: int = Field(default=5, env="CACHE_TIMEOUT")
    
    # Async task queue configuration
    celery_broker_url: Optional[str] = Field(default=None, env="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, env="CELERY_RESULT_BACKEND")
    task_queue_enabled: bool = Field(default=False, env="TASK_QUEUE_ENABLED")
    max_background_tasks: int = Field(default=50, env="MAX_BACKGROUND_TASKS")
    
    # Security configuration
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    enable_https_redirect: bool = Field(default=False, env="ENABLE_HTTPS_REDIRECT")
    trusted_hosts: List[str] = Field(default=["localhost", "127.0.0.1"], env="TRUSTED_HOSTS")
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Template and internationalization configuration
    templates_dir: str = Field(default="templates", env="TEMPLATES_DIR")
    default_template_language: str = Field(default="en", env="DEFAULT_TEMPLATE_LANGUAGE")
    supported_languages: List[str] = Field(default=["en", "zh", "ja"], env="SUPPORTED_LANGUAGES")
    
    # WebSocket configuration
    websocket_enabled: bool = Field(default=True, env="WEBSOCKET_ENABLED")
    websocket_heartbeat_interval: int = Field(default=30, env="WEBSOCKET_HEARTBEAT_INTERVAL")
    max_websocket_connections: int = Field(default=100, env="MAX_WEBSOCKET_CONNECTIONS")
    websocket_message_max_size: int = Field(default=1024 * 1024, env="WEBSOCKET_MESSAGE_MAX_SIZE")  # 1MB
    
    # HTTP client configuration for async requests
    http_client_timeout: int = Field(default=30, env="HTTP_CLIENT_TIMEOUT")
    http_client_max_connections: int = Field(default=100, env="HTTP_CLIENT_MAX_CONNECTIONS")
    http_client_max_keepalive: int = Field(default=50, env="HTTP_CLIENT_MAX_KEEPALIVE")
    http_client_keepalive_expiry: int = Field(default=30, env="HTTP_CLIENT_KEEPALIVE_EXPIRY")
    
    # Performance monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_endpoint: str = Field(default="/metrics", env="METRICS_ENDPOINT")
    slow_request_threshold: float = Field(default=1.0, env="SLOW_REQUEST_THRESHOLD")
    
    # Database configuration (if needed for future extensions)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=10, env="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @validator("trusted_hosts", pre=True)
    def parse_trusted_hosts(cls, v):
        """Parse trusted hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v
    
    @validator("supported_languages", pre=True)
    def parse_supported_languages(cls, v):
        """Parse supported languages from string or list"""
        if isinstance(v, str):
            return [lang.strip() for lang in v.split(",") if lang.strip()]
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()
    
    @validator("port")
    def validate_port(cls, v):
        """Validate port number"""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    def get_httpx_limits(self) -> Dict[str, Any]:
        """Get httpx client limits configuration"""
        return {
            "max_keepalive_connections": self.http_client_max_keepalive,
            "max_connections": self.http_client_max_connections,
            "keepalive_expiry": self.http_client_keepalive_expiry
        }
    
    def get_httpx_timeout(self) -> Dict[str, Any]:
        """Get httpx client timeout configuration"""
        return {
            "timeout": self.http_client_timeout,
            "connect": 10.0  # Connection timeout
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    def get_uvicorn_config(self) -> Dict[str, Any]:
        """Get optimal uvicorn configuration for async performance"""
        config = {
            "host": self.host,
            "port": self.port,
            "log_level": self.log_level.lower(),
            "access_log": self.enable_access_log,
            "workers": self.workers if self.is_production() else 1,
            "loop": "uvloop" if self.is_production() else "asyncio",
            "http": "httptools" if self.is_production() else "h11",
            "ws": "websockets",
            "lifespan": "on",
            "reload": not self.is_production() and self.debug,
            "use_colors": not self.is_production()
        }
        return config
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "ignore"  # Ignore extra environment variables


# Global configuration instance with caching
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance for optimal performance"""
    return Settings()

# Create global settings instance
settings = get_settings()

async def validate_async_config() -> bool:
    """Validate async configuration and external service connectivity"""
    try:
        # Validate OpenProject URL format
        if not settings.openproject_url.startswith(("http://", "https://")):
            raise ValueError("OpenProject URL must start with http:// or https://")
        
        # Test Redis connection if configured
        if settings.redis_url and settings.cache_enabled:
            try:
                import aioredis
                redis = aioredis.from_url(
                    settings.redis_url,
                    max_connections=settings.cache_max_connections,
                    socket_timeout=settings.cache_timeout
                )
                await redis.ping()
                await redis.close()
            except ImportError:
                raise ValueError("aioredis package required for Redis caching")
            except Exception as e:
                raise ValueError(f"Redis connection failed: {e}")
        
        return True
        
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")

def get_async_config_summary() -> Dict[str, Any]:
    """Get a summary of async configuration for monitoring"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "async_features": {
            "websockets": settings.websocket_enabled,
            "caching": settings.cache_enabled,
            "task_queue": settings.task_queue_enabled,
            "metrics": settings.enable_metrics,
            "rate_limiting": settings.rate_limit_enabled
        },
        "performance_limits": {
            "max_concurrent_requests": settings.max_concurrent_requests,
            "max_websocket_connections": settings.max_websocket_connections,
            "request_timeout": settings.request_timeout,
            "slow_request_threshold": settings.slow_request_threshold
        },
        "connection_pools": {
            "http_max_connections": settings.http_client_max_connections,
            "http_max_keepalive": settings.http_client_max_keepalive,
            "database_pool_size": settings.database_pool_size if settings.database_url else None
        }
    }
