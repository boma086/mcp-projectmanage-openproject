import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from models.schemas import Project, WorkPackage, Report, ReportSection

class OpenProjectAdapter:
    def __init__(self, url: str, api_key: str):
        """初始化OpenProject适配器
        
        Args:
            url: OpenProject实例URL
            api_key: API密钥
        """
        self.base_url = url.rstrip('/')
        self.api_key = api_key
        # 移除错误的 Authorization 头设置
        self.headers = {
            'Content-Type': 'application/json'
        }
        # 使用正确的 Basic Auth 格式：用户名为 'apikey'，密码为 API 密钥
        self.auth = ('apikey', api_key)
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}/api/v3{endpoint}"
        try:
            # 使用 auth 参数进行 Basic Auth 认证
            if method in ['POST', 'PATCH', 'PUT']:
                # 对于写操作，使用 json 参数
                response = requests.request(method, url, headers=self.headers, json=params, auth=self.auth)
            else:
                # 对于读操作，使用 params 参数
                response = requests.request(method, url, headers=self.headers, params=params, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API请求失败: {e}")
            return {}
    
    def get_projects(self) -> List[Project]:
        """获取所有项目"""
        try:
            data = self._make_request('/projects')
            projects = []
            
            if '_embedded' in data and 'elements' in data['_embedded']:
                for project_data in data['_embedded']['elements']:
                    projects.append(Project(
                        id=str(project_data.get('id', '')),
                        name=project_data.get('name', ''),
                        identifier=project_data.get('identifier', ''),
                        description=project_data.get('description', {}).get('raw', '') if project_data.get('description') else None,
                        created_at=datetime.fromisoformat(project_data['createdAt'].replace('Z', '+00:00')) if project_data.get('createdAt') else None,
                        updated_at=datetime.fromisoformat(project_data['updatedAt'].replace('Z', '+00:00')) if project_data.get('updatedAt') else None,
                        status=project_data.get('status', 'active')
                    ))
            return projects
        except Exception as e:
            print(f"获取项目列表时出错: {e}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取特定项目"""
        try:
            data = self._make_request(f'/projects/{project_id}')
            if data:
                return Project(
                    id=str(data.get('id', '')),
                    name=data.get('name', ''),
                    identifier=data.get('identifier', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    status=data.get('status', 'active')
                )
        except Exception as e:
            print(f"获取项目 {project_id} 时出错: {e}")
            return None
    
    def get_work_packages(self, project_id: str = None) -> List[WorkPackage]:
        """获取项目的工作包"""
        try:
            if project_id:
                params = {'filters': f'[{{"project":{{"operator":"=","values":["{project_id}"]}}}}]'}
            else:
                params = {}
            data = self._make_request('/work_packages', params=params)
            work_packages = []
            
            if '_embedded' in data and 'elements' in data['_embedded']:
                for wp_data in data['_embedded']['elements']:
                    work_packages.append(WorkPackage(
                        id=str(wp_data.get('id', '')),
                        subject=wp_data.get('subject', ''),
                        description=wp_data.get('description', {}).get('raw', '') if wp_data.get('description') else None,
                        status=wp_data.get('_links', {}).get('status', {}).get('title', '') if wp_data.get('_links') else None,
                        type=wp_data.get('_links', {}).get('type', {}).get('title', '') if wp_data.get('_links') else None,
                        priority=wp_data.get('_links', {}).get('priority', {}).get('title', '') if wp_data.get('_links') else None,
                        assigned_to=wp_data.get('_links', {}).get('assignee', {}).get('title', '') if wp_data.get('_links') else None,
                        created_at=datetime.fromisoformat(wp_data['createdAt'].replace('Z', '+00:00')) if wp_data.get('createdAt') else None,
                        updated_at=datetime.fromisoformat(wp_data['updatedAt'].replace('Z', '+00:00')) if wp_data.get('updatedAt') else None,
                        start_date=datetime.fromisoformat(wp_data['startDate']) if wp_data.get('startDate') else None,
                        due_date=datetime.fromisoformat(wp_data['dueDate']) if wp_data.get('dueDate') else None,
                        progress=wp_data.get('percentageDone', 0)
                    ))
            return work_packages
        except Exception as e:
            print(f"获取项目 {project_id} 的工作包时出错: {e}")
            return []
    
    def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """获取特定工作包"""
        try:
            data = self._make_request(f'/work_packages/{work_package_id}')
            if data:
                return WorkPackage(
                    id=str(data.get('id', '')),
                    subject=data.get('subject', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    status=data.get('_links', {}).get('status', {}).get('title', '') if data.get('_links') else None,
                    type=data.get('_links', {}).get('type', {}).get('title', '') if data.get('_links') else None,
                    priority=data.get('_links', {}).get('priority', {}).get('title', '') if data.get('_links') else None,
                    assigned_to=data.get('_links', {}).get('assignee', {}).get('title', '') if data.get('_links') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    start_date=datetime.fromisoformat(data['startDate']) if data.get('startDate') else None,
                    due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
                    progress=data.get('percentageDone', 0)
                )
        except Exception as e:
            print(f"获取工作包 {work_package_id} 时出错: {e}")
            return None

    def create_work_package(self, project_id: str, subject: str, description: str = None, work_package_type: str = "Task") -> Optional[WorkPackage]:
        """创建新的工作包"""
        try:
            payload = {
                "subject": subject,
                "_links": {
                    "project": {"href": f"/api/v3/projects/{project_id}"},
                    "type": {"href": f"/api/v3/types/1"}  # 默认类型，可能需要根据实际情况调整
                }
            }
            if description:
                payload["description"] = {"raw": description}

            data = self._make_request('/work_packages', method='POST', params=payload)
            if data:
                return WorkPackage(
                    id=str(data.get('id', '')),
                    subject=data.get('subject', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    status=data.get('_links', {}).get('status', {}).get('title', '') if data.get('_links') else None,
                    type=data.get('_links', {}).get('type', {}).get('title', '') if data.get('_links') else None,
                    priority=data.get('_links', {}).get('priority', {}).get('title', '') if data.get('_links') else None,
                    assigned_to=data.get('_links', {}).get('assignee', {}).get('title', '') if data.get('_links') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    start_date=datetime.fromisoformat(data['startDate']) if data.get('startDate') else None,
                    due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
                    progress=data.get('percentageDone', 0)
                )
        except Exception as e:
            print(f"创建工作包时出错: {e}")
            return None

    def update_work_package(self, work_package_id: str, subject: str = None, description: str = None, status: str = None) -> Optional[WorkPackage]:
        """更新工作包信息"""
        try:
            payload = {}
            if subject:
                payload["subject"] = subject
            if description:
                payload["description"] = {"raw": description}
            # 状态更新需要特殊处理，这里简化处理

            data = self._make_request(f'/work_packages/{work_package_id}', method='PATCH', params=payload)
            if data:
                return WorkPackage(
                    id=str(data.get('id', '')),
                    subject=data.get('subject', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    status=data.get('_links', {}).get('status', {}).get('title', '') if data.get('_links') else None,
                    type=data.get('_links', {}).get('type', {}).get('title', '') if data.get('_links') else None,
                    priority=data.get('_links', {}).get('priority', {}).get('title', '') if data.get('_links') else None,
                    assigned_to=data.get('_links', {}).get('assignee', {}).get('title', '') if data.get('_links') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    start_date=datetime.fromisoformat(data['startDate']) if data.get('startDate') else None,
                    due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
                    progress=data.get('percentageDone', 0)
                )
        except Exception as e:
            print(f"更新工作包 {work_package_id} 时出错: {e}")
            return None

    def generate_project_report(self, project_id: str) -> Report:
        """生成项目报告"""
        # 生成最近一周的报告
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        return self.generate_weekly_report(
            project_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )

    def generate_weekly_report(self, project_id: str, start_date: str, end_date: str) -> Report:
        """生成项目周报"""
        try:
            # 获取项目信息
            project = self.get_project(project_id)
            if not project:
                raise ValueError(f"找不到项目 {project_id}")
            
            # 获取项目工作包
            work_packages = self.get_work_packages(project_id)
            
            # 过滤指定日期范围内更新的工作包
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # 过滤在日期范围内更新的工作包
            filtered_wps = [wp for wp in work_packages if wp.updated_at and start_dt <= wp.updated_at <= end_dt]
            
            # 按状态分组
            status_groups = {}
            for wp in filtered_wps:
                status = wp.status or "未知状态"
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(wp)
            
            # 生成报告各部分
            sections = []
            
            # 添加概述部分
            summary = f"本周期内（{start_date} 至 {end_date}）共有 {len(filtered_wps)} 个工作包有更新。"
            
            # 添加各状态的工作包部分
            for status, wps in status_groups.items():
                content = f"### {status}工作包（{len(wps)}个）\n\n"
                for wp in wps:
                    content += f"- **{wp.subject}** (ID: {wp.id})\n"
                    if wp.assigned_to:
                        content += f"  - 负责人: {wp.assigned_to}\n"
                    if wp.progress is not None:
                        content += f"  - 进度: {wp.progress}%\n"
                    if wp.description:
                        desc_summary = wp.description[:100] + "..." if len(wp.description) > 100 else wp.description
                        content += f"  - 描述: {desc_summary}\n"
                    content += "\n"
                
                sections.append(ReportSection(
                    title=f"{status}工作包",
                    content=content
                ))
            
            # 添加统计信息
            statistics = {
                "total_work_packages": len(work_packages),
                "updated_work_packages": len(filtered_wps),
                "status_distribution": {status: len(wps) for status, wps in status_groups.items()}
            }
            
            # 创建报告
            return Report(
                title=f"{project.name} 周报: {start_date} 至 {end_date}",
                project_name=project.name,
                period=f"{start_date} 至 {end_date}",
                summary=summary,
                sections=sections,
                statistics=statistics
            )
            
        except Exception as e:
            print(f"生成周报时出错: {e}")
            # 返回一个错误报告
            return Report(
                title="生成报告出错",
                project_name=f"项目 {project_id}",
                period=f"{start_date} 至 {end_date}",
                summary=f"生成报告时出错: {str(e)}",
                sections=[],
                statistics={}
            )