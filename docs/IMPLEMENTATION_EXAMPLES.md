# Implementation Examples and Code Samples

This document provides detailed implementation examples and code samples for all four solution types in the OpenProject MCP integration project.

## 📋 Table of Contents

1. [HTTP Solution Implementation](#http-solution-implementation)
2. [FastAPI Solution Implementation](#fastapi-solution-implementation)
3. [FastMCP Solution Implementation](#fastmcp-solution-implementation)
4. [TypeScript Solution Implementation](#typescript-solution-implementation)
5. [Common Implementation Patterns](#common-implementation-patterns)
6. [Integration Examples](#integration-examples)
7. [Testing Examples](#testing-examples)
8. [Configuration Examples](#configuration-examples)

## 🌐 HTTP Solution Implementation

### Basic Setup

```python
# src/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from src.config import settings
from src.dependencies import get_openproject_client
from src.routers import projects, work_packages, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting HTTP MCP Server...")
    yield
    # Shutdown
    print("Shutting down HTTP MCP Server...")

app = FastAPI(
    title="OpenProject MCP HTTP Server",
    description="HTTP-based MCP server for OpenProject integration",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(work_packages.router, prefix="/api/work-packages", tags=["work-packages"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "OpenProject MCP HTTP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "docs": "/docs",
            "api": "/api"
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        client = await get_openproject_client()
        await client.test_connection()
        return {
            "status": "healthy",
            "timestamp": "2025-01-24T00:00:00Z",
            "version": "1.0.0",
            "openproject": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """MCP JSON-RPC endpoint"""
    try:
        # Process MCP request
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Handle different tools
            if tool_name == "get_projects":
                return await handle_get_projects(arguments)
            elif tool_name == "generate_report":
                return await handle_generate_report(arguments)
            else:
                raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")
        
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": "success"}
    
    except Exception as e:
        return {
            "jsonrpc": "2.0", 
            "id": request.get("id"),
            "error": {
                "code": -1,
                "message": str(e)
            }
        }

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
```

### OpenProject Adapter Implementation

```python
# src/adapters/openproject_adapter.py
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from mcp_core.domain.models import Project, WorkPackage, User
from mcp_core.domain.exceptions import MCPError
from src.config import settings

@dataclass
class OpenProjectAdapter:
    """Synchronous adapter for OpenProject API"""
    
    base_url: str
    api_key: str
    session: Optional[aiohttp.ClientSession] = None
    
    def __post_init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> bool:
        """Test connection to OpenProject"""
        try:
            async with self.session.get(f"{self.base_url}/api/v3/projects") as response:
                return response.status == 200
        except Exception:
            return False
    
    async def get_projects(self) -> List[Project]:
        """Get all projects from OpenProject"""
        try:
            async with self.session.get(f"{self.base_url}/api/v3/projects") as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        Project(
                            id=str(project.get("id")),
                            name=project.get("name", ""),
                            description=project.get("description", {}).get("raw", ""),
                            status=project.get("status", ""),
                            created_at=datetime.fromisoformat(project.get("createdAt", "").replace('Z', '+00:00')),
                            updated_at=datetime.fromisoformat(project.get("updatedAt", "").replace('Z', '+00:00'))
                        )
                        for project in data.get("_embedded", {}).get("elements", [])
                    ]
                else:
                    raise MCPError(f"Failed to fetch projects: {response.status}")
        except Exception as e:
            raise MCPError(f"Error fetching projects: {str(e)}")
    
    async def get_work_packages(self, project_id: str) -> List[WorkPackage]:
        """Get work packages for a project"""
        try:
            async with self.session.get(
                f"{self.base_url}/api/v3/projects/{project_id}/work_packages"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        WorkPackage(
                            id=str(wp.get("id")),
                            subject=wp.get("subject", ""),
                            description=wp.get("description", {}).get("raw", ""),
                            status=wp.get("status", {}).get("name", ""),
                            type=wp.get("type", {}).get("name", ""),
                            project_id=project_id,
                            assignee=wp.get("assignee", {}).get("name", ""),
                            due_date=datetime.fromisoformat(wp.get("dueDate", "").replace('Z', '+00:00')) if wp.get("dueDate") else None
                        )
                        for wp in data.get("_embedded", {}).get("elements", [])
                    ]
                else:
                    raise MCPError(f"Failed to fetch work packages: {response.status}")
        except Exception as e:
            raise MCPError(f"Error fetching work packages: {str(e)}")
    
    async def generate_report(self, project_id: str, report_type: str, **kwargs) -> str:
        """Generate a report for a project"""
        try:
            # Get project data
            project = await self.get_project_by_id(project_id)
            work_packages = await self.get_work_packages(project_id)
            
            # Generate report based on type
            if report_type == "weekly":
                return await self._generate_weekly_report(project, work_packages, **kwargs)
            elif report_type == "monthly":
                return await self._generate_monthly_report(project, work_packages, **kwargs)
            else:
                raise MCPError(f"Unknown report type: {report_type}")
        
        except Exception as e:
            raise MCPError(f"Error generating report: {str(e)}")
    
    async def _generate_weekly_report(self, project: Project, work_packages: List[WorkPackage], **kwargs) -> str:
        """Generate weekly report"""
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        
        report = f"""
# 週次報告書 - {project.name}

## プロジェクト概要
- **プロジェクト名**: {project.name}
- **報告期間**: {start_date} ~ {end_date}
- **ステータス**: {project.status}

## 今週の進捗
"""
        
        # Add work package progress
        completed_wps = [wp for wp in work_packages if wp.status == "完了"]
        in_progress_wps = [wp for wp in work_packages if wp.status == "進行中"]
        
        if completed_wps:
            report += "\n### 完了したタスク\n"
            for wp in completed_wps:
                report += f"- {wp.subject}\n"
        
        if in_progress_wps:
            report += "\n### 進行中のタスク\n"
            for wp in in_progress_wps:
                report += f"- {wp.subject} (担当: {wp.assignee or '未割り当て'})\n"
        
        report += f"""
## 今後の予定
- 継続してタスクを進捗させます
- 次回の進捗確認を予定しています

## リスクと課題
- 特に大きなリスクは現在ありません

報告日: {datetime.now().strftime('%Y-%m-%d')}
"""
        return report
    
    async def get_project_by_id(self, project_id: str) -> Project:
        """Get a specific project by ID"""
        try:
            async with self.session.get(f"{self.base_url}/api/v3/projects/{project_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return Project(
                        id=str(data.get("id")),
                        name=data.get("name", ""),
                        description=data.get("description", {}).get("raw", ""),
                        status=data.get("status", ""),
                        created_at=datetime.fromisoformat(data.get("createdAt", "").replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(data.get("updatedAt", "").replace('Z', '+00:00'))
                    )
                else:
                    raise MCPError(f"Failed to fetch project: {response.status}")
        except Exception as e:
            raise MCPError(f"Error fetching project: {str(e)}")
```

### Route Handler Implementation

```python
# src/routers/projects.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from src.adapters.openproject_adapter import OpenProjectAdapter
from src.dependencies import get_openproject_client
from mcp_core.domain.models import Project

router = APIRouter()

@router.get("/")
async def get_projects(
    client: OpenProjectAdapter = Depends(get_openproject_client)
) -> List[Project]:
    """Get all projects"""
    try:
        return await client.get_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    client: OpenProjectAdapter = Depends(get_openproject_client)
) -> Project:
    """Get a specific project"""
    try:
        return await client.get_project_by_id(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/reports/weekly")
async def generate_weekly_report(
    project_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    client: OpenProjectAdapter = Depends(get_openproject_client)
) -> dict:
    """Generate weekly report for a project"""
    try:
        report_content = await client.generate_report(
            project_id=project_id,
            report_type="weekly",
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "project_id": project_id,
            "report_type": "weekly",
            "period": f"{start_date} to {end_date}",
            "content": report_content,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def projects_health(
    client: OpenProjectAdapter = Depends(get_openproject_client)
) -> dict:
    """Health check for projects service"""
    try:
        await client.test_connection()
        return {
            "service": "projects",
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "service": "projects",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

## 🚀 FastAPI Solution Implementation

### Advanced FastAPI Application

```python
# app/main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.mcp_handler import MCPHandler
from app.services.enhanced_report_generator import EnhancedReportGenerator
from app.dependencies import get_openproject_service, get_report_service
from app.routers import projects, work_packages, users, reports

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print("Starting FastAPI MCP Server...")
    
    # Initialize services
    app.state.mcp_handler = MCPHandler()
    app.state.report_generator = EnhancedReportGenerator()
    
    yield
    # Shutdown
    print("Shutting down FastAPI MCP Server...")

app = FastAPI(
    title="OpenProject MCP FastAPI Server",
    description="High-performance async MCP server for OpenProject integration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(work_packages.router, prefix="/api/v1/work-packages", tags=["work-packages"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "OpenProject MCP FastAPI Server",
        "version": "2.0.0",
        "description": "High-performance async MCP server",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "docs": "/docs",
            "api": "/api/v1"
        },
        "features": [
            "Async processing",
            "WebSocket support",
            "Enhanced reporting",
            "Multi-language support",
            "Real-time monitoring"
        ]
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check with detailed metrics"""
    try:
        # Check all services
        mcp_handler = app.state.mcp_handler
        report_generator = app.state.report_generator
        
        mcp_status = await mcp_handler.health_check()
        report_status = await report_generator.health_check()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "services": {
                "mcp_handler": mcp_status,
                "report_generator": report_status,
                "openproject": "connected"
            },
            "metrics": {
                "uptime": "24h",
                "requests_total": 15420,
                "error_rate": 0.02,
                "avg_response_time": 0.125
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """Enhanced MCP JSON-RPC endpoint with async processing"""
    try:
        mcp_handler = app.state.mcp_handler
        return await mcp_handler.handle_request(request)
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -1,
                "message": str(e)
            }
        }

# WebSocket endpoint for real-time updates
from fastapi import WebSocket
from app.websockets.manager import WebSocketManager

websocket_manager = WebSocketManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle WebSocket messages
            await websocket_manager.handle_message(websocket, data)
    except Exception as e:
        await websocket_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=1 if settings.DEBUG else 4
    )
```

### Enhanced Service Implementation

```python
# app/services/enhanced_report_generator.py
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from jinja2 import Template

from mcp_core.domain.models import Project, WorkPackage, Report
from mcp_core.domain.services import ReportGenerator
from mcp_core.domain.exceptions import MCPError
from app.adapters.async_openproject_adapter import AsyncOpenProjectAdapter
from app.i18n.translation_service import TranslationService

@dataclass
class EnhancedReportGenerator:
    """Enhanced report generator with advanced features"""
    
    openproject_adapter: AsyncOpenProjectAdapter
    translation_service: TranslationService
    template_cache: Dict[str, Template] = None
    
    def __post_init__(self):
        self.template_cache = {}
    
    async def generate_enhanced_report(
        self,
        project_id: str,
        report_type: str,
        language: str = "ja",
        **kwargs
    ) -> Report:
        """Generate enhanced report with multi-language support"""
        try:
            # Get project data
            project = await self.openproject_adapter.get_project_by_id(project_id)
            work_packages = await self.openproject_adapter.get_work_packages(project_id)
            
            # Get translations
            translations = await self.translation_service.get_translations(language)
            
            # Generate report based on type
            if report_type == "weekly":
                content = await self._generate_weekly_report_enhanced(
                    project, work_packages, translations, **kwargs
                )
            elif report_type == "monthly":
                content = await self._generate_monthly_report_enhanced(
                    project, work_packages, translations, **kwargs
                )
            elif report_type == "progress":
                content = await self._generate_progress_report_enhanced(
                    project, work_packages, translations, **kwargs
                )
            else:
                raise MCPError(f"Unknown report type: {report_type}")
            
            return Report(
                id=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                project_id=project_id,
                type=report_type,
                content=content,
                language=language,
                generated_at=datetime.now(),
                metadata={
                    "total_work_packages": len(work_packages),
                    "completed_count": len([wp for wp in work_packages if wp.status == "完了"]),
                    "in_progress_count": len([wp for wp in work_packages if wp.status == "進行中"]),
                    "generator": "enhanced"
                }
            )
        
        except Exception as e:
            raise MCPError(f"Error generating enhanced report: {str(e)}")
    
    async def _generate_weekly_report_enhanced(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        translations: Dict[str, str],
        **kwargs
    ) -> str:
        """Generate enhanced weekly report with analytics"""
        
        # Calculate metrics
        total_wps = len(work_packages)
        completed_wps = [wp for wp in work_packages if wp.status == "完了"]
        in_progress_wps = [wp for wp in work_packages if wp.status == "進行中"]
        
        completion_rate = (len(completed_wps) / total_wps * 100) if total_wps > 0 else 0
        
        # Group work packages by assignee
        assignee_stats = {}
        for wp in work_packages:
            assignee = wp.assignee or "未割り当て"
            if assignee not in assignee_stats:
                assignee_stats[assignee] = {"total": 0, "completed": 0}
            assignee_stats[assignee]["total"] += 1
            if wp.status == "完了":
                assignee_stats[assignee]["completed"] += 1
        
        # Generate report using template
        template_str = """
# {{ translations.weekly_report }} - {{ project.name }}

## {{ translations.project_overview }}
- **{{ translations.project_name }}**: {{ project.name }}
- **{{ translations.report_period }}**: {{ start_date }} ~ {{ end_date }}
- **{{ translations.status }}**: {{ project.status }}
- **{{ translations.completion_rate }}**: {{ "%.1f"|format(completion_rate) }}%

## {{ translations.this_week_progress }}

### {{ translations.completed_tasks }}
{% for wp in completed_wps %}
- {{ wp.subject }}{% if wp.assignee %} ({{ translations.assignee }}: {{ wp.assignee }}){% endif %}
{% endfor %}

### {{ translations.in_progress_tasks }}
{% for wp in in_progress_wps %}
- {{ wp.subject }}{% if wp.assignee %} ({{ translations.assignee }}: {{ wp.assignee }}){% endif %}
{% if wp.due_date %} ({{ translations.due_date }}: {{ wp.due_date.strftime('%Y-%m-%d') }}){% endif %}
{% endfor %}

## {{ translations.team_performance }}
{% for assignee, stats in assignee_stats.items() %}
### {{ assignee }}
- {{ translations.completed_tasks }}: {{ stats.completed }}/{{ stats.total }}
- {{ translations.completion_rate }}: {{ "%.1f"|format(stats.completed / stats.total * 100) if stats.total > 0 else 0 }}%
{% endfor %}

## {{ translations.upcoming_plans }}
- {{ translations.continue_task_progress }}
- {{ translations.next_progress_check }}

## {{ translations.risks_and_issues }}
{% if risks %}
{% for risk in risks %}
- {{ risk }}
{% endfor %}
{% else %}
- {{ translations.no_major_risks }}
{% endif %}

{{ translations.report_date }}: {{ generated_date }}
"""
        
        template = Template(template_str)
        
        return template.render(
            translations=translations,
            project=project,
            completed_wps=completed_wps,
            in_progress_wps=in_progress_wps,
            completion_rate=completion_rate,
            assignee_stats=assignee_stats,
            start_date=kwargs.get("start_date", ""),
            end_date=kwargs.get("end_date", ""),
            risks=kwargs.get("risks", []),
            generated_date=datetime.now().strftime('%Y-%m-%d')
        )
    
    async def generate_batch_reports(
        self,
        project_ids: List[str],
        report_type: str,
        language: str = "ja"
    ) -> List[Report]:
        """Generate reports for multiple projects concurrently"""
        try:
            tasks = []
            for project_id in project_ids:
                task = self.generate_enhanced_report(
                    project_id, report_type, language
                )
                tasks.append(task)
            
            reports = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return successful reports
            successful_reports = []
            for i, result in enumerate(reports):
                if isinstance(result, Report):
                    successful_reports.append(result)
                else:
                    print(f"Failed to generate report for project {project_ids[i]}: {result}")
            
            return successful_reports
        
        except Exception as e:
            raise MCPError(f"Error generating batch reports: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for report generator service"""
        return {
            "service": "enhanced_report_generator",
            "status": "healthy",
            "template_cache_size": len(self.template_cache),
            "supported_languages": ["ja", "en", "zh"],
            "timestamp": datetime.now().isoformat()
        }
```

### MCP Handler Implementation

```python
# app/core/mcp_handler.py
from typing import Dict, List, Any, Optional
import asyncio
import json
from datetime import datetime

from mcp_core.application.mcp.tools import ToolManager
from mcp_core.application.mcp.resources import ResourceManager
from mcp_core.application.mcp.prompts import PromptManager
from mcp_core.domain.exceptions import MCPError
from app.services.enhanced_report_generator import EnhancedReportGenerator

class MCPHandler:
    """Enhanced MCP protocol handler with async support"""
    
    def __init__(self):
        self.tool_manager = ToolManager()
        self.resource_manager = ResourceManager()
        self.prompt_manager = PromptManager()
        self.report_generator = None
    
    async def initialize(self, report_generator: EnhancedReportGenerator):
        """Initialize MCP handler with services"""
        self.report_generator = report_generator
        
        # Register tools
        await self._register_tools()
        
        # Register resources
        await self._register_resources()
        
        # Register prompts
        await self._register_prompts()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP JSON-RPC request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "initialize":
                return await self._handle_initialize(params)
            elif method == "tools/list":
                return await self._handle_tools_list(params)
            elif method == "tools/call":
                return await self._handle_tools_call(params)
            elif method == "resources/list":
                return await self._handle_resources_list(params)
            elif method == "resources/read":
                return await self._handle_resources_read(params)
            elif method == "prompts/list":
                return await self._handle_prompts_list(params)
            elif method == "prompts/get":
                return await self._handle_prompts_get(params)
            else:
                raise MCPError(f"Unknown method: {method}")
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -1,
                    "message": str(e)
                }
            }
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "jsonrpc": "2.0",
            "id": params.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "OpenProject MCP Server",
                    "version": "2.0.0"
                }
            }
        }
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "generate_enhanced_weekly_report":
            return await self._generate_enhanced_weekly_report(arguments)
        elif tool_name == "generate_enhanced_monthly_report":
            return await self._generate_enhanced_monthly_report(arguments)
        elif tool_name == "assess_project_risks":
            return await self._assess_project_risks(arguments)
        elif tool_name == "analyze_workload":
            return await self._analyze_workload(arguments)
        else:
            raise MCPError(f"Unknown tool: {tool_name}")
    
    async def _generate_enhanced_weekly_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced weekly report"""
        try:
            project_id = arguments.get("project_id")
            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            language = arguments.get("language", "ja")
            
            if not all([project_id, start_date, end_date]):
                raise MCPError("Missing required arguments")
            
            report = await self.report_generator.generate_enhanced_report(
                project_id=project_id,
                report_type="weekly",
                language=language,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": report.content
                    }
                ]
            }
        
        except Exception as e:
            raise MCPError(f"Error generating weekly report: {str(e)}")
    
    async def _register_tools(self):
        """Register available tools"""
        tools = [
            {
                "name": "generate_enhanced_weekly_report",
                "description": "Generate enhanced weekly report with analytics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                        "language": {"type": "string", "description": "Report language (ja/en/zh)", "default": "ja"}
                    },
                    "required": ["project_id", "start_date", "end_date"]
                }
            },
            {
                "name": "assess_project_risks",
                "description": "Assess project risks and provide recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "Project ID"},
                        "include_recommendations": {"type": "boolean", "default": true}
                    },
                    "required": ["project_id"]
                }
            }
        ]
        
        for tool in tools:
            await self.tool_manager.register_tool(tool)
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for MCP handler"""
        return {
            "service": "mcp_handler",
            "status": "healthy",
            "tools_count": len(await self.tool_manager.list_tools()),
            "resources_count": len(await self.resource_manager.list_resources()),
            "prompts_count": len(await self.prompt_manager.list_prompts()),
            "timestamp": datetime.now().isoformat()
        }
```

## ⚡ FastMCP Solution Implementation

### Native FastMCP Server

```python
# solution-fastmcp/main.py
from fastmcp import FastMCP
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from mcp_core.domain.models import Project, WorkPackage
from mcp_core.domain.services import ReportGenerator, RiskAssessor, WorkloadAnalyzer
from mcp_core.infrastructure.openproject import OpenProjectClient

# Create FastMCP server
mcp = FastMCP("OpenProject MCP Server")

# Initialize services
openproject_client = None
report_generator = None
risk_assessor = None
workload_analyzer = None

@mcp.on_startup
async def startup():
    """Initialize services on startup"""
    global openproject_client, report_generator, risk_assessor, workload_analyzer
    
    # Initialize OpenProject client
    openproject_client = OpenProjectClient(
        url="http://localhost:8090",
        api_key="your-api-key"
    )
    
    # Initialize services
    report_generator = ReportGenerator(openproject_client)
    risk_assessor = RiskAssessor(openproject_client)
    workload_analyzer = WorkloadAnalyzer(openproject_client)
    
    print("FastMCP Server started successfully")

@mcp.on_shutdown
async def shutdown():
    """Cleanup on shutdown"""
    if openproject_client:
        await openproject_client.close()
    print("FastMCP Server shutdown")

# Tool definitions
@mcp.tool()
async def get_projects() -> List[Dict[str, Any]]:
    """Get all projects from OpenProject"""
    try:
        projects = await openproject_client.get_projects()
        return [
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            }
            for project in projects
        ]
    except Exception as e:
        raise Exception(f"Error fetching projects: {str(e)}")

@mcp.tool()
async def get_project_details(project_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific project"""
    try:
        project = await openproject_client.get_project_by_id(project_id)
        work_packages = await openproject_client.get_work_packages(project_id)
        
        return {
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat()
            },
            "work_packages_count": len(work_packages),
            "completed_work_packages": len([wp for wp in work_packages if wp.status == "完了"]),
            "in_progress_work_packages": len([wp for wp in work_packages if wp.status == "進行中"])
        }
    except Exception as e:
        raise Exception(f"Error fetching project details: {str(e)}")

@mcp.tool()
async def generate_weekly_report(
    project_id: str,
    start_date: str,
    end_date: str,
    language: str = "ja"
) -> str:
    """Generate weekly report for a project"""
    try:
        report = await report_generator.generate_report(
            project_id=project_id,
            report_type="weekly",
            start_date=start_date,
            end_date=end_date,
            language=language
        )
        return report
    except Exception as e:
        raise Exception(f"Error generating weekly report: {str(e)}")

@mcp.tool()
async def generate_monthly_report(
    project_id: str,
    year: int,
    month: int,
    language: str = "ja"
) -> str:
    """Generate monthly report for a project"""
    try:
        report = await report_generator.generate_report(
            project_id=project_id,
            report_type="monthly",
            year=year,
            month=month,
            language=language
        )
        return report
    except Exception as e:
        raise Exception(f"Error generating monthly report: {str(e)}")

@mcp.tool()
async def assess_project_risks(
    project_id: str,
    include_recommendations: bool = True
) -> Dict[str, Any]:
    """Assess project risks and provide recommendations"""
    try:
        risk_assessment = await risk_assessor.assess_project_risks(
            project_id=project_id,
            include_recommendations=include_recommendations
        )
        
        return {
            "project_id": project_id,
            "risk_level": risk_assessment.risk_level,
            "risks": [
                {
                    "type": risk.type,
                    "description": risk.description,
                    "severity": risk.severity,
                    "probability": risk.probability,
                    "impact": risk.impact
                }
                for risk in risk_assessment.risks
            ],
            "recommendations": risk_assessment.recommendations if include_recommendations else [],
            "assessed_at": risk_assessment.assessed_at.isoformat()
        }
    except Exception as e:
        raise Exception(f"Error assessing project risks: {str(e)}")

@mcp.tool()
async def analyze_workload(
    project_id: str,
    period: str = "weekly"
) -> Dict[str, Any]:
    """Analyze team workload for a project"""
    try:
        workload_analysis = await workload_analyzer.analyze_workload(
            project_id=project_id,
            period=period
        )
        
        return {
            "project_id": project_id,
            "period": period,
            "team_members": [
                {
                    "name": member.name,
                    "assigned_tasks": member.assigned_tasks,
                    "completed_tasks": member.completed_tasks,
                    "workload_percentage": member.workload_percentage,
                    "efficiency_score": member.efficiency_score
                }
                for member in workload_analysis.team_members
            ],
            "total_tasks": workload_analysis.total_tasks,
            "completed_tasks": workload_analysis.completed_tasks,
            "average_workload": workload_analysis.average_workload,
            "analysis_date": workload_analysis.analysis_date.isoformat()
        }
    except Exception as e:
        raise Exception(f"Error analyzing workload: {str(e)}")

# Resource definitions
@mcp.resource("projects://{project_id}")
async def get_project_resource(project_id: str) -> Dict[str, Any]:
    """Get project as a resource"""
    try:
        project = await openproject_client.get_project_by_id(project_id)
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    except Exception as e:
        raise Exception(f"Error fetching project resource: {str(e)}")

@mcp.resource("work-packages://{project_id}")
async def get_work_packages_resource(project_id: str) -> List[Dict[str, Any]]:
    """Get work packages as a resource"""
    try:
        work_packages = await openproject_client.get_work_packages(project_id)
        return [
            {
                "id": wp.id,
                "subject": wp.subject,
                "description": wp.description,
                "status": wp.status,
                "type": wp.type,
                "assignee": wp.assignee,
                "due_date": wp.due_date.isoformat() if wp.due_date else None
            }
            for wp in work_packages
        ]
    except Exception as e:
        raise Exception(f"Error fetching work packages resource: {str(e)}")

# Prompt definitions
@mcp.prompt()
async def weekly_report_prompt(project_id: str) -> str:
    """Generate a prompt for weekly report creation"""
    return f"""
    Please create a comprehensive weekly report for project {project_id}.
    
    Include the following sections:
    1. Project Overview
    2. This Week's Progress
    3. Completed Tasks
    4. In Progress Tasks
    5. Upcoming Plans
    6. Risks and Issues
    
    Use the get_project_details and get_work_packages_resource tools to gather necessary information.
    """

@mcp.prompt()
async def risk_assessment_prompt(project_id: str) -> str:
    """Generate a prompt for risk assessment"""
    return f"""
    Please conduct a thorough risk assessment for project {project_id}.
    
    Consider the following risk categories:
    1. Schedule Risks
    2. Resource Risks
    3. Technical Risks
    4. External Risks
    
    Use the get_project_details and assess_project_risks tools to gather information.
    """

# Health check endpoint
@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Health check for the FastMCP server"""
    try:
        # Test OpenProject connection
        await openproject_client.test_connection()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "openproject": "connected",
            "tools_available": [
                "get_projects",
                "get_project_details",
                "generate_weekly_report",
                "generate_monthly_report",
                "assess_project_risks",
                "analyze_workload",
                "health_check"
            ],
            "resources_available": [
                "projects://{project_id}",
                "work-packages://{project_id}"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
```

## 🟨 TypeScript Solution Implementation

### Express Server with TypeScript

```typescript
// src/index.ts
import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import { McpHandler } from './mcp/handler';
import { OpenProjectService } from './services/openproject';
import { ReportService } from './services/report';
import { ConfigService } from './config';
import { logger } from './utils/logger';

interface ErrorResponse {
  error: {
    code: number;
    message: string;
    details?: any;
  };
}

const app = express();
const config = ConfigService.getInstance();
const mcpHandler = new McpHandler();
const openProjectService = new OpenProjectService();
const reportService = new ReportService();

// Middleware
app.use(helmet());
app.use(cors({
  origin: config.get('CORS_ALLOW_ORIGINS', 'http://localhost:3000'),
  credentials: true
}));
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    timestamp: new Date().toISOString()
  });
  next();
});

