#!/usr/bin/env python3
"""
Integration test for MCP service layer

This test verifies that all service layers work together correctly
with proper async integration and error handling.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.openproject_service import OpenProjectService
from app.services.tool_service import ToolService
from app.services.resource_service import ResourceService
from app.services.prompt_service import PromptService
from app.services.report_service import ReportService
from app.services.template_service import TemplateService


class TestServiceIntegration:
    """Integration tests for MCP service layer"""
    
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
            "summary": "Test report summary"
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
    def openproject_service(self, mock_openproject_client):
        """Create OpenProject service with mocked client"""
        service = OpenProjectService(
            url="https://demo.openproject.org",
            api_key="test-api-key",
            http_client=mock_openproject_client
        )
        service._client = mock_openproject_client  # Skip initialization
        return service
    
    @pytest.fixture
    def tool_service(self, openproject_service):
        """Create Tool service"""
        return ToolService(openproject_service)
    
    @pytest.fixture
    def resource_service(self, openproject_service):
        """Create Resource service"""
        return ResourceService(openproject_service)
    
    @pytest.fixture
    def prompt_service(self, openproject_service):
        """Create Prompt service"""
        return PromptService(openproject_service)
    
    @pytest.fixture
    def report_service(self, openproject_service):
        """Create Report service"""
        return ReportService(openproject_service)
    
    @pytest.fixture
    def template_service(self):
        """Create Template service"""
        return TemplateService()
    
    @pytest.mark.asyncio
    async def test_tool_service_integration(self, tool_service):
        """Test ToolService integration with OpenProject"""
        # Test tool listing
        tools = await tool_service.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Test tool execution
        result = await tool_service.call_tool("get_projects", {})
        assert "projects" in result
        assert isinstance(result["projects"], list)
    
    @pytest.mark.asyncio
    async def test_resource_service_integration(self, resource_service):
        """Test ResourceService integration with OpenProject"""
        # Test resource listing
        resources = await resource_service.list_resources()
        assert isinstance(resources, list)
        assert len(resources) > 0
        
        # Test resource reading
        result = await resource_service.read_resource("openproject://projects")
        assert "content" in result
        assert "mimeType" in result
    
    @pytest.mark.asyncio
    async def test_prompt_service_integration(self, prompt_service):
        """Test PromptService integration with OpenProject"""
        # Test prompt listing
        prompts = await prompt_service.list_prompts()
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        
        # Test prompt generation
        result = await prompt_service.get_prompt("project_summary", {
            "project_id": "test-project-123"
        })
        assert "prompt" in result
        assert isinstance(result["prompt"], str)
        assert "Test Project" in result["prompt"]
    
    @pytest.mark.asyncio
    async def test_report_service_integration(self, report_service):
        """Test ReportService integration with OpenProject"""
        # Test report generation
        result = await report_service.generate_report("project_summary", {
            "project_id": "test-project-123"
        })
        assert "report_type" in result
        assert "project_id" in result
        assert "content" in result
        
        # Test weekly report
        weekly_result = await report_service.generate_report("weekly", {
            "project_id": "test-project-123",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        })
        assert weekly_result["report_type"] == "weekly"
    
    @pytest.mark.asyncio
    async def test_template_service_integration(self, template_service):
        """Test TemplateService functionality"""
        # Test template listing
        templates = await template_service.list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Test template retrieval
        template = await template_service.get_template("weekly_report")
        assert "name" in template
        assert "content" in template
        assert template["name"] == "weekly_report"
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, tool_service):
        """Test error handling across services"""
        # Test invalid tool call
        result = await tool_service.call_tool("invalid_tool", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]
        
        # Test missing parameters
        result = await tool_service.call_tool("get_project", {})
        assert "error" in result
        assert "project_id is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_service_interoperability(self, tool_service, resource_service, prompt_service):
        """Test that services work together seamlessly"""
        # Get projects using tool service
        tool_result = await tool_service.call_tool("get_projects", {})
        projects = tool_result["projects"]
        assert len(projects) > 0
        
        # Use project ID from tool service in resource service
        project_id = projects[0]["id"]
        resource_result = await resource_service.read_resource(f"openproject://projects/{project_id}")
        assert "content" in resource_result
        
        # Use project ID in prompt service
        prompt_result = await prompt_service.get_prompt("project_summary", {
            "project_id": project_id
        })
        assert "prompt" in prompt_result
        assert project_id in prompt_result["prompt"]


if __name__ == "__main__":
    # Run the integration tests
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