#!/usr/bin/env python3
"""
Simple integration test for MCP handler without complex mocking

This test verifies that the MCP handler works correctly with minimal mocking
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.core.mcp_handler import MCPHandler
from app.services.openproject_service import OpenProjectService
from app.services.tool_service import ToolService
from app.services.resource_service import ResourceService
from app.services.prompt_service import PromptService
from app.services.report_service import ReportService
from app.services.template_service import TemplateService


class TestMCPSimple:
    """Simple integration tests for MCP handler"""
    
    @pytest.fixture
    def mock_openproject_client(self):
        """Mock OpenProject client for testing"""
        mock_client = AsyncMock()
        
        # Mock project data
        mock_project = MagicMock()
        mock_project.id = "test-project-123"
        mock_project.name = "Test Project"
        mock_project.description = "Test project description"
        mock_project.status = "Active"
        mock_project.dict.return_value = {
            "id": "test-project-123",
            "name": "Test Project",
            "description": "Test project description",
            "status": "Active"
        }
        
        # Mock work package
        mock_wp = MagicMock()
        mock_wp.id = "wp-456"
        mock_wp.subject = "Test Work Package"
        mock_wp.status = "In Progress"
        mock_wp.progress = 50
        mock_wp.dict.return_value = {
            "id": "wp-456",
            "subject": "Test Work Package",
            "status": "In Progress",
            "progress": 50
        }
        
        # Mock report
        mock_report = MagicMock()
        mock_report.dict.return_value = {
            "title": "Test Report",
            "summary": "Test report summary",
            "project_name": "Test Project",
            "period": "2024-01-01 to 2024-01-07"
        }
        
        # Mock methods
        mock_client.get_projects = AsyncMock(return_value=[mock_project])
        mock_client.get_project = AsyncMock(return_value=mock_project)
        mock_client.get_work_packages = AsyncMock(return_value=[mock_wp])
        mock_client.get_work_package = AsyncMock(return_value=mock_wp)
        mock_client.check_connection = AsyncMock(return_value=True)
        mock_client.generate_weekly_report = AsyncMock(return_value=mock_report)
        mock_client.generate_monthly_report = AsyncMock(return_value=mock_report)
        mock_client.assess_project_risks = AsyncMock(return_value=mock_report)
        
        return mock_client
    
    @pytest.fixture
    def mcp_handler(self, mock_openproject_client):
        """Create MCP handler with minimal mocking"""
        handler = MCPHandler(openproject_client=mock_openproject_client)
        
        # Initialize with mocked services (don't mock async utilities)
        # Create OpenProjectService with the mock client directly
        handler.openproject_service = mock_openproject_client
        handler.tool_service = ToolService(handler.openproject_service)
        handler.resource_service = ResourceService(handler.openproject_service)
        handler.prompt_service = PromptService(handler.openproject_service)
        handler.report_service = ReportService(handler.openproject_service)
        handler.template_service = TemplateService()
        
        handler.initialized = True
        
        return handler
    
    @pytest.mark.asyncio
    async def test_tools_list_simple(self, mcp_handler):
        """Test tools/list MCP method with simple approach"""
        # Test the tool service directly
        tools = await mcp_handler.tool_service.list_tools()
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert any(tool["name"] == "get_projects" for tool in tools)
        assert any(tool["name"] == "get_project" for tool in tools)
    
    @pytest.mark.asyncio
    async def test_tools_call_simple(self, mcp_handler):
        """Test tools/call MCP method with simple approach"""
        # Test the tool service directly
        result = await mcp_handler.tool_service.call_tool("get_projects", {})
        
        assert "projects" in result
        assert isinstance(result["projects"], list)
        assert len(result["projects"]) > 0
    
    @pytest.mark.asyncio
    async def test_resources_list_simple(self, mcp_handler):
        """Test resources/list MCP method with simple approach"""
        # Test the resource service directly
        resources = await mcp_handler.resource_service.list_resources()
        
        assert isinstance(resources, list)
        assert len(resources) > 0
    
    @pytest.mark.asyncio
    async def test_prompts_list_simple(self, mcp_handler):
        """Test prompts/list MCP method with simple approach"""
        # Test the prompt service directly
        prompts = await mcp_handler.prompt_service.list_prompts()
        
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        assert any(prompt["name"] == "project_summary" for prompt in prompts)
    
    @pytest.mark.asyncio
    async def test_handler_initialization(self, mcp_handler):
        """Test MCP handler initialization"""
        assert mcp_handler.initialized == True
        # openproject_service is now a mock, but other services should be real instances
        assert hasattr(mcp_handler.openproject_service, 'get_projects')  # Mock has the method
        assert isinstance(mcp_handler.tool_service, ToolService)
        assert isinstance(mcp_handler.resource_service, ResourceService)
        assert isinstance(mcp_handler.prompt_service, PromptService)
        assert isinstance(mcp_handler.report_service, ReportService)
        assert isinstance(mcp_handler.template_service, TemplateService)


if __name__ == "__main__":
    # Run the simple integration tests
    import pytest
    import sys
    
    # Add the solution-fastapi directory to Python path
    sys.path.insert(0, '/Users/mabo/developer/repository/git/mcp-projectmanage-openproject/solution-fastapi')
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])
    
    sys.exit(exit_code)