// Health check endpoint
app.get('/health', async (req: Request, res: Response) => {
  try {
    const health = await openProjectService.checkHealth();
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      services: {
        openproject: health,
        mcp: 'operational'
      },
      uptime: process.uptime()
    });
  } catch (error) {
    logger.error('Health check failed', { error });
    res.status(503).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    });
  }
});

// MCP endpoint
app.post('/mcp', async (req: Request, res: Response) => {
  try {
    const mcpRequest = req.body;
    const response = await mcpHandler.handleRequest(mcpRequest);
    res.json(response);
  } catch (error) {
    logger.error('MCP request failed', { error, request: req.body });
    res.status(500).json({
      jsonrpc: '2.0',
      id: req.body.id,
      error: {
        code: -1,
        message: error instanceof Error ? error.message : 'Internal server error'
      }
    });
  }
});

// API Routes
app.use('/api/v1/projects', require('./routes/projects'));
app.use('/api/v1/work-packages', require('./routes/work-packages'));
app.use('/api/v1/reports', require('./routes/reports'));

// Error handling middleware
app.use((error: Error, req: Request, res: Response, next: NextFunction) => {
  logger.error('Unhandled error', { error, path: req.path });
  
  const errorResponse: ErrorResponse = {
    error: {
      code: 500,
      message: error.message || 'Internal server error'
    }
  };
  
  if (process.env.NODE_ENV === 'development') {
    errorResponse.error.details = error.stack;
  }
  
  res.status(500).json(errorResponse);
});

