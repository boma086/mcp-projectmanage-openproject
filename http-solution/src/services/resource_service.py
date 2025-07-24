"""
MCP Resources 服务
提供资源管理和访问功能
"""
import re
import json
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urlparse, parse_qs
from datetime import datetime

from src.models.schemas import Project, WorkPackage, Report
from src.utils.logger import mcp_logger
from src.utils.exceptions import OpenProjectError, ValidationError


class ResourceService:
    """MCP资源服务管理器"""
    
    def __init__(self, openproject_adapter):
        self.openproject_adapter = openproject_adapter
        self._static_resources = {}
        self._resource_templates = {}
        self._register_default_resources()
    
    def _register_default_resources(self):
        """注册默认的资源和模板"""
        # 静态资源
        self._static_resources = {
            "openproject://info": {
                "uri": "openproject://info",
                "name": "OpenProject服务信息",
                "description": "OpenProject MCP服务的基本信息和配置",
                "mimeType": "application/json"
            },
            "openproject://docs": {
                "uri": "openproject://docs",
                "name": "API文档",
                "description": "OpenProject MCP服务的API使用文档",
                "mimeType": "text/markdown"
            }
        }
        
        # 动态资源模板
        self._resource_templates = {
            "openproject://projects/{project_id}": {
                "uriTemplate": "openproject://projects/{project_id}",
                "name": "项目详情",
                "description": "获取特定项目的详细信息",
                "mimeType": "application/json"
            },
            "openproject://projects/{project_id}/work_packages": {
                "uriTemplate": "openproject://projects/{project_id}/work_packages",
                "name": "项目工作包",
                "description": "获取特定项目的所有工作包",
                "mimeType": "application/json"
            },
            "openproject://projects/{project_id}/report": {
                "uriTemplate": "openproject://projects/{project_id}/report",
                "name": "项目报告",
                "description": "获取特定项目的详细报告",
                "mimeType": "text/markdown"
            },
            "openproject://work_packages/{work_package_id}": {
                "uriTemplate": "openproject://work_packages/{work_package_id}",
                "name": "工作包详情",
                "description": "获取特定工作包的详细信息",
                "mimeType": "application/json"
            }
        }
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """列出所有可用资源"""
        resources = []
        
        # 添加静态资源
        for resource in self._static_resources.values():
            resources.append(resource)
        
        return resources
    
    def list_resource_templates(self) -> List[Dict[str, Any]]:
        """列出所有资源模板"""
        return list(self._resource_templates.values())
    
    def read_resource(self, uri: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """读取指定URI的资源内容"""
        mcp_logger.logger.debug(f"读取资源: {uri}", extra={'request_id': request_id})
        
        # 检查静态资源
        if uri in self._static_resources:
            return self._read_static_resource(uri, request_id)
        
        # 检查动态资源模板
        for template_uri, template_info in self._resource_templates.items():
            if params := self._match_template(template_uri, uri):
                return self._read_dynamic_resource(template_uri, params, request_id)
        
        raise ValidationError(f"Unknown resource URI: {uri}")
    
    def _match_template(self, template: str, uri: str) -> Optional[Dict[str, str]]:
        """匹配URI模板并提取参数，先整体转义模板再替换占位符"""
        import re
        # 先整体转义模板
        escaped_template = re.escape(template)
        # 替换转义后的占位符为命名组
        pattern = re.sub(r'\\\{([^}]+)\\\}', r'(?P<\1>[^/]+)', escaped_template)
        pattern = f"^{pattern}$"
        match = re.match(pattern, uri)
        if match:
            return match.groupdict()
        return None
    
    def _read_static_resource(self, uri: str, request_id: Optional[str] = None) -> Dict[str, Any]:
        """读取静态资源"""
        if uri == "openproject://info":
            content = {
                "service": "OpenProject MCP Server",
                "version": "1.0.0",
                "description": "MCP服务器，提供OpenProject项目管理功能",
                "capabilities": ["tools", "resources", "prompts"],
                "openproject_url": self.openproject_adapter.base_url if self.openproject_adapter else None,
                "timestamp": datetime.now().isoformat()
            }
            return {
                "uri": uri,
                "mimeType": "application/json",
                "text": json.dumps(content, ensure_ascii=False, indent=2)
            }
        
        elif uri == "openproject://docs":
            content = """# OpenProject MCP 服务文档

## 概述
这是一个MCP (Model Context Protocol) 服务器，提供与OpenProject项目管理系统的集成。

## 支持的工具
- `get_projects`: 获取所有项目列表
- `get_project`: 获取特定项目详情
- `get_work_packages`: 获取工作包列表
- `generate_project_report`: 生成项目报告

## 支持的资源
- `openproject://info`: 服务信息
- `openproject://docs`: 本文档
- `openproject://projects/{project_id}`: 项目详情
- `openproject://projects/{project_id}/work_packages`: 项目工作包
- `openproject://projects/{project_id}/report`: 项目报告

## 使用示例
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/read",
  "params": {
    "uri": "openproject://projects/1"
  }
}
```
"""
            return {
                "uri": uri,
                "mimeType": "text/markdown",
                "text": content
            }
        
        raise ValidationError(f"Unknown static resource: {uri}")
    
    def _read_dynamic_resource(self, template_uri: str, params: Dict[str, str], 
                              request_id: Optional[str] = None) -> Dict[str, Any]:
        """读取动态资源"""
        if not self.openproject_adapter:
            raise OpenProjectError("OpenProject adapter not initialized")
        
        try:
            if template_uri == "openproject://projects/{project_id}":
                project_id = params['project_id']
                project = self.openproject_adapter.get_project(project_id, request_id)
                if not project:
                    raise ValidationError(f"Project not found: {project_id}")
                
                content = {
                    "id": project.id,
                    "name": project.name,
                    "identifier": project.identifier,
                    "description": project.description,
                    "status": project.status,
                    "created_at": project.created_at.isoformat() if project.created_at else None,
                    "updated_at": project.updated_at.isoformat() if project.updated_at else None
                }
                
                return {
                    "uri": f"openproject://projects/{project_id}",
                    "mimeType": "application/json",
                    "text": json.dumps(content, ensure_ascii=False, indent=2)
                }
            
            elif template_uri == "openproject://projects/{project_id}/work_packages":
                project_id = params['project_id']
                work_packages = self.openproject_adapter.get_work_packages(project_id, request_id)
                
                content = {
                    "project_id": project_id,
                    "work_packages": [
                        {
                            "id": wp.id,
                            "subject": wp.subject,
                            "description": wp.description,
                            "status": wp.status,
                            "type": wp.type,
                            "priority": wp.priority,
                            "assigned_to": wp.assigned_to,
                            "progress": wp.progress,
                            "created_at": wp.created_at.isoformat() if wp.created_at else None,
                            "updated_at": wp.updated_at.isoformat() if wp.updated_at else None,
                            "start_date": wp.start_date.isoformat() if wp.start_date else None,
                            "due_date": wp.due_date.isoformat() if wp.due_date else None
                        }
                        for wp in work_packages
                    ],
                    "total_count": len(work_packages)
                }
                
                return {
                    "uri": f"openproject://projects/{project_id}/work_packages",
                    "mimeType": "application/json",
                    "text": json.dumps(content, ensure_ascii=False, indent=2)
                }
            
            elif template_uri == "openproject://projects/{project_id}/report":
                project_id = params['project_id']
                report = self.openproject_adapter.generate_project_report(project_id, request_id)
                
                content = f"# {report.title}\n\n"
                content += f"**项目**: {report.project_name}\n"
                content += f"**期间**: {report.period}\n"
                content += f"**生成时间**: {report.generated_at.isoformat()}\n\n"
                content += f"## 摘要\n{report.summary}\n\n"
                
                for section in report.sections:
                    content += f"## {section.title}\n{section.content}\n\n"
                
                if report.statistics:
                    content += "## 统计信息\n"
                    for key, value in report.statistics.items():
                        content += f"- **{key}**: {value}\n"
                
                return {
                    "uri": f"openproject://projects/{project_id}/report",
                    "mimeType": "text/markdown",
                    "text": content
                }
            
            else:
                raise ValidationError(f"Unknown dynamic resource template: {template_uri}")
                
        except Exception as e:
            if isinstance(e, (ValidationError, OpenProjectError)):
                raise
            else:
                mcp_logger.log_error(f"读取动态资源失败: {template_uri}", e, request_id)
                raise OpenProjectError(f"Failed to read resource: {str(e)}")
