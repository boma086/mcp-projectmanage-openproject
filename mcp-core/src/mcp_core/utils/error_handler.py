"""
错误处理框架 - 提供一致的错误报告和恢复系统

这个模块为所有核心库组件提供标准化的错误处理、上下文管理和恢复机制。
"""
from typing import Any, Dict, Optional, Type, Callable, Union, List, Tuple
from contextlib import contextmanager
import inspect
import functools
import traceback
from datetime import datetime

from mcp_core.shared.exceptions import MCPError
from mcp_core.shared.logger import get_logger


class ErrorContext:
    """错误上下文管理器，提供丰富的错误上下文信息"""
    
    def __init__(self, 
                 operation: str, 
                 component: str, 
                 context_data: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.component = component
        self.context_data = context_data or {}
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.success = False
        self.error: Optional[Exception] = None
        self.stack_trace: Optional[str] = None
    
    def set_error(self, error: Exception):
        """设置错误信息"""
        self.error = error
        self.success = False
        self.end_time = datetime.now()
        self.stack_trace = traceback.format_exc()
    
    def set_success(self):
        """标记操作成功"""
        self.success = True
        self.end_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        duration = (self.end_time - self.start_time).total_seconds() if self.end_time else None
        
        return {
            "operation": self.operation,
            "component": self.component,
            "context_data": self.context_data,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": duration,
            "success": self.success,
            "error_type": self.error.__class__.__name__ if self.error else None,
            "error_message": str(self.error) if self.error else None,
            "stack_trace": self.stack_trace
        }


class ErrorRecoveryStrategy:
    """错误恢复策略基类"""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """判断是否应该重试"""
        return attempt < self.max_retries
    
    def get_retry_delay(self, attempt: int) -> float:
        """获取重试延迟时间"""
        return self.backoff_factor * (2 ** (attempt - 1))
    
    def on_error(self, error: Exception, context: ErrorContext) -> None:
        """错误处理回调"""
        pass


class ExponentialBackoffStrategy(ErrorRecoveryStrategy):
    """指数退避重试策略"""
    
    def __init__(self, max_retries: int = 5, initial_delay: float = 1.0, max_delay: float = 60.0):
        super().__init__(max_retries, 1.0)
        self.initial_delay = initial_delay
        self.max_delay = max_delay
    
    def get_retry_delay(self, attempt: int) -> float:
        """计算指数退避延迟"""
        delay = self.initial_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)


class ErrorHandler:
    """错误处理主类，提供统一的错误处理机制"""
    
    def __init__(self, logger_name: str = "error_handler"):
        self.logger = get_logger(logger_name)
        self.recovery_strategies: Dict[Type[Exception], ErrorRecoveryStrategy] = {}
        self.default_strategy = ErrorRecoveryStrategy()
    
    def register_strategy(self, 
                         error_type: Type[Exception], 
                         strategy: ErrorRecoveryStrategy) -> None:
        """注册错误恢复策略"""
        self.recovery_strategies[error_type] = strategy
    
    def get_strategy(self, error: Exception) -> ErrorRecoveryStrategy:
        """获取适用的恢复策略"""
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                return strategy
        return self.default_strategy
    
    @contextmanager
    def error_context(self, 
                     operation: str, 
                     component: str, 
                     context_data: Optional[Dict[str, Any]] = None):
        """错误上下文管理器"""
        context = ErrorContext(operation, component, context_data)
        
        try:
            yield context
            context.set_success()
            self.logger.info(
                f"Operation '{operation}' completed successfully",
                extra={"context": context.to_dict()}
            )
        except Exception as e:
            context.set_error(e)
            strategy = self.get_strategy(e)
            strategy.on_error(e, context)
            
            self.logger.error(
                f"Operation '{operation}' failed: {str(e)}",
                extra={
                    "context": context.to_dict(),
                    "error_type": e.__class__.__name__,
                    "stack_trace": traceback.format_exc()
                }
            )
            raise
    
    def retry_on_failure(self, 
                        strategy: Optional[ErrorRecoveryStrategy] = None,
                        retryable_errors: Optional[List[Type[Exception]]] = None):
        """重试装饰器"""
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                current_strategy = strategy or self.default_strategy
                retryable = retryable_errors or [Exception]
                
                for attempt in range(1, current_strategy.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        # 检查错误是否可重试
                        if not any(isinstance(e, error_type) for error_type in retryable):
                            raise
                        
                        # 检查是否应该继续重试
                        if not current_strategy.should_retry(e, attempt):
                            raise
                        
                        # 计算延迟并重试
                        delay = current_strategy.get_retry_delay(attempt)
                        self.logger.warning(
                            f"Retry attempt {attempt} for {func.__name__} after error: {str(e)}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt,
                                "max_retries": current_strategy.max_retries,
                                "delay_seconds": delay,
                                "error_type": e.__class__.__name__
                            }
                        )
                        
                        import time
                        time.sleep(delay)
                
                # 所有重试都失败
                raise
            
            return wrapper
        
        return decorator
    
    def handle_error(self, 
                    error: Exception, 
                    operation: str, 
                    component: str, 
                    context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理错误并返回标准化错误响应"""
        context = ErrorContext(operation, component, context_data)
        context.set_error(error)
        
        strategy = self.get_strategy(error)
        strategy.on_error(error, context)
        
        # 记录错误
        self.logger.error(
            f"Error in {operation}: {str(error)}",
            extra={
                "context": context.to_dict(),
                "error_type": error.__class__.__name__,
                "stack_trace": traceback.format_exc()
            }
        )
        
        # 返回标准化错误响应
        if isinstance(error, MCPError):
            return error.to_dict()
        else:
            return {
                "code": -32603,  # Internal error
                "message": f"Internal error: {str(error)}",
                "data": {
                    "operation": operation,
                    "component": component,
                    "error_type": error.__class__.__name__
                }
            }


def create_error_response(code: int, 
                          message: str, 
                          error_type: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """创建标准化的错误响应"""
    response = {
        "code": code,
        "message": message
    }
    
    if error_type:
        response["error_type"] = error_type
    
    if details:
        response["details"] = details
    
    return response


def with_error_handler(operation: str, component: str):
    """错误处理装饰器"""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            handler = ErrorHandler(f"{component}.{func.__name__}")
            
            # 从函数签名中提取上下文数据
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            context_data = {
                "function": func.__name__,
                "module": func.__module__,
                "args": {k: str(v) for k, v in bound_args.arguments.items() 
                         if not k.startswith('_') and not isinstance(v, (str, int, float, bool, type(None)))}
            }
            
            with handler.error_context(operation, component, context_data):
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


# 全局错误处理器实例
default_error_handler = ErrorHandler()

# 预配置的恢复策略
NETWORK_RETRY_STRATEGY = ExponentialBackoffStrategy(
    max_retries=3, 
    initial_delay=1.0, 
    max_delay=10.0
)

DATABASE_RETRY_STRATEGY = ExponentialBackoffStrategy(
    max_retries=5, 
    initial_delay=0.5, 
    max_delay=30.0
)

# 注册默认策略
from mcp_core.shared.exceptions import (
    OpenProjectError, AuthenticationError, AuthorizationError,
    NotFoundError, TimeoutError, RateLimitError
)

default_error_handler.register_strategy(TimeoutError, NETWORK_RETRY_STRATEGY)
default_error_handler.register_strategy(RateLimitError, NETWORK_RETRY_STRATEGY)
default_error_handler.register_strategy(OpenProjectError, NETWORK_RETRY_STRATEGY)