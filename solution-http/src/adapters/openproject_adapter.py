"""
OpenProject 适配器 - HTTP Solution 包装器
使用核心库的异步适配器，为 HTTP 解决方案提供同步接口兼容性
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

# 导入核心库组件
from mcp_core.adapters.openproject import OpenProjectAdapter as CoreOpenProjectAdapter
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.domain.models import Project, WorkPackage, User, Report
from mcp_core.shared.exceptions import OpenProjectError, AuthenticationError, NotFoundError
from mcp_core.shared.config import get_global_config
from mcp_core.shared.logger import get_logger

logger = get_logger("http.adapter")


class HTTPOpenProjectClient(IOpenProjectClient):
    """
    HTTP 解决方案的 OpenProject 客户端
    
    这是一个包装器，将核心库的异步适配器封装为同步接口，
    以便在 FastAPI 的同步模式下使用。
    
    注意：此实现主要用于向后兼容，推荐使用 dependencies.py 中的
    SyncAsyncAdapter 来获得更好的性能和错误处理。
    """
    
    def __init__(self, url: str = None, api_key: str = None):
        """
        初始化 HTTP 客户端
        
        Args:
            url: OpenProject 服务器 URL
            api_key: API 密钥
        """
        logger.info("初始化 HTTP OpenProject 客户端")
        
        # 使用核心库的适配器作为底层实现
        self._core_adapter = CoreOpenProjectAdapter(url=url, api_key=api_key)
    
    async def initialize(self) -> None:
        """初始化客户端"""
        logger.debug("初始化核心适配器")
        await self._core_adapter.initialize()
    
    async def cleanup(self) -> None:
        """清理资源"""
        logger.debug("清理核心适配器资源")
        await self._core_adapter.cleanup()
    
    async def check_connection(self) -> bool:
        """检查连接状态"""
        return await self._core_adapter.check_connection()
    
    # ==================== 项目相关方法 ====================
    
    async def get_projects(self) -> List[Project]:
        """获取所有项目"""
        return await self._core_adapter.get_projects()
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取单个项目"""
        return await self._core_adapter.get_project(project_id)
    
    # ==================== 工作包相关方法 ====================
    
    async def get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """获取工作包列表"""
        return await self._core_adapter.get_work_packages(project_id)
    
    async def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """获取单个工作包"""
        return await self._core_adapter.get_work_package(work_package_id)
    
    async def create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """创建工作包"""
        return await self._core_adapter.create_work_package(work_package_data)
    
    async def update_work_package(self, work_package_id: str, 
                                work_package_data: Dict[str, Any]) -> WorkPackage:
        """更新工作包"""
        return await self._core_adapter.update_work_package(work_package_id, work_package_data)
    
    # ==================== 用户相关方法 ====================
    
    async def get_users(self) -> List[User]:
        """获取用户列表"""
        return await self._core_adapter.get_users()
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取单个用户"""
        return await self._core_adapter.get_user(user_id)
    
    # ==================== 报告生成方法 ====================
    
    async def generate_weekly_report(self, project_id: str, 
                                   start_date: str, end_date: str) -> Report:
        """生成周报"""
        return await self._core_adapter.generate_weekly_report(project_id, start_date, end_date)
    
    async def generate_monthly_report(self, project_id: str, 
                                    year: int, month: int) -> Report:
        """生成月报"""
        return await self._core_adapter.generate_monthly_report(project_id, year, month)
    
    async def assess_project_risks(self, project_id: str) -> Report:
        """评估项目风险"""
        return await self._core_adapter.assess_project_risks(project_id)
    
    # ==================== 配置方法 ====================
    
    def get_base_url(self) -> str:
        """获取基础 URL"""
        return self._core_adapter.get_base_url()
    
    def get_api_key(self) -> str:
        """获取 API 密钥"""
        return self._core_adapter.get_api_key()
