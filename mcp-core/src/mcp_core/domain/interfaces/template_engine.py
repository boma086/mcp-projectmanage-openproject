"""
模板引擎接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ITemplateEngine(ABC):
    """模板引擎接口"""
    
    @abstractmethod
    async def list_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板列表"""
        pass
    
    @abstractmethod
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取指定模板"""
        pass
    
    @abstractmethod
    async def save_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """保存模板"""
        pass
    
    @abstractmethod
    async def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        pass
    
    @abstractmethod
    async def render_template(self, template_id: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        pass
    
    @abstractmethod
    async def get_template_variables(self, template_id: str) -> List[Dict[str, Any]]:
        """获取模板中使用的变量"""
        pass
    
    @abstractmethod
    async def validate_template(self, template_data: Dict[str, Any]) -> bool:
        """验证模板格式"""
        pass
    
    @abstractmethod
    async def create_default_templates(self) -> None:
        """创建默认模板"""
        pass
