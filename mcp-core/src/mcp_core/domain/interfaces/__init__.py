"""
领域接口定义

定义核心业务接口，供不同实现方案使用
"""

from .openproject_client import IOpenProjectClient
from .template_engine import ITemplateEngine
from .cache_provider import ICacheProvider

__all__ = [
    "IOpenProjectClient",
    "ITemplateEngine", 
    "ICacheProvider",
]
