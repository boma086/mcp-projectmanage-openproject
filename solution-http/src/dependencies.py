"""
HTTP Solution Dependency Injection
使用 FastAPI 的依赖注入系统管理服务生命周期
"""

import asyncio
import threading
from typing import Optional, Generator
from functools import lru_cache

from fastapi import Depends, HTTPException
from mcp_core.adapters.openproject import OpenProjectAdapter
from mcp_core.application.mcp.handler import MCPHandler
from mcp_core.shared.exceptions import OpenProjectError, AuthenticationError
from mcp_core.shared.logger import get_logger
from .config import get_http_config, HTTPSolutionConfig

logger = get_logger("http.dependencies")

# 全局实例缓存
_openproject_adapter: Optional[OpenProjectAdapter] = None
_mcp_handler: Optional[MCPHandler] = None
_adapter_lock = threading.Lock()

class SyncAsyncAdapter:
    """
    同步-异步适配器，用于在同步 FastAPI 端点中调用异步方法
    避免在每个端点重复创建事件循环的开销
    """
    
    def __init__(self, async_client: OpenProjectAdapter):
        self.async_client = async_client
        self._loop = None
        self._thread = None
        self._setup_async_context()
    
    def _setup_async_context(self):
        """设置异步上下文"""
        try:
            # 尝试获取当前事件循环
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行中的循环，创建新的
            self._loop = None
    
    def _run_async(self, coro):
        """运行异步协程"""
        if self._loop and self._loop.is_running():
            # 如果有运行中的循环，在新线程中运行
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            # 没有运行中的循环，直接运行
            return asyncio.run(coro)
    
    # 封装常用的异步方法为同步接口
    def get_projects(self):
        return self._run_async(self.async_client.get_projects())
    
    def get_project(self, project_id: str):
        return self._run_async(self.async_client.get_project(project_id))
    
    def get_work_packages(self, project_id: Optional[str] = None):
        return self._run_async(self.async_client.get_work_packages(project_id))
    
    def get_work_package(self, work_package_id: str):
        return self._run_async(self.async_client.get_work_package(work_package_id))
    
    def get_users(self):
        return self._run_async(self.async_client.get_users())
    
    def get_user(self, user_id: str):
        return self._run_async(self.async_client.get_user(user_id))
    
    def check_connection(self):
        return self._run_async(self.async_client.check_connection())
    
    def generate_weekly_report(self, project_id: str, start_date: str, end_date: str):
        return self._run_async(self.async_client.generate_weekly_report(project_id, start_date, end_date))
    
    def generate_monthly_report(self, project_id: str, year: int, month: int):
        return self._run_async(self.async_client.generate_monthly_report(project_id, year, month))
    
    def assess_project_risks(self, project_id: str):
        return self._run_async(self.async_client.assess_project_risks(project_id))


@lru_cache()
def get_config() -> HTTPSolutionConfig:
    """获取配置依赖"""
    return get_http_config()


def get_openproject_adapter() -> SyncAsyncAdapter:
    """
    获取 OpenProject 适配器依赖
    使用线程安全的单例模式，确保连接复用
    """
    global _openproject_adapter
    
    with _adapter_lock:
        if _openproject_adapter is None:
            try:
                config = get_config()
                logger.info("创建新的 OpenProject 适配器实例")
                
                # 创建核心库的异步适配器
                _openproject_adapter = OpenProjectAdapter(
                    url=config.openproject_url,
                    api_key=config.openproject_api_key
                )
                
                # 初始化适配器
                asyncio.run(_openproject_adapter.initialize())
                
                logger.info(f"OpenProject 适配器初始化成功: {config.openproject_url}")
                
            except Exception as e:
                logger.error(f"OpenProject 适配器初始化失败: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"Failed to initialize OpenProject adapter: {str(e)}"
                )
    
    # 返回同步适配器包装器
    return SyncAsyncAdapter(_openproject_adapter)


def get_mcp_handler(
    openproject_adapter: SyncAsyncAdapter = Depends(get_openproject_adapter)
) -> MCPHandler:
    """
    获取 MCP 处理器依赖
    依赖于 OpenProject 适配器
    """
    global _mcp_handler
    
    if _mcp_handler is None:
        try:
            logger.info("创建新的 MCP 处理器实例")
            # MCP 处理器需要原始的异步适配器
            _mcp_handler = MCPHandler(openproject_adapter.async_client)
            logger.info("MCP 处理器创建成功")
            
        except Exception as e:
            logger.error(f"MCP 处理器创建失败: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"Failed to create MCP handler: {str(e)}"
            )
    
    return _mcp_handler


def validate_openproject_connection(
    adapter: SyncAsyncAdapter = Depends(get_openproject_adapter)
) -> SyncAsyncAdapter:
    """
    验证 OpenProject 连接的依赖
    在需要确保连接正常的端点中使用
    """
    try:
        is_connected = adapter.check_connection()
        if not is_connected:
            logger.warning("OpenProject 连接验证失败")
            raise HTTPException(
                status_code=503,
                detail="OpenProject server is not accessible"
            )
        
        logger.debug("OpenProject 连接验证成功")
        return adapter
        
    except AuthenticationError as e:
        logger.error(f"OpenProject 认证失败: {e}")
        raise HTTPException(
            status_code=401,
            detail="OpenProject authentication failed. Please check API key."
        )
    except OpenProjectError as e:
        logger.error(f"OpenProject 连接错误: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"OpenProject server error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"连接验证时发生未知错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Connection validation failed: {str(e)}"
        )


def cleanup_dependencies():
    """
    清理依赖资源
    在应用关闭时调用
    """
    global _openproject_adapter, _mcp_handler
    
    logger.info("清理依赖资源...")
    
    try:
        if _openproject_adapter:
            asyncio.run(_openproject_adapter.cleanup())
            _openproject_adapter = None
            logger.info("OpenProject 适配器已清理")
        
        if _mcp_handler:
            _mcp_handler = None
            logger.info("MCP 处理器已清理")
            
    except Exception as e:
        logger.error(f"清理依赖资源时出错: {e}")


# 依赖注入快捷方式
# 用于常见的依赖组合

def get_validated_adapter() -> SyncAsyncAdapter:
    """获取经过连接验证的适配器 - 快捷方式"""
    return Depends(validate_openproject_connection)


def get_basic_adapter() -> SyncAsyncAdapter:
    """获取基本适配器（不验证连接） - 快捷方式"""
    return Depends(get_openproject_adapter)


def get_handler_with_adapter() -> tuple[MCPHandler, SyncAsyncAdapter]:
    """获取 MCP 处理器和适配器 - 快捷方式"""
    def _get_handler_with_adapter(
        handler: MCPHandler = Depends(get_mcp_handler),
        adapter: SyncAsyncAdapter = Depends(get_openproject_adapter)
    ) -> tuple[MCPHandler, SyncAsyncAdapter]:
        return handler, adapter
    
    return Depends(_get_handler_with_adapter)