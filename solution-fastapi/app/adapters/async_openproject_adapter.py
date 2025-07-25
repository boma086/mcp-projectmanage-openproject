"""
异步 OpenProject 适配器 - 使用核心库实现
"""
import asyncio
import requests
from typing import List, Optional, Dict, Any
from datetime import datetime

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.domain.models import Project, WorkPackage, User, Report
from mcp_core.domain.services import ReportGeneratorService
from mcp_core.shared.exceptions import OpenProjectError, AuthenticationError, NotFoundError
from mcp_core.shared.config import get_global_config


class AsyncOpenProjectClient(IOpenProjectClient):
    """基于混合方案的异步 OpenProject 客户端实现（requests + 线程池）"""

    def __init__(self, url: str = None, api_key: str = None):
        config = get_global_config()
        self.base_url = (url or config.openproject_url).rstrip('/')
        self.api_key = api_key or config.openproject_api_key
        
        # 初始化报告生成服务
        self.report_generator = ReportGeneratorService(self)
    
    async def initialize(self) -> None:
        """初始化客户端（混合方案不需要初始化）"""
        pass

    async def cleanup(self) -> None:
        """清理资源（混合方案不需要清理）"""
        pass
    
    async def check_connection(self) -> bool:
        """检查连接状态"""
        try:
            await self.initialize()
            response = await self.client.get(f"{self.base_url}/api/v3")
            return response.status_code == 200
        except Exception:
            return False
    
    async def _make_request(self, endpoint: str, method: str = 'GET',
                           params: Optional[Dict] = None,
                           json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """发送 API 请求（使用同步 requests 在线程池中执行）"""
        url = f"{self.base_url}/api/v3{endpoint}"

        def sync_request():
            """同步请求函数"""
            session = requests.Session()
            session.auth = ('apikey', self.api_key)
            session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })

            try:
                if method.upper() == 'GET':
                    response = session.get(url, params=params, timeout=30)
                elif method.upper() == 'POST':
                    response = session.post(url, json=json_data, timeout=30)
                elif method.upper() == 'PATCH':
                    response = session.patch(url, json=json_data, timeout=30)
                elif method.upper() == 'PUT':
                    response = session.put(url, json=json_data, timeout=30)
                elif method.upper() == 'DELETE':
                    response = session.delete(url, timeout=30)
                else:
                    raise OpenProjectError(f"Unsupported HTTP method: {method}")

                # 处理响应
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

            except requests.RequestException as e:
                raise OpenProjectError(f"Request failed: {str(e)}")
            finally:
                session.close()

        # 在线程池中执行同步请求
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, sync_request)
        except Exception as e:
            if isinstance(e, (OpenProjectError, AuthenticationError, NotFoundError)):
                raise
            raise OpenProjectError(f"Unexpected error: {str(e)}")
    
    async def get_projects(self) -> List[Project]:
        """获取所有项目"""
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
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """获取单个项目"""
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
    
    async def get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """获取工作包列表"""
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
    
    async def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """获取单个工作包"""
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
    
    async def create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """创建工作包"""
        raise NotImplementedError("Create work package not implemented yet")
    
    async def update_work_package(self, work_package_id: str, 
                                work_package_data: Dict[str, Any]) -> WorkPackage:
        """更新工作包"""
        raise NotImplementedError("Update work package not implemented yet")
    
    async def get_users(self) -> List[User]:
        """获取用户列表"""
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
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取单个用户"""
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
    
    # 报告生成方法 - 委托给报告生成服务
    async def generate_weekly_report(self, project_id: str, 
                                   start_date: str, end_date: str) -> Report:
        """生成周报"""
        return await self.report_generator.generate_weekly_report(project_id, start_date, end_date)
    
    async def generate_monthly_report(self, project_id: str, 
                                    year: int, month: int) -> Report:
        """生成月报"""
        return await self.report_generator.generate_monthly_report(project_id, year, month)
    
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
