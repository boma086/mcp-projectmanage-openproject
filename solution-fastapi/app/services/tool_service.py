"""
Tool Service for MCP Protocol

Handles tool listing and execution with async optimizations.
"""
from typing import List, Dict, Any
from mcp_core.domain.interfaces.openproject_client import IOpenProjectClient


class ToolService:
    """Service for managing MCP tools"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.openproject_client = openproject_client
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available MCP tools"""
        return [
            {
                "name": "get_projects",
                "description": "Get all projects from OpenProject",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_project",
                "description": "Get a specific project by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "get_work_packages",
                "description": "Get work packages for a project",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID (optional)"}
                    }
                }
            },
            {
                "name": "get_work_package",
                "description": "Get a specific work package by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "work_package_id": {"type": "string", "description": "Work Package ID"}
                    },
                    "required": ["work_package_id"]
                }
            },
            {
                "name": "create_work_package",
                "description": "Create a new work package",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string", "description": "Work package subject"},
                        "description": {"type": "string", "description": "Work package description"},
                        "project_id": {"type": "string", "description": "Project ID"},
                        "type": {"type": "string", "description": "Work package type"}
                    },
                    "required": ["subject", "project_id"]
                }
            },
            {
                "name": "generate_weekly_report",
                "description": "Generate a weekly project report",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                    },
                    "required": ["project_id", "start_date", "end_date"]
                }
            },
            {
                "name": "generate_monthly_report",
                "description": "Generate a monthly project report",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"},
                        "year": {"type": "integer", "description": "Year"},
                        "month": {"type": "integer", "description": "Month (1-12)"}
                    },
                    "required": ["project_id", "year", "month"]
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with arguments"""
        try:
            if tool_name == "get_projects":
                projects = await self.openproject_client.get_projects()
                return {"projects": [self._convert_to_dict(project) for project in projects]}
            
            elif tool_name == "get_project":
                project_id = arguments.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                project = await self.openproject_client.get_project(project_id)
                return {"project": self._convert_to_dict(project) if project else None}
            
            elif tool_name == "get_work_packages":
                project_id = arguments.get("project_id")
                work_packages = await self.openproject_client.get_work_packages(project_id)
                return {"work_packages": [self._convert_to_dict(wp) for wp in work_packages]}
            
            elif tool_name == "get_work_package":
                work_package_id = arguments.get("work_package_id")
                if not work_package_id:
                    raise ValueError("work_package_id is required")
                wp = await self.openproject_client.get_work_package(work_package_id)
                return {"work_package": self._convert_to_dict(wp) if wp else None}
            
            elif tool_name == "create_work_package":
                work_package_data = {
                    "subject": arguments.get("subject"),
                    "description": arguments.get("description", ""),
                    "_links": {
                        "project": {"href": f"/api/v3/projects/{arguments.get('project_id')}"},
                        "type": {"href": f"/api/v3/types/{arguments.get('type', 1)}"}
                    }
                }
                wp = await self.openproject_client.create_work_package(work_package_data)
                return {"work_package": self._convert_to_dict(wp)}
            
            elif tool_name == "generate_weekly_report":
                project_id = arguments.get("project_id")
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                if not all([project_id, start_date, end_date]):
                    raise ValueError("project_id, start_date, and end_date are required")
                report = await self.openproject_client.generate_weekly_report(project_id, start_date, end_date)
                return {"report": self._convert_to_dict(report)}
            
            elif tool_name == "generate_monthly_report":
                project_id = arguments.get("project_id")
                year = arguments.get("year")
                month = arguments.get("month")
                if not all([project_id, year, month]):
                    raise ValueError("project_id, year, and month are required")
                report = await self.openproject_client.generate_monthly_report(project_id, year, month)
                return {"report": self._convert_to_dict(report)}
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            return {"error": str(e), "tool": tool_name}
    
    def _convert_to_dict(self, obj) -> Dict[str, Any]:
        """Convert object to dictionary, handling both domain objects and mocks"""
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
            return obj.dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        elif isinstance(obj, dict):
            return obj
        else:
            # For mocks and other objects, try to get attributes
            result = {}
            for attr_name in dir(obj):
                if not attr_name.startswith('_'):
                    try:
                        attr_value = getattr(obj, attr_name)
                        if not callable(attr_value):
                            result[attr_name] = attr_value
                    except:
                        pass
            return result