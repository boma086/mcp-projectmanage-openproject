"""
OpenProject 客户端接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from mcp_core.domain.models import Project, WorkPackage, User, Report


class IOpenProjectClient(ABC):
    """OpenProject 客户端接口"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化客户端"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass
    
    @abstractmethod
    async def check_connection(self) -> bool:
        """检查连接状态"""
        pass
    
    # 项目相关方法
    @abstractmethod
    async def get_projects(self) -> List[Project]:
        """获取所有项目"""
        pass
    
    @abstractmethod
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取单个项目"""
        pass
    
    # 工作包相关方法
    @abstractmethod
    async def get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """获取工作包列表"""
        pass
    
    @abstractmethod
    async def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """获取单个工作包"""
        pass
    
    @abstractmethod
    async def create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """创建工作包"""
        pass
    
    @abstractmethod
    async def update_work_package(self, work_package_id: str, 
                                work_package_data: Dict[str, Any]) -> WorkPackage:
        """更新工作包"""
        pass
    
    # 用户相关方法
    @abstractmethod
    async def get_users(self) -> List[User]:
        """获取用户列表"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取单个用户"""
        pass
    
    # 报告生成方法
    @abstractmethod
    async def generate_weekly_report(self, project_id: str, 
                                   start_date: str, end_date: str) -> Report:
        """生成周报"""
        pass
    
    @abstractmethod
    async def generate_monthly_report(self, project_id: str, 
                                    year: int, month: int) -> Report:
        """生成月报"""
        pass
    
    @abstractmethod
    async def assess_project_risks(self, project_id: str) -> Report:
        """评估项目风险"""
        pass
    
    # 配置方法
    @abstractmethod
    def get_base_url(self) -> str:
        """获取基础 URL"""
        pass
    
    @abstractmethod
    def get_api_key(self) -> str:
        """获取 API 密钥"""
        pass
