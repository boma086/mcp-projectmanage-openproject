"""
适配器模块 - 外部系统集成接口

该模块提供统一的适配器接口，用于与外部系统（如 OpenProject）进行集成。
所有适配器实现都应遵循相同的模式和错误处理机制。
"""

from .openproject import OpenProjectAdapter

__all__ = [
    'OpenProjectAdapter',
]