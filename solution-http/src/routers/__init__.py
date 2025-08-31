"""
HTTP Solution Routers Package
FastAPI router modules for organizing REST API endpoints
"""

from .projects import router as projects_router
from .work_packages import router as work_packages_router
from .users import router as users_router

__all__ = [
    "projects_router",
    "work_packages_router", 
    "users_router"
]