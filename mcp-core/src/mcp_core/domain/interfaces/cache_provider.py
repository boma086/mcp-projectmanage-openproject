"""
缓存提供者接口定义
"""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class ICacheProvider(ABC):
    """缓存提供者接口"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """清空所有缓存"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """获取键的剩余生存时间"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """清理过期的缓存项"""
        pass
