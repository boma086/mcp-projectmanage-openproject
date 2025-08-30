"""
工具模块 - 提供各种实用功能和错误处理框架

这个模块包含通用的工具函数和错误处理机制，供所有核心库组件使用。
"""

from .error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorRecoveryStrategy,
    ExponentialBackoffStrategy,
    with_error_handler,
    create_error_response,
    default_error_handler,
    NETWORK_RETRY_STRATEGY,
    DATABASE_RETRY_STRATEGY
)

__all__ = [
    'ErrorHandler',
    'ErrorContext', 
    'ErrorRecoveryStrategy',
    'ExponentialBackoffStrategy',
    'with_error_handler',
    'create_error_response',
    'default_error_handler',
    'NETWORK_RETRY_STRATEGY',
    'DATABASE_RETRY_STRATEGY'
]