"""
Resource Service for MCP Protocol

Handles resource listing and reading with async optimizations.
"""
from typing import List, Dict, Any
from mcp_core.domain.interfaces.openproject_client import IOpenProjectClient


class ResourceService:
    """Service for managing MCP resources"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.openproject_client = openproject_client
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available MCP resources"""
        try:
            projects = await self.openproject_client.get_projects()
            
            resources = []
            for project in projects:
                resources.append({
                    "uri": f"openproject://projects/{project.id}",
                    "name": project.name,
                    "description": f"OpenProject: {project.name}",
                    "mimeType": "application/json"
                })
                
                # Add work packages for each project
                work_packages = await self.openproject_client.get_work_packages(project.id)
                for wp in work_packages:
                    resources.append({
                        "uri": f"openproject://work_packages/{wp.id}",
                        "name": f"{wp.subject} - {project.name}",
                        "description": f"Work Package: {wp.subject}",
                        "mimeType": "application/json"
                    })
            
            return resources
            
        except Exception as e:
            # Fallback to basic resources if OpenProject is unavailable
            return [
                {
                    "uri": "openproject://projects",
                    "name": "OpenProject Projects",
                    "description": "List of all OpenProject projects",
                    "mimeType": "application/json"
                },
                {
                    "uri": "openproject://work_packages",
                    "name": "OpenProject Work Packages",
                    "description": "List of all OpenProject work packages",
                    "mimeType": "application/json"
                }
            ]
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource"""
        try:
            if uri.startswith("openproject://projects/"):
                # Read specific project
                project_id = uri.split("/")[-1]
                if project_id == "projects":
                    # List all projects
                    projects = await self.openproject_client.get_projects()
                    content = {
                        "type": "project_list",
                        "projects": [project.dict() for project in projects]
                    }
                    return {"content": str(content), "mimeType": "application/json"}
                else:
                    # Get specific project
                    project = await self.openproject_client.get_project(project_id)
                    if project:
                        content = {
                            "type": "project",
                            "project": project.dict()
                        }
                        return {"content": str(content), "mimeType": "application/json"}
                    else:
                        return {"content": f"Project {project_id} not found", "mimeType": "text/plain"}
            
            elif uri.startswith("openproject://work_packages/"):
                # Read specific work package
                wp_id = uri.split("/")[-1]
                if wp_id == "work_packages":
                    # List all work packages
                    work_packages = await self.openproject_client.get_work_packages()
                    content = {
                        "type": "work_package_list",
                        "work_packages": [wp.dict() for wp in work_packages]
                    }
                    return {"content": str(content), "mimeType": "application/json"}
                else:
                    # Get specific work package
                    wp = await self.openproject_client.get_work_package(wp_id)
                    if wp:
                        content = {
                            "type": "work_package",
                            "work_package": wp.dict()
                        }
                        return {"content": str(content), "mimeType": "application/json"}
                    else:
                        return {"content": f"Work Package {wp_id} not found", "mimeType": "text/plain"}
            
            elif uri == "openproject://projects":
                projects = await self.openproject_client.get_projects()
                content = {
                    "type": "project_list",
                    "projects": [project.dict() for project in projects]
                }
                return {"content": str(content), "mimeType": "application/json"}
            
            elif uri == "openproject://work_packages":
                work_packages = await self.openproject_client.get_work_packages()
                content = {
                    "type": "work_package_list",
                    "work_packages": [wp.dict() for wp in work_packages]
                }
                return {"content": str(content), "mimeType": "application/json"}
            
            else:
                return {"content": f"Unknown resource URI: {uri}", "mimeType": "text/plain"}
                
        except Exception as e:
            return {"content": f"Error reading resource: {str(e)}", "mimeType": "text/plain"}