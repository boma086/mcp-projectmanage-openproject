"""
OpenProject Service Implementation

This service implements the IOpenProjectClient interface using the async OpenProject adapter
with connection pooling and performance optimizations.
"""
import httpx
from typing import List, Optional, Dict, Any
from mcp_core.domain.interfaces.openproject_client import IOpenProjectClient
from mcp_core.domain.models import Project, WorkPackage, User, Report
from app.adapters.async_openproject_adapter import AsyncOpenProjectClient
from app.core.config import settings


class OpenProjectService(IOpenProjectClient):
    """OpenProject service implementation with async connection pooling"""
    
    def __init__(self, url: str, api_key: str, http_client: Optional[httpx.AsyncClient] = None):
        self.url = url
        self.api_key = api_key
        self._http_client = http_client
        self._client: Optional[AsyncOpenProjectClient] = None
    
    async def initialize(self) -> None:
        """Initialize the OpenProject client with connection pooling"""
        if self._client is None:
            self._client = AsyncOpenProjectClient(
                url=self.url,
                api_key=self.api_key,
                http_client=self._http_client
            )
            await self._client.initialize()
    
    async def cleanup(self) -> None:
        """Cleanup resources"""
        if self._client:
            await self._client.cleanup()
            self._client = None
    
    async def check_connection(self) -> bool:
        """Check connection to OpenProject server"""
        if not self._client:
            await self.initialize()
        return await self._client.check_connection()
    
    # Project methods
    async def get_projects(self) -> List[Project]:
        """Get all projects"""
        if not self._client:
            await self.initialize()
        return await self._client.get_projects()
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get single project"""
        if not self._client:
            await self.initialize()
        return await self._client.get_project(project_id)
    
    # Work package methods
    async def get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """Get work packages"""
        if not self._client:
            await self.initialize()
        return await self._client.get_work_packages(project_id)
    
    async def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """Get single work package"""
        if not self._client:
            await self.initialize()
        return await self._client.get_work_package(work_package_id)
    
    async def create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """Create work package"""
        if not self._client:
            await self.initialize()
        return await self._client.create_work_package(work_package_data)
    
    async def update_work_package(self, work_package_id: str, 
                                work_package_data: Dict[str, Any]) -> WorkPackage:
        """Update work package"""
        if not self._client:
            await self.initialize()
        return await self._client.update_work_package(work_package_id, work_package_data)
    
    # User methods
    async def get_users(self) -> List[User]:
        """Get users"""
        if not self._client:
            await self.initialize()
        return await self._client.get_users()
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get single user"""
        if not self._client:
            await self.initialize()
        return await self._client.get_user(user_id)
    
    # Report generation methods
    async def generate_weekly_report(self, project_id: str, 
                                   start_date: str, end_date: str) -> Report:
        """Generate weekly report"""
        if not self._client:
            await self.initialize()
        return await self._client.generate_weekly_report(project_id, start_date, end_date)
    
    async def generate_monthly_report(self, project_id: str, 
                                    year: int, month: int) -> Report:
        """Generate monthly report"""
        if not self._client:
            await self.initialize()
        return await self._client.generate_monthly_report(project_id, year, month)
    
    async def assess_project_risks(self, project_id: str) -> Report:
        """Assess project risks"""
        if not self._client:
            await self.initialize()
        return await self._client.assess_project_risks(project_id)
    
    # Configuration methods
    def get_base_url(self) -> str:
        """Get base URL"""
        return self.url
    
    def get_api_key(self) -> str:
        """Get API key"""
        return self.api_key