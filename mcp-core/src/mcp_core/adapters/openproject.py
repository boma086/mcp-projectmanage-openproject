"""
OpenProject 适配器实现

提供标准化的 OpenProject API 接口，支持异步操作和完整的错误处理。
该适配器实现了 IOpenProjectClient 接口，可被所有解决方案架构共享使用。
"""

import asyncio
import aiohttp
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from urllib.parse import urljoin

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.domain.models import Project, WorkPackage, User, Report
from mcp_core.shared.exceptions import (
    OpenProjectError, AuthenticationError, AuthorizationError, 
    NotFoundError, ValidationError, TimeoutError, RateLimitError
)
from mcp_core.shared.config import get_global_config
from mcp_core.shared.logger import get_logger


logger = get_logger(__name__)


class OpenProjectAdapter(IOpenProjectClient):
    """
    OpenProject API 适配器
    
    提供统一的 OpenProject API 访问接口，支持：
    - 异步操作
    - 连接池管理
    - 错误处理和重试机制
    - 请求/响应日志记录
    - 类型安全的数据模型转换
    """
    
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None):
        """
        初始化 OpenProject 适配器
        
        Args:
            url: OpenProject 实例 URL，如未提供则从配置读取
            api_key: API 密钥，如未提供则从配置读取
        """
        config = get_global_config()
        self.base_url = (url or config.openproject_url).rstrip('/')
        self.api_key = api_key or config.openproject_api_key
        self.timeout = config.request_timeout
        self.max_retries = config.retry_attempts
        self.retry_delay = config.retry_delay
        
        # HTTP 会话管理
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        logger.info(f"OpenProject 适配器已初始化: {self.base_url}")
    
    async def initialize(self) -> None:
        """初始化 HTTP 会话"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=20,  # 总连接池大小
                limit_per_host=10,  # 每个主机的连接数
                ttl_dns_cache=300,  # DNS 缓存时间
                use_dns_cache=True,
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=self._session_timeout,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'mcp-core/1.0 OpenProject-Adapter'
                }
            )
            logger.debug("HTTP 会话已初始化")
    
    async def cleanup(self) -> None:
        """清理 HTTP 会话和连接池"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP 会话已关闭")
    
    async def check_connection(self) -> bool:
        """
        检查与 OpenProject 的连接状态
        
        Returns:
            bool: 连接是否正常
        """
        try:
            await self._make_request("/")
            logger.info("OpenProject 连接测试成功")
            return True
        except Exception as e:
            logger.warning(f"OpenProject 连接测试失败: {e}")
            return False
    
    async def _make_request(
        self, 
        endpoint: str, 
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求到 OpenProject API
        
        Args:
            endpoint: API 端点路径
            method: HTTP 方法
            params: URL 查询参数
            json_data: JSON 请求体
            headers: 额外的请求头
            
        Returns:
            Dict[str, Any]: API 响应数据
            
        Raises:
            OpenProjectError: API 请求失败
            AuthenticationError: 认证失败
            AuthorizationError: 授权失败
            NotFoundError: 资源未找到
            TimeoutError: 请求超时
            RateLimitError: 超出速率限制
        """
        await self.initialize()
        
        url = urljoin(f"{self.base_url}/api/v3", endpoint.lstrip('/'))
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        # 记录请求日志
        logger.debug(f"发送 {method} 请求到: {url}")
        if params:
            logger.debug(f"查询参数: {params}")
        if json_data:
            logger.debug(f"请求体: {json_data}")
        
        last_exception = None
        
        # 重试机制
        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers
                ) as response:
                    # 处理响应状态码
                    await self._handle_response_status(response)
                    
                    # 解析响应数据
                    try:
                        data = await response.json()
                        logger.debug(f"API 响应成功: {response.status}")
                        return data
                    except aiohttp.ContentTypeError:
                        # 某些端点可能返回非 JSON 响应
                        text = await response.text()
                        if response.status == 200:
                            return {"message": text}
                        raise OpenProjectError(f"无效的响应格式: {text}")
                        
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"请求超时 (尝试 {attempt + 1}/{self.max_retries + 1})")
                
            except aiohttp.ClientError as e:
                last_exception = OpenProjectError(f"网络错误: {str(e)}")
                
            except (AuthenticationError, AuthorizationError, NotFoundError, RateLimitError):
                # 这些错误不需要重试
                raise
                
            except Exception as e:
                last_exception = OpenProjectError(f"请求失败: {str(e)}")
            
            # 如果不是最后一次尝试，等待后重试
            if attempt < self.max_retries:
                wait_time = self.retry_delay * (2 ** attempt)  # 指数退避
                logger.warning(f"请求失败，{wait_time:.1f}秒后重试... (尝试 {attempt + 1}/{self.max_retries + 1})")
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        raise last_exception
    
    async def _handle_response_status(self, response: aiohttp.ClientResponse) -> None:
        """
        处理 HTTP 响应状态码，抛出相应异常
        
        Args:
            response: HTTP 响应对象
            
        Raises:
            AuthenticationError: 401 错误
            AuthorizationError: 403 错误  
            NotFoundError: 404 错误
            RateLimitError: 429 错误
            OpenProjectError: 其他客户端/服务器错误
        """
        if response.status == 401:
            raise AuthenticationError("认证失败，请检查 API 密钥")
        elif response.status == 403:
            raise AuthorizationError("权限不足，无法访问资源")
        elif response.status == 404:
            raise NotFoundError("请求的资源不存在")
        elif response.status == 429:
            retry_after = response.headers.get('Retry-After', '60')
            raise RateLimitError(f"超出 API 速率限制，请在 {retry_after} 秒后重试")
        elif response.status >= 400:
            try:
                error_data = await response.json()
                error_msg = error_data.get('message', f'API 错误 {response.status}')
            except:
                error_msg = f'HTTP {response.status} 错误'
            raise OpenProjectError(error_msg, status_code=response.status)
    
    # ==================== 项目相关方法 ====================
    
    async def get_projects(self) -> List[Project]:
        """
        获取所有可访问的项目
        
        Returns:
            List[Project]: 项目列表
        """
        logger.info("获取所有项目")
        data = await self._make_request("/projects")
        
        projects = []
        for item in data.get('_embedded', {}).get('elements', []):
            try:
                project = self._convert_to_project(item)
                projects.append(project)
            except Exception as e:
                logger.warning(f"转换项目数据失败: {e}, 数据: {item}")
                continue
        
        logger.info(f"成功获取 {len(projects)} 个项目")
        return projects
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """
        获取指定项目的详细信息
        
        Args:
            project_id: 项目 ID
            
        Returns:
            Optional[Project]: 项目对象，不存在时返回 None
        """
        logger.info(f"获取项目: {project_id}")
        
        try:
            data = await self._make_request(f"/projects/{project_id}")
            project = self._convert_to_project(data)
            logger.info(f"成功获取项目: {project.name}")
            return project
        except NotFoundError:
            logger.warning(f"项目不存在: {project_id}")
            return None
    
    # ==================== 工作包相关方法 ====================
    
    async def get_work_packages(self, project_id: Optional[str] = None) -> List[WorkPackage]:
        """
        获取工作包列表
        
        Args:
            project_id: 项目 ID，如果提供则只返回该项目的工作包
            
        Returns:
            List[WorkPackage]: 工作包列表
        """
        logger.info(f"获取工作包列表 (项目: {project_id or '全部'})")
        
        endpoint = "/work_packages"
        params = {}
        
        if project_id:
            # 使用 OpenProject 的过滤器语法
            params['filters'] = f'[{{"project":{{"operator":"=","values":["{project_id}"]}}}}]'
        
        data = await self._make_request(endpoint, params=params)
        
        work_packages = []
        for item in data.get('_embedded', {}).get('elements', []):
            try:
                wp = self._convert_to_work_package(item, project_id)
                work_packages.append(wp)
            except Exception as e:
                logger.warning(f"转换工作包数据失败: {e}, 数据: {item}")
                continue
        
        logger.info(f"成功获取 {len(work_packages)} 个工作包")
        return work_packages
    
    async def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """
        获取指定工作包的详细信息
        
        Args:
            work_package_id: 工作包 ID
            
        Returns:
            Optional[WorkPackage]: 工作包对象，不存在时返回 None
        """
        logger.info(f"获取工作包: {work_package_id}")
        
        try:
            data = await self._make_request(f"/work_packages/{work_package_id}")
            wp = self._convert_to_work_package(data)
            logger.info(f"成功获取工作包: {wp.subject}")
            return wp
        except NotFoundError:
            logger.warning(f"工作包不存在: {work_package_id}")
            return None
    
    async def create_work_package(self, work_package_data: Dict[str, Any]) -> WorkPackage:
        """
        创建新的工作包
        
        Args:
            work_package_data: 工作包数据
            
        Returns:
            WorkPackage: 创建的工作包对象
            
        Raises:
            ValidationError: 数据验证失败
            OpenProjectError: 创建失败
        """
        logger.info("创建新工作包")
        
        # 验证必需字段
        if 'subject' not in work_package_data:
            raise ValidationError("工作包主题 (subject) 是必需的", field="subject")
        
        try:
            data = await self._make_request("/work_packages", method="POST", json_data=work_package_data)
            wp = self._convert_to_work_package(data)
            logger.info(f"成功创建工作包: {wp.subject} (ID: {wp.id})")
            return wp
        except Exception as e:
            logger.error(f"创建工作包失败: {e}")
            raise
    
    async def update_work_package(
        self, 
        work_package_id: str, 
        work_package_data: Dict[str, Any]
    ) -> WorkPackage:
        """
        更新工作包信息
        
        Args:
            work_package_id: 工作包 ID
            work_package_data: 更新的数据
            
        Returns:
            WorkPackage: 更新后的工作包对象
            
        Raises:
            NotFoundError: 工作包不存在
            ValidationError: 数据验证失败
            OpenProjectError: 更新失败
        """
        logger.info(f"更新工作包: {work_package_id}")
        
        try:
            data = await self._make_request(
                f"/work_packages/{work_package_id}", 
                method="PATCH", 
                json_data=work_package_data
            )
            wp = self._convert_to_work_package(data)
            logger.info(f"成功更新工作包: {wp.subject}")
            return wp
        except Exception as e:
            logger.error(f"更新工作包失败: {e}")
            raise
    
    # ==================== 用户相关方法 ====================
    
    async def get_users(self) -> List[User]:
        """
        获取所有用户列表
        
        Returns:
            List[User]: 用户列表
        """
        logger.info("获取用户列表")
        data = await self._make_request("/users")
        
        users = []
        for item in data.get('_embedded', {}).get('elements', []):
            try:
                user = self._convert_to_user(item)
                users.append(user)
            except Exception as e:
                logger.warning(f"转换用户数据失败: {e}, 数据: {item}")
                continue
        
        logger.info(f"成功获取 {len(users)} 个用户")
        return users
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """
        获取指定用户的详细信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Optional[User]: 用户对象，不存在时返回 None
        """
        logger.info(f"获取用户: {user_id}")
        
        try:
            data = await self._make_request(f"/users/{user_id}")
            user = self._convert_to_user(data)
            logger.info(f"成功获取用户: {user.name}")
            return user
        except NotFoundError:
            logger.warning(f"用户不存在: {user_id}")
            return None
    
    # ==================== 报告生成方法 ====================
    
    async def generate_weekly_report(
        self, 
        project_id: str, 
        start_date: str, 
        end_date: str
    ) -> Report:
        """
        生成项目周报
        
        Args:
            project_id: 项目 ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            Report: 周报对象
        """
        logger.info(f"生成周报: 项目 {project_id}, 时间 {start_date} 到 {end_date}")
        
        # 获取项目信息
        project = await self.get_project(project_id)
        if not project:
            raise NotFoundError(f"项目不存在: {project_id}")
        
        # 获取时间范围内的工作包
        work_packages = await self.get_work_packages(project_id)
        
        # 这里应该委托给报告生成服务，暂时返回基本报告
        return Report(
            title=f"{project.name} 周报",
            project_name=project.name,
            period=f"{start_date} 至 {end_date}",
            summary=f"项目 {project.name} 在 {start_date} 至 {end_date} 期间共有 {len(work_packages)} 个工作包"
        )
    
    async def generate_monthly_report(self, project_id: str, year: int, month: int) -> Report:
        """
        生成项目月报
        
        Args:
            project_id: 项目 ID
            year: 年份
            month: 月份
            
        Returns:
            Report: 月报对象
        """
        logger.info(f"生成月报: 项目 {project_id}, 时间 {year}-{month:02d}")
        
        project = await self.get_project(project_id)
        if not project:
            raise NotFoundError(f"项目不存在: {project_id}")
        
        return Report(
            title=f"{project.name} {year}年{month}月报告",
            project_name=project.name,
            period=f"{year}年{month:02d}月",
            summary=f"项目 {project.name} 的 {year}年{month}月报告"
        )
    
    async def assess_project_risks(self, project_id: str) -> Report:
        """
        评估项目风险
        
        Args:
            project_id: 项目 ID
            
        Returns:
            Report: 风险评估报告
        """
        logger.info(f"评估项目风险: {project_id}")
        
        project = await self.get_project(project_id)
        if not project:
            raise NotFoundError(f"项目不存在: {project_id}")
        
        return Report(
            title=f"{project.name} 风险评估报告",
            project_name=project.name,
            period=f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            summary="风险评估功能正在开发中"
        )
    
    # ==================== 配置方法 ====================
    
    def get_base_url(self) -> str:
        """获取 OpenProject 基础 URL"""
        return self.base_url
    
    def get_api_key(self) -> str:
        """获取 API 密钥"""
        return self.api_key
    
    # ==================== 数据转换方法 ====================
    
    def _convert_to_project(self, data: Dict[str, Any]) -> Project:
        """将 API 响应数据转换为 Project 对象"""
        return Project(
            id=str(data['id']),
            name=data['name'],
            identifier=data['identifier'],
            description=self._extract_text_content(data.get('description')),
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt')),
            status=self._extract_name(data.get('status'))
        )
    
    def _convert_to_work_package(
        self, 
        data: Dict[str, Any], 
        project_id: Optional[str] = None
    ) -> WorkPackage:
        """将 API 响应数据转换为 WorkPackage 对象"""
        return WorkPackage(
            id=str(data['id']),
            subject=data['subject'],
            description=self._extract_text_content(data.get('description')),
            status=self._extract_name(data.get('status')),
            type=self._extract_name(data.get('type')),
            priority=self._extract_name(data.get('priority')),
            assigned_to=self._extract_name(data.get('assignee')),
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt')),
            start_date=self._parse_date(data.get('startDate')),
            due_date=self._parse_date(data.get('dueDate')),
            progress=data.get('percentageDone'),
            project_id=project_id or self._extract_id(data.get('project'))
        )
    
    def _convert_to_user(self, data: Dict[str, Any]) -> User:
        """将 API 响应数据转换为 User 对象"""
        return User(
            id=str(data['id']),
            name=data['name'],
            email=data.get('email'),
            login=data.get('login'),
            created_at=self._parse_datetime(data.get('createdAt')),
            updated_at=self._parse_datetime(data.get('updatedAt')),
            status=data.get('status')
        )
    
    # ==================== 辅助方法 ====================
    
    def _extract_text_content(self, content: Optional[Dict[str, Any]]) -> str:
        """从内容对象中提取文本"""
        if not content:
            return ""
        return content.get('raw', '') if isinstance(content, dict) else str(content)
    
    def _extract_name(self, obj: Optional[Dict[str, Any]]) -> Optional[str]:
        """从对象中提取名称"""
        if not obj or not isinstance(obj, dict):
            return None
        return obj.get('name')
    
    def _extract_id(self, obj: Optional[Dict[str, Any]]) -> Optional[str]:
        """从对象中提取 ID"""
        if not obj or not isinstance(obj, dict):
            return None
        return str(obj.get('id'))
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析 ISO 格式的日期时间字符串"""
        if not date_str:
            return None
        
        try:
            # 处理 ISO 格式和时区信息
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # 移除时区信息，统一使用本地时间
            return dt.replace(tzinfo=None)
        except (ValueError, AttributeError) as e:
            logger.warning(f"日期时间解析失败: {date_str}, 错误: {e}")
            return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, AttributeError) as e:
            logger.warning(f"日期解析失败: {date_str}, 错误: {e}")
            return None
    
    # ==================== 上下文管理器支持 ====================
    
    async def __aenter__(self):
        """异步上下文管理器进入"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.cleanup()