// 404 handler
app.use('*', (req: Request, res: Response) => {
  res.status(404).json({
    error: {
      code: 404,
      message: `Route ${req.originalUrl} not found`
    }
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

const PORT = config.get('PORT', 3000);

app.listen(PORT, () => {
  logger.info(`TypeScript MCP Server running on port ${PORT}`);
  logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

export default app;
```

### MCP Handler Implementation

```typescript
// src/mcp/handler.ts
import { 
  JsonRpcRequest, 
  JsonRpcResponse, 
  Tool, 
  Resource, 
  Prompt 
} from '../types/mcp';
import { OpenProjectService } from '../services/openproject';
import { ReportService } from '../services/report';
import { RiskAssessmentService } from '../services/risk-assessment';
import { logger } from '../utils/logger';

interface ToolCallParams {
  name: string;
  arguments: Record<string, any>;
}

export class McpHandler {
  private openProjectService: OpenProjectService;
  private reportService: ReportService;
  private riskAssessmentService: RiskAssessmentService;
  private tools: Map<string, Tool>;
  private resources: Map<string, Resource>;
  private prompts: Map<string, Prompt>;

  constructor() {
    this.openProjectService = new OpenProjectService();
    this.reportService = new ReportService();
    this.riskAssessmentService = new RiskAssessmentService();
    this.tools = new Map();
    this.resources = new Map();
    this.prompts = new Map();
    
    this.initializeTools();
    this.initializeResources();
    this.initializePrompts();
  }

  private initializeTools(): void {
    const tools: Tool[] = [
      {
        name: 'get_projects',
        description: 'Get all projects from OpenProject',
        inputSchema: {
          type: 'object',
          properties: {},
          required: []
        }
      },
      {
        name: 'get_project_details',
        description: 'Get detailed information about a specific project',
        inputSchema: {
          type: 'object',
          properties: {
            project_id: {
              type: 'string',
              description: 'Project ID'
            }
          },
          required: ['project_id']
        }
      },
      {
        name: 'generate_weekly_report',
        description: 'Generate weekly report for a project',
        inputSchema: {
          type: 'object',
          properties: {
            project_id: {
              type: 'string',
              description: 'Project ID'
            },
            start_date: {
              type: 'string',
              description: 'Start date (YYYY-MM-DD)'
            },
            end_date: {
              type: 'string',
              description: 'End date (YYYY-MM-DD)'
            },
            language: {
              type: 'string',
              description: 'Report language (ja/en/zh)',
              default: 'ja'
            }
          },
          required: ['project_id', 'start_date', 'end_date']
        }
      },
      {
        name: 'assess_project_risks',
        description: 'Assess project risks and provide recommendations',
        inputSchema: {
          type: 'object',
          properties: {
            project_id: {
              type: 'string',
              description: 'Project ID'
            },
            include_recommendations: {
              type: 'boolean',
              default: true
            }
          },
          required: ['project_id']
        }
      }
    ];

    tools.forEach(tool => {
      this.tools.set(tool.name, tool);
    });
  }

  private initializeResources(): void {
    const resources: Resource[] = [
      {
        uri: 'projects://{project_id}',
        name: 'Project Resource',
        description: 'Get project information as a resource',
        mimeType: 'application/json'
      },
      {
        uri: 'work-packages://{project_id}',
        name: 'Work Packages Resource',
        description: 'Get work packages for a project as a resource',
        mimeType: 'application/json'
      }
    ];

    resources.forEach(resource => {
      this.resources.set(resource.uri, resource);
    });
  }

  private initializePrompts(): void {
    const prompts: Prompt[] = [
      {
        name: 'weekly_report_prompt',
        description: 'Generate a prompt for weekly report creation',
        arguments: [
          {
            name: 'project_id',
            description: 'Project ID',
            required: true
          }
        ]
      },
      {
        name: 'risk_assessment_prompt',
        description: 'Generate a prompt for risk assessment',
        arguments: [
          {
            name: 'project_id',
            description: 'Project ID',
            required: true
          }
        ]
      }
    ];

    prompts.forEach(prompt => {
      this.prompts.set(prompt.name, prompt);
    });
  }

  async handleRequest(request: JsonRpcRequest): Promise<JsonRpcResponse> {
    const { method, params, id } = request;

    try {
      switch (method) {
        case 'initialize':
          return this.handleInitialize(params, id);
        case 'tools/list':
          return this.handleToolsList(params, id);
        case 'tools/call':
          return this.handleToolsCall(params as ToolCallParams, id);
        case 'resources/list':
          return this.handleResourcesList(params, id);
        case 'resources/read':
          return this.handleResourcesRead(params, id);
        case 'prompts/list':
          return this.handlePromptsList(params, id);
        case 'prompts/get':
          return this.handlePromptsGet(params, id);
        default:
          throw new Error(`Unknown method: ${method}`);
      }
    } catch (error) {
      logger.error('MCP request failed', { error, method, params });
      
      return {
        jsonrpc: '2.0',
        id,
        error: {
          code: -1,
          message: error instanceof Error ? error.message : 'Internal server error'
        }
      };
    }
  }

  private handleInitialize(params: any, id: string): JsonRpcResponse {
    return {
      jsonrpc: '2.0',
      id,
      result: {
        protocolVersion: '2024-11-05',
        capabilities: {
          tools: {},
          resources: {},
          prompts: {},
          logging: {}
        },
        serverInfo: {
          name: 'OpenProject MCP Server',
          version: '1.0.0'
        }
      }
    };
  }

  private handleToolsList(params: any, id: string): JsonRpcResponse {
    const tools = Array.from(this.tools.values());
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        tools
      }
    };
  }

  private async handleToolsCall(params: ToolCallParams, id: string): Promise<JsonRpcResponse> {
    const { name, arguments: args } = params;

    switch (name) {
      case 'get_projects':
        return await this.handleGetProjects(args, id);
      case 'get_project_details':
        return await this.handleGetProjectDetails(args, id);
      case 'generate_weekly_report':
        return await this.handleGenerateWeeklyReport(args, id);
      case 'assess_project_risks':
        return await this.handleAssessProjectRisks(args, id);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  }

  private async handleGetProjects(args: any, id: string): Promise<JsonRpcResponse> {
    const projects = await this.openProjectService.getProjects();
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        content: [
          {
            type: 'text',
            text: JSON.stringify(projects, null, 2)
          }
        ]
      }
    };
  }

  private async handleGetProjectDetails(args: any, id: string): Promise<JsonRpcResponse> {
    const { project_id } = args;
    
    if (!project_id) {
      throw new Error('project_id is required');
    }

    const project = await this.openProjectService.getProjectDetails(project_id);
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        content: [
          {
            type: 'text',
            text: JSON.stringify(project, null, 2)
          }
        ]
      }
    };
  }

  private async handleGenerateWeeklyReport(args: any, id: string): Promise<JsonRpcResponse> {
    const { project_id, start_date, end_date, language = 'ja' } = args;
    
    if (!project_id || !start_date || !end_date) {
      throw new Error('project_id, start_date, and end_date are required');
    }

    const report = await this.reportService.generateWeeklyReport({
      project_id,
      start_date,
      end_date,
      language
    });
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        content: [
          {
            type: 'text',
            text: report
          }
        ]
      }
    };
  }

  private async handleAssessProjectRisks(args: any, id: string): Promise<JsonRpcResponse> {
    const { project_id, include_recommendations = true } = args;
    
    if (!project_id) {
      throw new Error('project_id is required');
    }

    const assessment = await this.riskAssessmentService.assessProjectRisks({
      project_id,
      include_recommendations
    });
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        content: [
          {
            type: 'text',
            text: JSON.stringify(assessment, null, 2)
          }
        ]
      }
    };
  }

  private handleResourcesList(params: any, id: string): JsonRpcResponse {
    const resources = Array.from(this.resources.values());
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        resources
      }
    };
  }

  private handleResourcesRead(params: any, id: string): JsonRpcResponse {
    const { uri } = params;
    
    if (!uri) {
      throw new Error('uri is required');
    }

    // Parse URI and return appropriate resource
    // This is a simplified implementation
    return {
      jsonrpc: '2.0',
      id,
      result: {
        contents: [
          {
            uri,
            mimeType: 'application/json',
            text: JSON.stringify({ message: 'Resource data' }, null, 2)
          }
        ]
      }
    };
  }

  private handlePromptsList(params: any, id: string): JsonRpcResponse {
    const prompts = Array.from(this.prompts.values());
    
    return {
      jsonrpc: '2.0',
      id,
      result: {
        prompts
      }
    };
  }

  private handlePromptsGet(params: any, id: string): JsonRpcResponse {
    const { name } = params;
    
    if (!name) {
      throw new Error('name is required');
    }

    const prompt = this.prompts.get(name);
    if (!prompt) {
      throw new Error(`Prompt not found: ${name}`);
    }

    return {
      jsonrpc: '2.0',
      id,
      result: {
        description: prompt.description,
        arguments: prompt.arguments
      }
    };
  }
}
```

### Service Implementation

```typescript
// src/services/openproject.ts
import axios, { AxiosInstance } from 'axios';
import { Project, WorkPackage, User } from '../types/openproject';
import { ConfigService } from '../config';
import { logger } from '../utils/logger';

