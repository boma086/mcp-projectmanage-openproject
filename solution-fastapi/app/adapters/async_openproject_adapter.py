"""
Async OpenProject Adapter with True Async Support and Connection Pooling

This module provides a fully async implementation of the OpenProject client
using httpx with connection pooling for optimal performance in high-concurrency
scenarios.
"""
import asyncio
import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.domain.models import Project, WorkPackage, User, Report
from mcp_core.domain.services import ReportGeneratorService
from mcp_core.shared.exceptions import OpenProjectError, AuthenticationError, NotFoundError
from mcp_core.shared.config import get_global_config


class AsyncOpenProjectClient(IOpenProjectClient):
    """True async OpenProject client implementation with httpx and connection pooling."""

    def __init__(self, url: str = None, api_key: str = None, http_client: httpx.AsyncClient = None):
        config = get_global_config()
        self.base_url = (url or config.openproject_url).rstrip('/')
        self.api_key = api_key or config.openproject_api_key
        self._http_client = http_client
        
        # Initialize report generator service
        self.report_generator = ReportGeneratorService(self)
    
    async def initialize(self) -> None:
        """Initialize the client with connection pooling.
        
        If no HTTP client was provided during initialization, create a dedicated
        one with optimized connection pooling settings.
        """
        if self._http_client is None:
            # Create dedicated HTTP client with optimized pooling
            self._http_client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=50,
                    keepalive_expiry=30
                ),
                timeout=httpx.Timeout(30.0, connect=10.0)
            )

    async def cleanup(self) -> None:
        """Cleanup resources and close HTTP client connections.
        
        This ensures proper connection pool cleanup to prevent resource leaks.
        """
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    async def check_connection(self) -> bool:
        """Check connection status to OpenProject API.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            await self._make_request("/")
            return True
        except Exception:
            return False
    
    async def _make_request(self, endpoint: str, method: str = 'GET',
                           params: Optional[Dict] = None,
                           json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make async HTTP request to OpenProject API with connection pooling.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, PATCH, PUT, DELETE)
            params: Query parameters
            json_data: Request JSON data
            
        Returns:
            Dict[str, Any]: Response JSON data
            
        Raises:
            OpenProjectError: For general API errors
            AuthenticationError: For authentication failures
            NotFoundError: For 404 responses
        """
        if self._http_client is None:
            raise OpenProjectError("HTTP client not initialized")
        
        url = f"{self.base_url}/api/v3{endpoint}"
        
        # Prepare request headers and auth
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        auth = ('apikey', self.api_key)
        
        try:
            # Make async HTTP request using connection pool
            response = await self._http_client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                auth=auth,
                timeout=30.0
            )
            
            # Handle response errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key or authentication failed")
            elif response.status_code == 403:
                raise AuthenticationError("Access forbidden")
            elif response.status_code == 404:
                raise NotFoundError("Resource not found")
            elif response.status_code >= 400:
                error_msg = f"API request failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'message' in error_data:
                        error_msg += f": {error_data['message']}"
                except:
                    pass
                raise OpenProjectError(error_msg, status_code=response.status_code)

            return response.json()

        except httpx.RequestError as e:
            raise OpenProjectError(f"Request failed: {str(e)}")
        except httpx.TimeoutException as e:
            raise OpenProjectError(f"Request timeout: {str(e)}")
        except Exception as e:
            if isinstance(e, (OpenProjectError, AuthenticationError, NotFoundError)):
                raise
            raise OpenProjectError(f"Unexpected error: {str(e)}")
    

    # 公开接口方法实现（委托给私有方法）
    async def get_projects(self) -> List[Project]:
        """获取所有项目"""
        return await self._get_projects()
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取单个项目"""
        return await self._get_project(project_id)
    
    async def get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """获取工作包列表"""
        return await self._get_work_packages(project_id)
    
    async def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """获取单个工作包"""
        return await self._get_work_package(work_package_id)
    
    async def create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """创建工作包"""
        return await self._create_work_package(work_package_data)
    
    async def update_work_package(self, work_package_id: str, 
                                work_package_data: Dict[str, Any]) -> WorkPackage:
        """更新工作包"""
        return await self._update_work_package(work_package_id, work_package_data)
    
    async def get_users(self) -> List[User]:
        """获取用户列表"""
        return await self._get_users()
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取单个用户"""
        return await self._get_user(user_id)

    # 以下为 OpenProject 原始 API，仅供 MCP 业务内部调用，不对外暴露
    async def _get_projects(self) -> List[Project]:
        """(内部) 获取所有项目"""
        # ...原 get_projects 代码...
        data = await self._make_request("/projects")
        projects = []
        for item in data.get('_embedded', {}).get('elements', []):
            project = Project(
                id=str(item['id']),
                name=item['name'],
                identifier=item['identifier'],
                description=item.get('description', {}).get('raw', ''),
                created_at=self._parse_datetime(item.get('createdAt')),
                updated_at=self._parse_datetime(item.get('updatedAt')),
                status=item.get('status', {}).get('name') if item.get('status') else None
            )
            projects.append(project)
        return projects

    async def _get_project(self, project_id: str) -> Optional[Project]:
        """(内部) 获取单个项目"""
        try:
            data = await self._make_request(f"/projects/{project_id}")
            return Project(
                id=str(data['id']),
                name=data['name'],
                identifier=data['identifier'],
                description=data.get('description', {}).get('raw', ''),
                created_at=self._parse_datetime(data.get('createdAt')),
                updated_at=self._parse_datetime(data.get('updatedAt')),
                status=data.get('status', {}).get('name') if data.get('status') else None
            )
        except NotFoundError:
            return None

    async def _get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """(内部) 获取工作包列表"""
        endpoint = "/work_packages"
        params = {}
        if project_id:
            params['filters'] = f'[{{"project":{{"operator":"=","values":["{project_id}"]}}}}]'
        data = await self._make_request(endpoint, params=params)
        work_packages = []
        for item in data.get('_embedded', {}).get('elements', []):
            wp = WorkPackage(
                id=str(item['id']),
                subject=item['subject'],
                description=item.get('description', {}).get('raw', ''),
                status=item.get('status', {}).get('name') if item.get('status') else None,
                type=item.get('type', {}).get('name') if item.get('type') else None,
                priority=item.get('priority', {}).get('name') if item.get('priority') else None,
                assigned_to=item.get('assignee', {}).get('name') if item.get('assignee') else None,
                created_at=self._parse_datetime(item.get('createdAt')),
                updated_at=self._parse_datetime(item.get('updatedAt')),
                start_date=self._parse_date(item.get('startDate')),
                due_date=self._parse_date(item.get('dueDate')),
                progress=item.get('percentageDone'),
                project_id=project_id
            )
            work_packages.append(wp)
        return work_packages

    async def _get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """(内部) 获取单个工作包"""
        try:
            data = await self._make_request(f"/work_packages/{work_package_id}")
            return WorkPackage(
                id=str(data['id']),
                subject=data['subject'],
                description=data.get('description', {}).get('raw', ''),
                status=data.get('status', {}).get('name') if data.get('status') else None,
                type=data.get('type', {}).get('name') if data.get('type') else None,
                priority=data.get('priority', {}).get('name') if data.get('priority') else None,
                assigned_to=data.get('assignee', {}).get('name') if data.get('assignee') else None,
                created_at=self._parse_datetime(data.get('createdAt')),
                updated_at=self._parse_datetime(data.get('updatedAt')),
                start_date=self._parse_date(data.get('startDate')),
                due_date=self._parse_date(data.get('dueDate')),
                progress=data.get('percentageDone')
            )
        except NotFoundError:
            return None

    async def _get_users(self) -> List[User]:
        """(内部) 获取用户列表"""
        data = await self._make_request("/users")
        users = []
        for item in data.get('_embedded', {}).get('elements', []):
            user = User(
                id=str(item['id']),
                name=item['name'],
                email=item.get('email'),
                login=item.get('login'),
                created_at=self._parse_datetime(item.get('createdAt')),
                updated_at=self._parse_datetime(item.get('updatedAt')),
                status=item.get('status')
            )
            users.append(user)
        return users

    async def _get_user(self, user_id: str) -> Optional[User]:
        """(内部) 获取单个用户"""
        try:
            data = await self._make_request(f"/users/{user_id}")
            return User(
                id=str(data['id']),
                name=data['name'],
                email=data.get('email'),
                login=data.get('login'),
                created_at=self._parse_datetime(data.get('createdAt')),
                updated_at=self._parse_datetime(data.get('updatedAt')),
                status=data.get('status')
            )
        except NotFoundError:
            return None

    async def _create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """(内部) 创建工作包"""
        data = await self._make_request("/work_packages", method="POST", json_data=work_package_data)
        return WorkPackage(
            id=str(data['id']),
            subject=data['subject'],
            description=data.get('description', {}).get('raw', ''),
            status=data.get('status', {}).get('name') if data.get('status') else None,
            type=data.get('type', {}).get('name') if data.get('type') else None,
            priority=data.get('priority', {}).get('name') if data.get('priority') else None,
            assigned_to=data.get('assignee', {}).get('name') if data.get('assignee') else None,
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt')),
            start_date=self._parse_date(data.get('startDate')),
            due_date=self._parse_date(data.get('dueDate')),
            progress=data.get('percentageDone')
        )

    async def _update_work_package(self, work_package_id: str, 
                                 work_package_data: Dict[str, Any]) -> WorkPackage:
        """(内部) 更新工作包"""
        data = await self._make_request(f"/work_packages/{work_package_id}", 
                                      method="PATCH", json_data=work_package_data)
        return WorkPackage(
            id=str(data['id']),
            subject=data['subject'],
            description=data.get('description', {}).get('raw', ''),
            status=data.get('status', {}).get('name') if data.get('status') else None,
            type=data.get('type', {}).get('name') if data.get('type') else None,
            priority=data.get('priority', {}).get('name') if data.get('priority') else None,
            assigned_to=data.get('assignee', {}).get('name') if data.get('assignee') else None,
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt')),
            start_date=self._parse_date(data.get('startDate')),
            due_date=self._parse_date(data.get('dueDate')),
            progress=data.get('percentageDone')
        )
    
    # 报告生成方法 - 委托给报告生成服务
    async def generate_weekly_report(self, project_id: str, 
                                   start_date: str, end_date: str) -> Report:
        """生成周报"""
        return await self.report_generator.generate_weekly_report(project_id, start_date, end_date)
    
    async def generate_monthly_report(self, project_id: str, 
                                    year: int, month: int) -> Report:
        """生成月报"""
        return await self.report_generator.generate_monthly_report(project_id, year, month)
    
    async def generate_enhanced_weekly_report(self, project_id: str, 
                                            start_date: str, end_date: str,
                                            language: str = "ja") -> Report:
        """生成增强型周报"""
        try:
            from app.services.enhanced_report_generator import EnhancedReportGeneratorService, ReportLanguage
            
            enhanced_generator = EnhancedReportGeneratorService(self)
            language_map = {
                "zh": ReportLanguage.CHINESE,
                "ja": ReportLanguage.JAPANESE,
                "en": ReportLanguage.ENGLISH
            }
            report_language = language_map.get(language.lower(), ReportLanguage.JAPANESE)
            
            return await enhanced_generator.generate_enhanced_weekly_report(
                project_id, start_date, end_date, report_language
            )
        except ImportError:
            # 回退到基本报告
            return await self.generate_weekly_report(project_id, start_date, end_date)
    
    async def generate_enhanced_monthly_report(self, project_id: str, year: int, month: int,
                                             language: str = "ja") -> Report:
        """生成增强型月报"""
        try:
            from app.services.enhanced_report_generator import EnhancedReportGeneratorService, ReportLanguage
            
            enhanced_generator = EnhancedReportGeneratorService(self)
            language_map = {
                "zh": ReportLanguage.CHINESE,
                "ja": ReportLanguage.JAPANESE,
                "en": ReportLanguage.ENGLISH
            }
            report_language = language_map.get(language.lower(), ReportLanguage.JAPANESE)
            
            return await enhanced_generator.generate_enhanced_monthly_report(
                project_id, year, month, report_language
            )
        except ImportError:
            # 回退到基本报告
            return await self.generate_monthly_report(project_id, year, month)
    
    async def assess_project_risks(self, project_id: str) -> Report:
        """评估项目风险"""
        project = await self.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")
        
        return Report(
            title=f"{project.name} 风险评估报告",
            project_name=project.name,
            period=f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            summary="风险评估功能正在开发中..."
        )
    
    def get_base_url(self) -> str:
        """获取基础 URL"""
        return self.base_url
    
    def get_api_key(self) -> str:
        """获取 API 密钥"""
        return self.api_key
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期时间字符串"""
        if not date_str:
            return None
        
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except (ValueError, AttributeError):
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, AttributeError):
            return None
