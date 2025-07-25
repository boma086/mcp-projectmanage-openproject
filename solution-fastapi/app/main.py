"""
精简的 FastAPI MCP 服务器 - 使用核心库
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.adapters.async_openproject_adapter import AsyncOpenProjectClient
from dotenv import load_dotenv

# 导入核心库
from mcp_core import (
    MCPHandler, get_logger, Config, set_global_config,
    MCPError
)

# 初始化核心库配置
logger = get_logger("mcp.fastapi")
try:
    config = Config()
    set_global_config(config)
    logger.info("核心库配置初始化成功")
except Exception as e:
    logger.error(f"核心库配置初始化失败", e)
    raise MCPError(f"Failed to initialize core config: {e}")

# 全局服务实例
openproject_client = None
mcp_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global openproject_client, mcp_handler
    
    # 启动时初始化
    try:
        logger.info("初始化 FastAPI MCP 服务...")
        
        # 创建异步 OpenProject 客户端
        openproject_client = AsyncOpenProjectClient()
        await openproject_client.initialize()
        
        # 创建 MCP 处理器
        mcp_handler = MCPHandler(openproject_client)
        
        logger.info("FastAPI MCP 服务初始化成功")
        
        yield
        
    finally:
        # 关闭时清理
        logger.info("清理 FastAPI MCP 服务...")
        if openproject_client:
            await openproject_client.cleanup()


# 创建 FastAPI 应用
app = FastAPI(
    title="MCP OpenProject Server",
    description="基于 FastAPI 的 MCP OpenProject 服务器",
    version="1.0.0",
    lifespan=lifespan
)

# 加载环境变量
load_dotenv()

# 读取允许的 CORS 源
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost,http://127.0.0.1").split(",")
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件（从共享 Web 目录）
if os.path.exists("../shared-web"):
    app.mount("/web", StaticFiles(directory="../shared-web"), name="web")


@app.get("/")
async def root():
    """根路径 - 返回服务信息"""
    return {
        "name": "MCP OpenProject Server",
        "version": "1.0.0",
        "framework": "FastAPI",
        "status": "running",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查 OpenProject 连接
        connection_ok = False
        if openproject_client:
            connection_ok = await openproject_client.check_connection()
        
        return {
            "status": "healthy",
            "services": {
                "openproject": "connected" if connection_ok else "disconnected",
                "mcp_handler": "ready" if mcp_handler else "not_ready"
            },
            "timestamp": "2025-01-24T19:52:00Z"
        }
    except Exception as e:
        logger.error("健康检查失败", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """处理 MCP 请求"""
    try:
        # 确保服务已初始化
        if not mcp_handler:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # 读取请求体
        request_data = await request.json()
        
        # 使用核心库的 MCP 处理器
        response = await mcp_handler.handle_request(request_data)
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error("处理 MCP 请求失败", e)
        
        # 返回 JSON-RPC 错误响应
        error_response = {
            "jsonrpc": "2.0",
            "id": request_data.get("id") if "request_data" in locals() else None,
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": str(e)
            }
        }
        return JSONResponse(content=error_response)


@app.get("/projects")
async def get_projects():
    """获取项目列表 - REST API 端点"""
    try:
        if not openproject_client:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        projects = await openproject_client.get_projects()
        
        return {
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "identifier": p.identifier,
                    "description": p.description,
                    "status": p.status
                }
                for p in projects
            ]
        }
        
    except Exception as e:
        logger.error("获取项目列表失败", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情 - REST API 端点"""
    try:
        if not openproject_client:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        project = await openproject_client.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "id": project.id,
            "name": project.name,
            "identifier": project.identifier,
            "description": project.description,
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取项目详情失败: {project_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/work_packages")
async def get_work_packages(project_id: str):
    """获取项目工作包 - REST API 端点"""
    try:
        if not openproject_client:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        work_packages = await openproject_client.get_work_packages(project_id)
        
        return {
            "work_packages": [
                {
                    "id": wp.id,
                    "subject": wp.subject,
                    "status": wp.status,
                    "type": wp.type,
                    "priority": wp.priority,
                    "assigned_to": wp.assigned_to,
                    "progress": wp.progress
                }
                for wp in work_packages
            ]
        }
        
    except Exception as e:
        logger.error(f"获取工作包失败: {project_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/reports/weekly")
async def generate_weekly_report(project_id: str, start_date: str, end_date: str):
    """生成周报 - REST API 端点"""
    try:
        if not openproject_client:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        report = await openproject_client.generate_weekly_report(project_id, start_date, end_date)
        
        return {
            "title": report.title,
            "project_name": report.project_name,
            "period": report.period,
            "summary": report.summary,
            "sections": [
                {
                    "title": section.title,
                    "content": section.content,
                    "order": section.order
                }
                for section in report.sections
            ],
            "statistics": report.statistics,
            "markdown": report.to_markdown()
        }
        
    except Exception as e:
        logger.error(f"生成周报失败: {project_id}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# 异常处理器
@app.exception_handler(MCPError)
async def mcp_error_handler(request: Request, exc: MCPError):
    """MCP 错误处理器"""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "data": exc.data
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8020))
    
    logger.info(f"启动 FastAPI MCP 服务器，端口: {port}")
    logger.info(f"服务地址:")
    logger.info(f"  - API 文档: http://localhost:{port}/docs")
    logger.info(f"  - 健康检查: http://localhost:{port}/health")
    logger.info(f"  - MCP 端点: http://localhost:{port}/mcp")
    logger.info(f"  - Web 界面: http://localhost:{port}/web/template_editor.html")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