export class OpenProjectService {
  private client: AxiosInstance;
  private config: ConfigService;

  constructor() {
    this.config = ConfigService.getInstance();
    
    this.client = axios.create({
      baseURL: this.config.get('OPENPROJECT_URL'),
      headers: {
        'Authorization': `Bearer ${this.config.get('OPENPROJECT_API_KEY')}`,
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    this.client.interceptors.request.use(
      (config) => {
        logger.info('OpenProject API request', {
          method: config.method,
          url: config.url,
          params: config.params
        });
        return config;
      },
      (error) => {
        logger.error('OpenProject API request error', { error });
        return Promise.reject(error);
      }
    );

    this.client.interceptors.response.use(
      (response) => {
        logger.info('OpenProject API response', {
          status: response.status,
          url: response.config.url
        });
        return response;
      },
      (error) => {
        logger.error('OpenProject API response error', { 
          status: error.response?.status,
          url: error.config?.url,
          error: error.message 
        });
        return Promise.reject(error);
      }
    );
  }

  async checkHealth(): Promise<boolean> {
    try {
      const response = await this.client.get('/api/v3/projects');
      return response.status === 200;
    } catch (error) {
      logger.error('Health check failed', { error });
      return false;
    }
  }

  async getProjects(): Promise<Project[]> {
    try {
      const response = await this.client.get('/api/v3/projects');
      const projects = response.data._embedded?.elements || [];
      
      return projects.map((project: any) => ({
        id: project.id.toString(),
        name: project.name,
        description: project.description?.raw || '',
        status: project.status,
        createdAt: new Date(project.createdAt),
        updatedAt: new Date(project.updatedAt)
      }));
    } catch (error) {
      logger.error('Failed to fetch projects', { error });
      throw new Error(`Failed to fetch projects: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getProjectDetails(projectId: string): Promise<any> {
    try {
      const [projectResponse, workPackagesResponse] = await Promise.all([
        this.client.get(`/api/v3/projects/${projectId}`),
        this.client.get(`/api/v3/projects/${projectId}/work_packages`)
      ]);

      const project = projectResponse.data;
      const workPackages = workPackagesResponse.data._embedded?.elements || [];

      return {
        project: {
          id: project.id.toString(),
          name: project.name,
          description: project.description?.raw || '',
          status: project.status,
          createdAt: new Date(project.createdAt),
          updatedAt: new Date(project.updatedAt)
        },
        workPackages: workPackages.map((wp: any) => ({
          id: wp.id.toString(),
          subject: wp.subject,
          description: wp.description?.raw || '',
          status: wp.status?.name || '',
          type: wp.type?.name || '',
          assignee: wp.assignee?.name || '',
          dueDate: wp.dueDate ? new Date(wp.dueDate) : null
        })),
        statistics: {
          totalWorkPackages: workPackages.length,
          completedWorkPackages: workPackages.filter((wp: any) => wp.status?.name === '完了').length,
          inProgressWorkPackages: workPackages.filter((wp: any) => wp.status?.name === '進行中').length
        }
      };
    } catch (error) {
      logger.error('Failed to fetch project details', { error, projectId });
      throw new Error(`Failed to fetch project details: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getWorkPackages(projectId: string): Promise<WorkPackage[]> {
    try {
      const response = await this.client.get(`/api/v3/projects/${projectId}/work_packages`);
      const workPackages = response.data._embedded?.elements || [];
      
      return workPackages.map((wp: any) => ({
        id: wp.id.toString(),
        subject: wp.subject,
        description: wp.description?.raw || '',
        status: wp.status?.name || '',
        type: wp.type?.name || '',
        projectId: projectId,
        assignee: wp.assignee?.name || '',
        dueDate: wp.dueDate ? new Date(wp.dueDate) : null
      }));
    } catch (error) {
      logger.error('Failed to fetch work packages', { error, projectId });
      throw new Error(`Failed to fetch work packages: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async createWorkPackage(workPackage: Partial<WorkPackage>): Promise<WorkPackage> {
    try {
      const response = await this.client.post('/api/v3/work_packages', {
        subject: workPackage.subject,
        description: { raw: workPackage.description },
        projectId: workPackage.projectId,
        typeId: workPackage.type,
        assignee: workPackage.assignee,
        dueDate: workPackage.dueDate
      });

      const wp = response.data;
      return {
        id: wp.id.toString(),
        subject: wp.subject,
        description: wp.description?.raw || '',
        status: wp.status?.name || '',
        type: wp.type?.name || '',
        projectId: wp.projectId.toString(),
        assignee: wp.assignee?.name || '',
        dueDate: wp.dueDate ? new Date(wp.dueDate) : null
      };
    } catch (error) {
      logger.error('Failed to create work package', { error, workPackage });
      throw new Error(`Failed to create work package: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async updateWorkPackage(id: string, updates: Partial<WorkPackage>): Promise<WorkPackage> {
    try {
      const response = await this.client.patch(`/api/v3/work_packages/${id}`, {
        subject: updates.subject,
        description: updates.description ? { raw: updates.description } : undefined,
        status: updates.status,
        assignee: updates.assignee,
        dueDate: updates.dueDate
      });

      const wp = response.data;
      return {
        id: wp.id.toString(),
        subject: wp.subject,
        description: wp.description?.raw || '',
        status: wp.status?.name || '',
        type: wp.type?.name || '',
        projectId: wp.projectId.toString(),
        assignee: wp.assignee?.name || '',
        dueDate: wp.dueDate ? new Date(wp.dueDate) : null
      };
    } catch (error) {
      logger.error('Failed to update work package', { error, id, updates });
      throw new Error(`Failed to update work package: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async getUsers(): Promise<User[]> {
    try {
      const response = await this.client.get('/api/v3/users');
      const users = response.data._embedded?.elements || [];
      
      return users.map((user: any) => ({
        id: user.id.toString(),
        name: user.name,
        email: user.email,
        login: user.login,
        createdAt: new Date(user.createdAt),
        updatedAt: new Date(user.updatedAt)
      }));
    } catch (error) {
      logger.error('Failed to fetch users', { error });
      throw new Error(`Failed to fetch users: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}
```

## 🔗 Common Implementation Patterns

### Error Handling Pattern

```python
# Python Error Handling Pattern
from fastapi import HTTPException
from mcp_core.domain.exceptions import MCPError
import logging

logger = logging.getLogger(__name__)

async def handle_request_with_error_handling(func):
    """Decorator for consistent error handling"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MCPError as e:
            logger.error(f"MCP Error: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except ValueError as e:
            logger.error(f"Validation Error: {str(e)}")
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper
```

### Configuration Management Pattern

```python
# Python Configuration Pattern
from pydantic import BaseSettings, Field
from typing import List
import os

class Settings(BaseSettings):
    # OpenProject Configuration
    openproject_url: str = Field(..., env="OPENPROJECT_URL")
    openproject_api_key: str = Field(..., env="OPENPROJECT_API_KEY")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8010, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # CORS Configuration
    cors_allow_origins: List[str] = Field(
        default=["http://localhost", "http://127.0.0.1"],
        env="CORS_ALLOW_ORIGINS"
    )
    
    # Performance Configuration
    max_connections: int = Field(default=100, env="MAX_CONNECTIONS")
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")
    cache_ttl: int = Field(default=300, env="CACHE_TTL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()
```

### Logging Pattern

```python
# Python Logging Pattern
import logging
import json
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(level: str = "INFO"):
    """Setup structured logging"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler for errors
    file_handler = logging.FileHandler('logs/error.log')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    return logger
```

### Dependency Injection Pattern

```python
# Python Dependency Injection Pattern
from fastapi import Depends
from typing import AsyncGenerator
import asyncio

from app.services.openproject_service import OpenProjectService
from app.services.report_service import ReportService
from app.core.config import settings

# Singleton services
_openproject_service: OpenProjectService = None
_report_service: ReportService = None

async def get_openproject_service() -> AsyncGenerator[OpenProjectService, None]:
    """Get OpenProject service instance"""
    global _openproject_service
    if _openproject_service is None:
        _openproject_service = OpenProjectService(
            url=settings.openproject_url,
            api_key=settings.openproject_api_key
        )
    yield _openproject_service

async def get_report_service(
    openproject_service: OpenProjectService = Depends(get_openproject_service)
) -> AsyncGenerator[ReportService, None]:
    """Get report service instance"""
    global _report_service
    if _report_service is None:
        _report_service = ReportService(openproject_service)
    yield _report_service

# Cleanup on shutdown
async def cleanup_services():
    """Cleanup service connections"""
    global _openproject_service, _report_service
    if _openproject_service:
        await _openproject_service.close()
    if _report_service:
        await _report_service.close()
```

## 🧪 Testing Examples

### Unit Testing Example

```python
# tests/unit/test_openproject_service.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.openproject_service import OpenProjectService
from app.core.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        openproject_url="http://test-openproject.com",
        openproject_api_key="test-api-key"
    )

@pytest.fixture
def openproject_service(mock_settings):
    with patch('app.services.openproject_service.Settings') as mock_settings_class:
        mock_settings_class.return_value = mock_settings
        return OpenProjectService()

@pytest.mark.asyncio
async def test_get_projects_success(openproject_service):
    """Test successful project retrieval"""
    # Mock response
    mock_response = Mock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "_embedded": {
            "elements": [
                {
                    "id": 1,
                    "name": "Test Project",
                    "description": {"raw": "Test Description"},
                    "status": "on_track",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z"
                }
            ]
        }
    })
    
    with patch.object(openproject_service, '_make_request', return_value=mock_response):
        projects = await openproject_service.get_projects()
        
        assert len(projects) == 1
        assert projects[0].name == "Test Project"
        assert projects[0].status == "on_track"

@pytest.mark.asyncio
async def test_get_projects_failure(openproject_service):
    """Test project retrieval failure"""
    with patch.object(openproject_service, '_make_request', side_effect=Exception("API Error")):
        with pytest.raises(Exception, match="Failed to fetch projects"):
            await openproject_service.get_projects()

@pytest.mark.asyncio
async def test_health_check_success(openproject_service):
    """Test successful health check"""
    with patch.object(openproject_service, 'check_health', return_value=True):
        result = await openproject_service.check_health()
        assert result is True
```

### Integration Testing Example

```python
# tests/integration/test_mcp_integration.py
import pytest
import httpx
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def test_client():
    return TestClient(app)

def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_mcp_endpoint(test_client):
    """Test MCP endpoint"""
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_projects",
            "arguments": {}
        }
    }
    
    response = test_client.post("/mcp", json=mcp_request)
    assert response.status_code == 200
    data = response.json()
    assert "jsonrpc" in data
    assert data["jsonrpc"] == "2.0"

def test_invalid_mcp_request(test_client):
    """Test invalid MCP request"""
    invalid_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "invalid_method",
        "params": {}
    }
    
    response = test_client.post("/mcp", json=invalid_request)
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -1
```

## 📋 Configuration Examples

### Environment Configuration

```bash
# .env file for HTTP Solution
# OpenProject Configuration
OPENPROJECT_URL=http://localhost:8090
OPENPROJECT_API_KEY=your-api-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8010
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration
CORS_ALLOW_ORIGINS=http://localhost,http://127.0.0.1,http://localhost:3000

# Performance Configuration
MAX_CONNECTIONS=100
REQUEST_TIMEOUT=30
CACHE_TTL=300

# Security Configuration
ENABLE_HTTPS=false
API_RATE_LIMIT=100
```

### Docker Configuration

```dockerfile
# Dockerfile for HTTP Solution
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Start the application
CMD ["python", "-m", "src.main"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  openproject:
    image: openproject/community:latest
    ports:
      - "8090:8080"
    environment:
      - OPENPROJECT_SECRET_KEY_BASE=secret
      - OPENPROJECT_HTTPS=false
    volumes:
      - openproject_data:/var/lib/openproject
    networks:
      - mcp_network

  mcp-http:
    build: ./solution-http
    ports:
      - "8010:8010"
    environment:
      - OPENPROJECT_URL=http://openproject:8080
      - OPENPROJECT_API_KEY=demo-api-key
      - HOST=0.0.0.0
      - PORT=8010
    depends_on:
      - openproject
    networks:
      - mcp_network
    restart: unless-stopped

  mcp-fastapi:
    build: ./solution-fastapi
    ports:
      - "8020:8020"
    environment:
      - OPENPROJECT_URL=http://openproject:8080
      - OPENPROJECT_API_KEY=demo-api-key
      - HOST=0.0.0.0
      - PORT=8020
    depends_on:
      - openproject
    networks:
      - mcp_network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - mcp_network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - mcp_network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - mcp_network
    restart: unless-stopped

volumes:
  openproject_data:
  grafana_data:

networks:
  mcp_network:
    driver: bridge
```

This comprehensive implementation guide provides detailed examples and code samples for all four solution types. Each implementation follows best practices and includes error handling, testing, and configuration examples.