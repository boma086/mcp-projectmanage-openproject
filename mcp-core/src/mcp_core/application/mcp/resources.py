"""
MCP 资源管理器
"""
from typing import Dict, Any, List
from datetime import datetime

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import InvalidParams, NotFoundError
from mcp_core.shared.logger import get_logger


class MCPResourceManager:
    """MCP 资源管理器"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
        self.logger = get_logger("mcp.resources")
    
    async def list_resources(self) -> Dict[str, Any]:
        """列出所有可用资源"""
        try:
            # 获取项目列表作为资源
            projects = await self.client.get_projects()
            
            resources = []
            
            # 添加项目资源
            for project in projects:
                resources.append({
                    "uri": f"openproject://projects/{project.id}",
                    "name": f"项目: {project.name}",
                    "description": f"项目 {project.name} 的详细信息",
                    "mimeType": "application/json"
                })
                
                # 添加项目工作包资源
                resources.append({
                    "uri": f"openproject://projects/{project.id}/work_packages",
                    "name": f"工作包: {project.name}",
                    "description": f"项目 {project.name} 的所有工作包",
                    "mimeType": "application/json"
                })
                
                # 添加项目报告资源
                resources.append({
                    "uri": f"openproject://projects/{project.id}/reports/weekly",
                    "name": f"周报: {project.name}",
                    "description": f"项目 {project.name} 的周报",
                    "mimeType": "text/markdown"
                })
                
                resources.append({
                    "uri": f"openproject://projects/{project.id}/reports/monthly",
                    "name": f"月报: {project.name}",
                    "description": f"项目 {project.name} 的月报",
                    "mimeType": "text/markdown"
                })
            
            # 添加全局资源
            resources.extend([
                {
                    "uri": "openproject://projects",
                    "name": "所有项目",
                    "description": "OpenProject 中的所有项目列表",
                    "mimeType": "application/json"
                },
                {
                    "uri": "openproject://users",
                    "name": "所有用户",
                    "description": "OpenProject 中的所有用户列表",
                    "mimeType": "application/json"
                },
                {
                    "uri": "openproject://work_packages",
                    "name": "所有工作包",
                    "description": "OpenProject 中的所有工作包",
                    "mimeType": "application/json"
                }
            ])
            
            return {"resources": resources}
            
        except Exception as e:
            self.logger.error("Failed to list resources", e)
            # 返回基本资源列表
            return {
                "resources": [
                    {
                        "uri": "openproject://projects",
                        "name": "所有项目",
                        "description": "OpenProject 中的所有项目列表",
                        "mimeType": "application/json"
                    }
                ]
            }
    
    async def read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """读取指定资源"""
        uri = params.get("uri")
        if not uri:
            raise InvalidParams("Missing resource URI")
        
        self.logger.info(f"Reading resource: {uri}")
        
        try:
            # 解析 URI
            if not uri.startswith("openproject://"):
                raise InvalidParams(f"Invalid URI scheme: {uri}")
            
            path = uri[14:]  # 移除 "openproject://" 前缀
            parts = path.split("/")
            
            if path == "projects":
                return await self._read_projects()
            elif path == "users":
                return await self._read_users()
            elif path == "work_packages":
                return await self._read_work_packages()
            elif len(parts) >= 2 and parts[0] == "projects":
                project_id = parts[1]
                if len(parts) == 2:
                    return await self._read_project(project_id)
                elif len(parts) == 3 and parts[2] == "work_packages":
                    return await self._read_project_work_packages(project_id)
                elif len(parts) == 4 and parts[2] == "reports":
                    report_type = parts[3]
                    return await self._read_project_report(project_id, report_type)
            
            raise InvalidParams(f"Unknown resource path: {path}")
            
        except Exception as e:
            self.logger.error(f"Failed to read resource {uri}", e)
            raise
    
    async def _read_projects(self) -> Dict[str, Any]:
        """读取所有项目"""
        projects = await self.client.get_projects()
        
        projects_data = []
        for project in projects:
            projects_data.append({
                "id": project.id,
                "name": project.name,
                "identifier": project.identifier,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            })
        
        return {
            "contents": [
                {
                    "uri": "openproject://projects",
                    "mimeType": "application/json",
                    "text": f"找到 {len(projects)} 个项目:\n\n" + 
                           "\n".join([f"- {p['name']} ({p['identifier']}): {p['description'] or '无描述'}" 
                                    for p in projects_data])
                }
            ]
        }
    
    async def _read_users(self) -> Dict[str, Any]:
        """读取所有用户"""
        users = await self.client.get_users()
        
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "login": user.login,
                "status": user.status
            })
        
        return {
            "contents": [
                {
                    "uri": "openproject://users",
                    "mimeType": "application/json",
                    "text": f"找到 {len(users)} 个用户:\n\n" + 
                           "\n".join([f"- {u['name']} ({u['email'] or '无邮箱'}): {u['status'] or '未知状态'}" 
                                    for u in users_data])
                }
            ]
        }
    
    async def _read_work_packages(self) -> Dict[str, Any]:
        """读取所有工作包"""
        work_packages = await self.client.get_work_packages()
        
        text = f"找到 {len(work_packages)} 个工作包:\n\n"
        for wp in work_packages[:20]:  # 限制显示数量
            text += f"- {wp.subject}\n"
            text += f"  状态: {wp.status or '未知'}\n"
            if wp.assigned_to:
                text += f"  负责人: {wp.assigned_to}\n"
            text += "\n"
        
        if len(work_packages) > 20:
            text += f"... 还有 {len(work_packages) - 20} 个工作包"
        
        return {
            "contents": [
                {
                    "uri": "openproject://work_packages",
                    "mimeType": "application/json",
                    "text": text
                }
            ]
        }
    
    async def _read_project(self, project_id: str) -> Dict[str, Any]:
        """读取指定项目"""
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")
        
        text = f"项目详情:\n\n"
        text += f"名称: {project.name}\n"
        text += f"标识符: {project.identifier}\n"
        text += f"状态: {project.status or '未知'}\n"
        text += f"描述: {project.description or '无描述'}\n"
        text += f"创建时间: {project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else '未知'}\n"
        text += f"更新时间: {project.updated_at.strftime('%Y-%m-%d %H:%M:%S') if project.updated_at else '未知'}"
        
        return {
            "contents": [
                {
                    "uri": f"openproject://projects/{project_id}",
                    "mimeType": "application/json",
                    "text": text
                }
            ]
        }
    
    async def _read_project_work_packages(self, project_id: str) -> Dict[str, Any]:
        """读取项目工作包"""
        work_packages = await self.client.get_work_packages(project_id)
        
        text = f"项目工作包 (共 {len(work_packages)} 个):\n\n"
        for wp in work_packages:
            text += f"- {wp.subject}\n"
            text += f"  状态: {wp.status or '未知'}\n"
            if wp.assigned_to:
                text += f"  负责人: {wp.assigned_to}\n"
            if wp.progress is not None:
                text += f"  进度: {wp.progress}%\n"
            text += "\n"
        
        return {
            "contents": [
                {
                    "uri": f"openproject://projects/{project_id}/work_packages",
                    "mimeType": "application/json",
                    "text": text
                }
            ]
        }
    
    async def _read_project_report(self, project_id: str, report_type: str) -> Dict[str, Any]:
        """读取项目报告"""
        if report_type == "weekly":
            # 生成本周的周报
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            report = await self.client.generate_weekly_report(
                project_id,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
        elif report_type == "monthly":
            # 生成本月的月报
            now = datetime.now()
            report = await self.client.generate_monthly_report(project_id, now.year, now.month)
        else:
            raise InvalidParams(f"Unknown report type: {report_type}")
        
        return {
            "contents": [
                {
                    "uri": f"openproject://projects/{project_id}/reports/{report_type}",
                    "mimeType": "text/markdown",
                    "text": report.to_markdown()
                }
            ]
        }
