"""
OpenProject Adapter for FastMCP Solution

This module provides an async OpenProject API adapter for the FastMCP solution.
"""

import json
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.domain.models import Project, WorkPackage
from mcp_core.shared.exceptions import OpenProjectError, AuthenticationError, NotFoundError

from ..monitoring import monitor_openproject_request, logger


class OpenProjectAdapter(IOpenProjectClient):
    """Async OpenProject API adapter"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.logger = logger.bind(component="openproject_adapter")
        
        # Session configuration
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # API endpoints
        self.api_base = f"{self.base_url}/api/v3"
    
    async def __aenter__(self):
        """Initialize the adapter"""
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up the adapter"""
        if self.session:
            await self.session.close()
    
    @monitor_openproject_request("GET", "/projects")
    async def get_projects(self) -> List[Project]:
        """Get all projects from OpenProject"""
        try:
            async with self.session.get(f"{self.api_base}/projects") as response:
                if response.status == 200:
                    data = await response.json()
                    projects = []
                    
                    for project_data in data.get("_embedded", {}).get("elements", []):
                        project = Project(
                            id=project_data["id"],
                            identifier=project_data["identifier"],
                            name=project_data["name"],
                            description=project_data.get("description", {}).get("raw"),
                            status=project_data.get("status", {}).get("name"),
                            created_at=project_data.get("createdAt"),
                            updated_at=project_data.get("updatedAt")
                        )
                        projects.append(project)
                    
                    self.logger.info(f"Retrieved {len(projects)} projects")
                    return projects
                    
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                else:
                    raise OpenProjectError(f"Failed to get projects: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise OpenProjectError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenProjectError(f"JSON decode error: {str(e)}")
    
    @monitor_openproject_request("GET", "/projects/{project_id}")
    async def get_project(self, project_id: int) -> Optional[Project]:
        """Get a specific project from OpenProject"""
        try:
            async with self.session.get(f"{self.api_base}/projects/{project_id}") as response:
                if response.status == 200:
                    project_data = await response.json()
                    
                    project = Project(
                        id=project_data["id"],
                        identifier=project_data["identifier"],
                        name=project_data["name"],
                        description=project_data.get("description", {}).get("raw"),
                        status=project_data.get("status", {}).get("name"),
                        created_at=project_data.get("createdAt"),
                        updated_at=project_data.get("updatedAt")
                    )
                    
                    self.logger.info(f"Retrieved project: {project.name}")
                    return project
                    
                elif response.status == 404:
                    return None
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                else:
                    raise OpenProjectError(f"Failed to get project: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise OpenProjectError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenProjectError(f"JSON decode error: {str(e)}")
    
    @monitor_openproject_request("GET", "/work_packages")
    async def get_work_packages(self, project_id: Optional[int] = None) -> List[WorkPackage]:
        """Get work packages from OpenProject"""
        try:
            params = {}
            if project_id:
                params["filters"] = json.dumps([{"projectId": {"operator": "=", "values": [project_id]}}])
            
            async with self.session.get(f"{self.api_base}/work_packages", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    work_packages = []
                    
                    for wp_data in data.get("_embedded", {}).get("elements", []):
                        work_package = WorkPackage(
                            id=wp_data["id"],
                            subject=wp_data["subject"],
                            description=wp_data.get("description", {}).get("raw"),
                            type=wp_data.get("_type", {}).get("name"),
                            status=wp_data.get("status", {}).get("name"),
                            priority=wp_data.get("priority"),
                            assignee=wp_data.get("assignee", {}).get("name"),
                            project_id=wp_data.get("_links", {}).get("project", {}).get("href", "").split("/")[-1],
                            created_at=wp_data.get("createdAt"),
                            updated_at=wp_data.get("updatedAt")
                        )
                        work_packages.append(work_package)
                    
                    self.logger.info(f"Retrieved {len(work_packages)} work packages")
                    return work_packages
                    
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                else:
                    raise OpenProjectError(f"Failed to get work packages: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise OpenProjectError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenProjectError(f"JSON decode error: {str(e)}")
    
    @monitor_openproject_request("POST", "/work_packages")
    async def create_work_package(
        self,
        project_id: int,
        subject: str,
        description: Optional[str] = None,
        work_package_type: str = "Task",
        status: Optional[str] = None,
        priority: Optional[int] = None
    ) -> WorkPackage:
        """Create a new work package in OpenProject"""
        try:
            payload = {
                "subject": subject,
                "_type": work_package_type,
                "_links": {
                    "project": {"href": f"/api/v3/projects/{project_id}"}
                }
            }
            
            if description:
                payload["description"] = {"raw": description}
            
            if status:
                payload["status"] = status
            
            if priority:
                payload["priority"] = priority
            
            async with self.session.post(f"{self.api_base}/work_packages", json=payload) as response:
                if response.status == 201:
                    wp_data = await response.json()
                    
                    work_package = WorkPackage(
                        id=wp_data["id"],
                        subject=wp_data["subject"],
                        description=wp_data.get("description", {}).get("raw"),
                        type=wp_data.get("_type", {}).get("name"),
                        status=wp_data.get("status", {}).get("name"),
                        priority=wp_data.get("priority"),
                        project_id=project_id,
                        created_at=wp_data.get("createdAt"),
                        updated_at=wp_data.get("updatedAt")
                    )
                    
                    self.logger.info(f"Created work package: {work_package.subject}")
                    return work_package
                    
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 422:
                    raise OpenProjectError("Validation error: invalid work package data")
                else:
                    raise OpenProjectError(f"Failed to create work package: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise OpenProjectError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenProjectError(f"JSON decode error: {str(e)}")
    
    @monitor_openproject_request("PATCH", "/work_packages/{work_package_id}")
    async def update_work_package(
        self,
        work_package_id: int,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None
    ) -> WorkPackage:
        """Update a work package in OpenProject"""
        try:
            payload = {}
            lock_version = None
            
            # Get current work package to get lock version
            current_wp = await self.get_work_package_by_id(work_package_id)
            if not current_wp:
                raise NotFoundError(f"Work package {work_package_id} not found")
            
            if hasattr(current_wp, 'lock_version'):
                lock_version = current_wp.lock_version
            
            if subject is not None:
                payload["subject"] = subject
            
            if description is not None:
                payload["description"] = {"raw": description}
            
            if status is not None:
                payload["status"] = status
            
            if priority is not None:
                payload["priority"] = priority
            
            if lock_version:
                payload["lockVersion"] = lock_version
            
            async with self.session.patch(f"{self.api_base}/work_packages/{work_package_id}", json=payload) as response:
                if response.status == 200:
                    wp_data = await response.json()
                    
                    work_package = WorkPackage(
                        id=wp_data["id"],
                        subject=wp_data["subject"],
                        description=wp_data.get("description", {}).get("raw"),
                        type=wp_data.get("_type", {}).get("name"),
                        status=wp_data.get("status", {}).get("name"),
                        priority=wp_data.get("priority"),
                        project_id=wp_data.get("_links", {}).get("project", {}).get("href", "").split("/")[-1],
                        created_at=wp_data.get("createdAt"),
                        updated_at=wp_data.get("updatedAt")
                    )
                    
                    self.logger.info(f"Updated work package: {work_package.subject}")
                    return work_package
                    
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status == 404:
                    raise NotFoundError(f"Work package {work_package_id} not found")
                elif response.status == 409:
                    raise OpenProjectError("Conflict: work package was modified by another user")
                elif response.status == 422:
                    raise OpenProjectError("Validation error: invalid work package data")
                else:
                    raise OpenProjectError(f"Failed to update work package: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise OpenProjectError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenProjectError(f"JSON decode error: {str(e)}")
    
    async def get_work_package_by_id(self, work_package_id: int) -> Optional[WorkPackage]:
        """Get a specific work package by ID"""
        try:
            async with self.session.get(f"{self.api_base}/work_packages/{work_package_id}") as response:
                if response.status == 200:
                    wp_data = await response.json()
                    
                    work_package = WorkPackage(
                        id=wp_data["id"],
                        subject=wp_data["subject"],
                        description=wp_data.get("description", {}).get("raw"),
                        type=wp_data.get("_type", {}).get("name"),
                        status=wp_data.get("status", {}).get("name"),
                        priority=wp_data.get("priority"),
                        assignee=wp_data.get("assignee", {}).get("name"),
                        project_id=wp_data.get("_links", {}).get("project", {}).get("href", "").split("/")[-1],
                        created_at=wp_data.get("createdAt"),
                        updated_at=wp_data.get("updatedAt")
                    )
                    
                    return work_package
                    
                elif response.status == 404:
                    return None
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                else:
                    raise OpenProjectError(f"Failed to get work package: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise OpenProjectError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenProjectError(f"JSON decode error: {str(e)}")
    
    async def test_connection(self) -> bool:
        """Test the connection to OpenProject"""
        try:
            async with self.session.get(f"{self.api_base}/projects") as response:
                return response.status == 200
        except Exception:
            return False
    
    async def get_api_version(self) -> str:
        """Get the OpenProject API version"""
        try:
            async with self.session.get(f"{self.base_url}/api/v3") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("_type", "unknown")
                else:
                    return "unknown"
        except Exception:
            return "unknown"
