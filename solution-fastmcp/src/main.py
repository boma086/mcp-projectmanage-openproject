"""
FastMCP Server with Monitoring Integration

This is the main entry point for the FastMCP solution with comprehensive monitoring.
"""

import os
import asyncio
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

import uvicorn
from fastmcp import FastMCP, Server
from fastmcp.server.http import HTTPServer
from fastmcp.server.sse import SSEServer
import aiohttp.web

from mcp_core.application.mcp.handler import MCPHandler
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.logger import get_logger

from .adapters.openproject_adapter import OpenProjectAdapter
from .monitoring import (
    get_monitoring, 
    get_health_checker,
    HealthStatus,
    logger as monitoring_logger
)


class FastMCPServer:
    """FastMCP Server with monitoring integration"""
    
    def __init__(self):
        self.app = FastMCP("OpenProject MCP Server")
        self.mcp_handler = None
        self.openproject_client = None
        self.health_checker = None
        self.monitoring = get_monitoring()
        self.logger = monitoring_logger.bind(component="fastmcp_server")
        
        # Configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8030"))
        self.openproject_url = os.getenv("OPENPROJECT_URL")
        self.openproject_api_key = os.getenv("OPENPROJECT_API_KEY")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # Session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize servers
        self.http_server = None
        self.sse_server = None
    
    async def initialize(self) -> None:
        """Initialize the FastMCP server"""
        try:
            self.logger.info("Initializing FastMCP server", 
                           host=self.host, 
                           port=self.port,
                           openproject_url=self.openproject_url)
            
            # Validate configuration
            if not self.openproject_url or not self.openproject_api_key:
                raise ValueError("OPENPROJECT_URL and OPENPROJECT_API_KEY are required")
            
            # Initialize OpenProject client
            self.openproject_client = OpenProjectAdapter(
                base_url=self.openproject_url,
                api_key=self.openproject_api_key
            )
            
            # Initialize MCP handler
            self.mcp_handler = MCPHandler(self.openproject_client)
            
            # Initialize health checker
            self.health_checker = get_health_checker(
                self.openproject_url, 
                self.openproject_api_key
            )
            
            # Setup monitoring endpoints
            await self._setup_monitoring_endpoints()
            
            # Setup MCP tools and resources
            await self._setup_mcp_tools()
            
            self.logger.info("FastMCP server initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize FastMCP server", error=str(e))
            raise
    
    async def _setup_monitoring_endpoints(self) -> None:
        """Setup monitoring endpoints"""
        
        @self.app.get("/health/live")
        async def liveness_check():
            """Liveness check endpoint"""
            async with self.monitoring.monitor_request("GET", "/health/live"):
                health_summary = await self.health_checker.check_liveness()
                
                status_code = 200 if health_summary.overall_status == HealthStatus.HEALTHY else 503
                
                return {
                    "status": health_summary.overall_status.value,
                    "timestamp": health_summary.timestamp,
                    "checks": [
                        {
                            "name": result.name,
                            "status": result.status.value,
                            "duration_ms": result.duration_ms,
                            "message": result.message
                        }
                        for result in health_summary.results
                    ]
                }, status_code
        
        @self.app.get("/health/ready")
        async def readiness_check():
            """Readiness check endpoint"""
            async with self.monitoring.monitor_request("GET", "/health/ready"):
                health_summary = await self.health_checker.check_readiness()
                
                status_code = 200 if health_summary.overall_status == HealthStatus.HEALTHY else 503
                
                return {
                    "status": health_summary.overall_status.value,
                    "timestamp": health_summary.timestamp,
                    "checks": [
                        {
                            "name": result.name,
                            "status": result.status.value,
                            "duration_ms": result.duration_ms,
                            "message": result.message
                        }
                        for result in health_summary.results
                    ]
                }, status_code
        
        @self.app.get("/health/deep")
        async def deep_health_check():
            """Deep health check endpoint"""
            async with self.monitoring.monitor_request("GET", "/health/deep"):
                health_summary = await self.health_checker.check_deep_health()
                
                status_code = 200 if health_summary.overall_status == HealthStatus.HEALTHY else 503
                
                return {
                    "status": health_summary.overall_status.value,
                    "timestamp": health_summary.timestamp,
                    "total_checks": health_summary.total_checks,
                    "healthy_checks": health_summary.healthy_checks,
                    "degraded_checks": health_summary.degraded_checks,
                    "unhealthy_checks": health_summary.unhealthy_checks,
                    "checks": [
                        {
                            "name": result.name,
                            "status": result.status.value,
                            "duration_ms": result.duration_ms,
                            "message": result.message,
                            "details": result.details
                        }
                        for result in health_summary.results
                    ]
                }, status_code
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus metrics endpoint"""
            async with self.monitoring.monitor_request("GET", "/metrics"):
                metrics_data = self.monitoring.metrics.get_metrics()
                
                return {
                    "content": metrics_data,
                    "content_type": "text/plain; version=0.0.4"
                }
        
        @self.app.get("/")
        async def root():
            """Root endpoint with service info"""
            async with self.monitoring.monitor_request("GET", "/"):
                return {
                    "service": "OpenProject FastMCP Server",
                    "version": "1.0.0",
                    "architecture": "fastmcp-native",
                    "endpoints": {
                        "mcp": "/mcp",
                        "health": "/health",
                        "metrics": "/metrics"
                    },
                    "documentation": "https://github.com/modelcontextprotocol/python-sdk"
                }
    
    async def _setup_mcp_tools(self) -> None:
        """Setup MCP tools and resources"""
        
        @self.app.tool()
        async def get_projects():
            """Get all projects from OpenProject"""
            async with self.monitoring.monitor_mcp_operation("get_projects", "projects"):
                projects = await self.openproject_client.get_projects()
                return {"projects": projects}
        
        @self.app.tool()
        async def get_project(project_id: int):
            """Get a specific project from OpenProject"""
            async with self.monitoring.monitor_mcp_operation("get_project", "projects"):
                project = await self.openproject_client.get_project(project_id)
                return {"project": project}
        
        @self.app.tool()
        async def get_work_packages(project_id: int = None):
            """Get work packages from OpenProject"""
            async with self.monitoring.monitor_mcp_operation("get_work_packages", "work_packages"):
                work_packages = await self.openproject_client.get_work_packages(project_id)
                return {"work_packages": work_packages}
        
        @self.app.tool()
        async def create_work_package(
            project_id: int,
            subject: str,
            description: str = None,
            work_package_type: str = "Task"
        ):
            """Create a new work package in OpenProject"""
            async with self.monitoring.monitor_mcp_operation("create_work_package", "work_packages"):
                work_package = await self.openproject_client.create_work_package(
                    project_id=project_id,
                    subject=subject,
                    description=description,
                    work_package_type=work_package_type
                )
                return {"work_package": work_package}
        
        @self.app.tool()
        async def update_work_package(
            work_package_id: int,
            subject: str = None,
            description: str = None,
            status: str = None
        ):
            """Update a work package in OpenProject"""
            async with self.monitoring.monitor_mcp_operation("update_work_package", "work_packages"):
                work_package = await self.openproject_client.update_work_package(
                    work_package_id=work_package_id,
                    subject=subject,
                    description=description,
                    status=status
                )
                return {"work_package": work_package}
        
        @self.app.tool()
        async def generate_project_report(project_id: int):
            """Generate a project report"""
            async with self.monitoring.monitor_mcp_operation("generate_project_report", "reports"):
                # Get project data
                project = await self.openproject_client.get_project(project_id)
                work_packages = await self.openproject_client.get_work_packages(project_id)
                
                # Generate report
                report = {
                    "project": project,
                    "work_packages": work_packages,
                    "generated_at": datetime.now().isoformat(),
                    "total_work_packages": len(work_packages),
                    "summary": {
                        "total_tasks": len([wp for wp in work_packages if wp.get("type") == "Task"]),
                        "total_bugs": len([wp for wp in work_packages if wp.get("type") == "Bug"]),
                        "total_features": len([wp for wp in work_packages if wp.get("type") == "Feature"])
                    }
                }
                
                return {"report": report}
    
    async def handle_mcp_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request with monitoring"""
        request_id = request_data.get("id", "unknown")
        method = request_data.get("method", "unknown")
        
        # Register session if this is an initialize request
        if method == "initialize":
            session_id = f"session_{request_id}_{int(time.time())}"
            self.active_sessions[session_id] = {
                "id": session_id,
                "created_at": time.time(),
                "client_info": request_data.get("params", {}).get("clientInfo", {})
            }
            self.health_checker.register_session(session_id)
        
        async with self.monitoring.monitor_mcp_protocol_operation(method):
            try:
                # Handle MCP request
                result = await self.mcp_handler.handle_request(request_data)
                
                # Record successful operation
                self.monitoring.metrics.record_mcp_operation(
                    method, 
                    "mcp_protocol", 
                    "success", 
                    0  # Duration is handled by the context manager
                )
                
                return result
                
            except Exception as e:
                # Record failed operation
                self.monitoring.metrics.record_mcp_operation(
                    method, 
                    "mcp_protocol", 
                    "error", 
                    0  # Duration is handled by the context manager
                )
                
                raise
    
    async def start(self) -> None:
        """Start the FastMCP server"""
        try:
            await self.initialize()
            
            self.logger.info("Starting FastMCP server", 
                           host=self.host, 
                           port=self.port)
            
            # Start HTTP server
            self.http_server = HTTPServer(
                app=self.app,
                host=self.host,
                port=self.port
            )
            
            # Start SSE server
            self.sse_server = SSEServer(
                app=self.app,
                host=self.host,
                port=self.port + 1  # Different port for SSE
            )
            
            # Start both servers
            await asyncio.gather(
                self.http_server.start(),
                self.sse_server.start()
            )
            
        except Exception as e:
            self.logger.error("Failed to start FastMCP server", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop the FastMCP server"""
        try:
            self.logger.info("Stopping FastMCP server")
            
            # Stop servers
            if self.http_server:
                await self.http_server.stop()
            
            if self.sse_server:
                await self.sse_server.stop()
            
            # Clean up sessions
            for session_id in list(self.active_sessions.keys()):
                self.health_checker.unregister_session(session_id)
            
            self.logger.info("FastMCP server stopped")
            
        except Exception as e:
            self.logger.error("Error stopping FastMCP server", error=str(e))


async def main():
    """Main entry point"""
    server = FastMCPServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
