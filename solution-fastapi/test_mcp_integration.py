#!/usr/bin/env python3
"""
Integration test for MCP handler with all services

This test verifies that the MCP handler properly integrates with all service layers
and can handle various MCP protocol operations with async optimizations.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.mcp_handler import MCPHandler
from app.services.openproject_service import OpenProjectService
from app.services.tool_service import ToolService
from app.services.resource_service import ResourceService
from app.services.prompt_service import PromptService
from app.services.report_service import ReportService
from app.services.template_service import TemplateService


class TestMCPIntegration:
    """Integration tests for MCP handler with service layer"""
    
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
        
        # Mock methods - use async methods that return actual values
        mock_client.get_projects = AsyncMock(return_value=[mock_project])
        mock_client.get_project = AsyncMock(return_value=mock_project)
        mock_client.get_work_packages = AsyncMock(return_value=[mock_wp])
        mock_client.get_work_package = AsyncMock(return_value=mock_wp)
        mock_client.check_connection = AsyncMock(return_value=True)
        
        # Create proper report mock with dict method
        mock_report = MagicMock()
        mock_report.dict.return_value = {
            "title": "Test Report",
            "summary": "Test report summary",
            "project_name": "Test Project",
            "period": "2024-01-01 to 2024-01-07"
        }
        
        mock_client.generate_weekly_report = AsyncMock(return_value=mock_report)
        mock_client.generate_monthly_report = AsyncMock(return_value=mock_report)
        mock_client.assess_project_risks = AsyncMock(return_value=mock_report)
        
        return mock_client
    
    @pytest.fixture
    def mcp_handler(self, mock_openproject_client):
        """Create MCP handler with mocked dependencies"""
        handler = MCPHandler(openproject_client=mock_openproject_client)
        
        # Mock the async utilities to avoid complex setup
        with patch('app.core.mcp_handler.connection_pool'), \
             patch('app.core.mcp_handler.performance_monitor'), \
             patch('app.core.mcp_handler.AsyncTimeoutManager'), \
             patch('app.core.mcp_handler.async_retry'), \
             patch('app.core.mcp_handler.safe_async_execute'), \
             patch('app.core.mcp_handler.notify_mcp_operation'):
            
            # Initialize with mocked services
            handler.openproject_service = OpenProjectService(
                url="https://demo.openproject.org",
                api_key="test-api-key",
                http_client=mock_openproject_client
            )
            handler.tool_service = ToolService(handler.openproject_service)
            handler.resource_service = ResourceService(handler.openproject_service)
            handler.prompt_service = PromptService(handler.openproject_service)
            handler.report_service = ReportService(handler.openproject_service)
            handler.template_service = TemplateService()
            
            handler.initialized = True
            
            yield handler
    
    @pytest.mark.asyncio
    async def test_mcp_handler_initialization(self, mcp_handler, mock_openproject_client):
        """Test MCP handler initialization with mocked services"""
        assert mcp_handler.initialized == True
        assert isinstance(mcp_handler.openproject_service, OpenProjectService)
        assert isinstance(mcp_handler.tool_service, ToolService)
        assert isinstance(mcp_handler.resource_service, ResourceService)
        assert isinstance(mcp_handler.prompt_service, PromptService)
        assert isinstance(mcp_handler.report_service, ReportService)
        assert isinstance(mcp_handler.template_service, TemplateService)
    
    @pytest.mark.asyncio
    async def test_tools_list_integration(self, mcp_handler):
        """Test tools/list MCP method integration"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) > 0
        
        # Verify tool structure
        tools = response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        assert "get_projects" in tool_names
        assert "get_project" in tool_names
        assert "get_work_packages" in tool_names
    
    @pytest.mark.asyncio
    async def test_tools_call_integration(self, mcp_handler):
        """Test tools/call MCP method integration"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "get_projects",
                "arguments": {}
            }
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 2
        assert "result" in response
        assert "projects" in response["result"]
    
    @pytest.mark.asyncio
    async def test_resources_list_integration(self, mcp_handler):
        """Test resources/list MCP method integration"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 3
        assert "result" in response
        assert "resources" in response["result"]
        
        # Should return both fallback and actual resources
        resources = response["result"]["resources"]
        assert len(resources) >= 2  # At least the fallback resources
    
    @pytest.mark.asyncio
    async def test_prompts_list_integration(self, mcp_handler):
        """Test prompts/list MCP method integration"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "prompts/list",
            "params": {}
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 4
        assert "result" in response
        assert "prompts" in response["result"]
        
        prompts = response["result"]["prompts"]
        assert len(prompts) > 0
        prompt_names = [prompt["name"] for prompt in prompts]
        assert "project_summary" in prompt_names
        assert "weekly_report_template" in prompt_names
    
    @pytest.mark.asyncio
    async def test_prompts_get_integration(self, mcp_handler):
        """Test prompts/get MCP method integration"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "prompts/get",
            "params": {
                "name": "project_summary",
                "arguments": {
                    "project_id": "test-project-123"
                }
            }
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 5
        assert "result" in response
        assert "prompt" in response["result"]
        
        prompt = response["result"]["prompt"]
        assert isinstance(prompt, str)
        assert "Test Project" in prompt
    
    @pytest.mark.asyncio
    async def test_initialize_method(self, mcp_handler):
        """Test initialize MCP method"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "initialize",
            "params": {}
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 6
        assert "result" in response
        
        result = response["result"]
        assert "protocolVersion" in result
        assert "capabilities" in result
        assert "serverInfo" in result
        assert "performance" in result
        
        # Verify async capabilities
        capabilities = result["capabilities"]
        assert capabilities["tools"]["asyncSupport"] == True
        assert capabilities["resources"]["asyncSupport"] == True
        assert capabilities["prompts"]["asyncSupport"] == True
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_method(self, mcp_handler):
        """Test error handling for invalid MCP method"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "invalid_method",
            "params": {}
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 7
        assert "error" in response
        assert response["error"]["code"] == -32601  # MethodNotFound
    
    @pytest.mark.asyncio
    async def test_error_handling_missing_parameters(self, mcp_handler):
        """Test error handling for missing parameters"""
        request_body = json.dumps({
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {}  # Missing name parameter
        }).encode('utf-8')
        
        response = await mcp_handler.handle_request(request_body, "application/json")
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 8
        assert "error" in response
        assert response["error"]["code"] == -32600  # InvalidRequest


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