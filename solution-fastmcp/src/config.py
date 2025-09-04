"""
Configuration Module for FastMCP Solution

This module provides configuration management for the FastMCP solution.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings aligned with deployment standard"""
    
    # Application Configuration
    app_name: str = Field(default="fastmcp-mcp", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, testing, production)")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8030, description="Server port")
    sse_port: int = Field(default=8031, description="SSE port")
    
    # OpenProject Configuration
    openproject_url: str = Field(..., description="OpenProject URL")
    openproject_api_key: str = Field(..., description="OpenProject API key")
    openproject_timeout: int = Field(default=30, description="OpenProject timeout in seconds")
    openproject_max_retries: int = Field(default=3, description="OpenProject max retries")
    
    # FastMCP Specific Configuration
    max_sessions: int = Field(default=1000, description="Maximum MCP sessions")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_endpoint: str = Field(default="/metrics", description="Metrics endpoint")
    log_level: str = Field(default="INFO", description="Log level")
    structured_logging: bool = Field(default=True, description="Enable structured logging")
    correlation_ids: bool = Field(default=True, description="Enable correlation IDs")
    
    # Health Check Configuration
    health_check_enabled: bool = Field(default=True, description="Enable health checks")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    deep_health_check_interval: int = Field(default=300, description="Deep health check interval in seconds")
    health_check_timeout: int = Field(default=10, description="Health check timeout in seconds")
    
    # MCP Configuration
    mcp_protocol_version: str = Field(default="2024-11-05", description="MCP protocol version")
    
    # SSE Configuration
    sse_enabled: bool = Field(default=True, description="Enable SSE support")
    
    # Performance Configuration
    max_concurrent_requests: int = Field(default=500, description="Maximum concurrent requests")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    max_request_size: int = Field(default=10485760, description="Maximum request size in bytes")
    
    # Security Configuration
    cors_allow_origins: str = Field(default="http://localhost,http://127.0.0.1", description="CORS allowed origins")
    trusted_hosts: str = Field(default="localhost,127.0.0.1", description="Trusted hosts")
    
    # Cache Configuration
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    enable_cache: bool = Field(default=True, description="Enable caching")
    redis_url: str = Field(default="redis://redis:6379/0", description="Redis URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings"""
    return Settings()


def validate_settings(settings: Settings) -> bool:
    """Validate application settings"""
    errors = []
    
    # Validate OpenProject configuration
    if not settings.openproject_url:
        errors.append("openproject_url is required")
    
    if not settings.openproject_api_key:
        errors.append("openproject_api_key is required")
    
    # Validate port ranges
    if not (1 <= settings.port <= 65535):
        errors.append("port must be between 1 and 65535")
    
    if not (1 <= settings.sse_port <= 65535):
        errors.append("sse_port must be between 1 and 65535")
    
    # Validate timeout values
    if settings.health_check_timeout <= 0:
        errors.append("health_check_timeout must be positive")
    
    if settings.request_timeout <= 0:
        errors.append("request_timeout must be positive")
    
    if settings.session_timeout <= 0:
        errors.append("session_timeout must be positive")
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if settings.log_level not in valid_log_levels:
        errors.append(f"log_level must be one of {valid_log_levels}")
    
    # Validate environment
    valid_environments = ["development", "testing", "production"]
    if settings.environment not in valid_environments:
        errors.append(f"environment must be one of {valid_environments}")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    return True


def get_environment_config() -> dict:
    """Get environment-specific configuration"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    configs = {
        "development": {
            "debug": True,
            "log_level": "DEBUG",
            "enable_metrics": True,
            "health_check_interval": 10,
            "structured_logging": False,
            "max_concurrent_requests": 100,
        },
        "production": {
            "debug": False,
            "log_level": "INFO",
            "enable_metrics": True,
            "health_check_interval": 30,
            "structured_logging": True,
            "max_concurrent_requests": 500,
        },
        "testing": {
            "debug": True,
            "log_level": "DEBUG",
            "enable_metrics": True,
            "health_check_interval": 5,
            "structured_logging": False,
            "max_concurrent_requests": 50,
        }
    }
    
    return configs.get(env, configs["development"])
