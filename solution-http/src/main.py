#!/usr/bin/env python3
"""
HTTP MCP 服务器 - FastAPI 同步模式实现
使用同步请求-响应模式，提供简单的 REST API 端点
"""
import os
import asyncio
import threading
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# 导入本地模块
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from adapters.openproject_adapter import HTTPOpenProjectClient
from config import get_http_config, HTTPSolutionConfig

# 导入核心库
from mcp_core import (
    MCPHandler, get_logger, Config, set_global_config,
    MCPError
)

# 加载环境变量
load_dotenv()

# 全局配置和服务实例
http_config = get_http_config()
logger = get_logger("mcp.http")
openproject_client: Optional[HTTPOpenProjectClient] = None
mcp_handler: Optional[MCPHandler] = None
_services_initialized = False
_init_lock = threading.Lock()


def initialize_core_config():
    """初始化核心库配置"""
    try:
        # 创建核心库配置，只包含核心字段
        core_config = Config(
            openproject_url=http_config.openproject_url,
            openproject_api_key=http_config.openproject_api_key,
            log_level=http_config.log_level,
            templates_dir=http_config.templates_dir,
            cache_ttl=http_config.cache_ttl
        )
        set_global_config(core_config)
        logger.info("核心库配置初始化成功")
    except Exception as e:
        logger.error(f"核心库配置初始化失败: {e}")
        raise MCPError(f"Failed to initialize core config: {e}")


def initialize_services():
    """线程安全的服务初始化（同步模式）"""
    global openproject_client, mcp_handler, _services_initialized
    
    with _init_lock:
        if not _services_initialized:
            try:
                logger.info("初始化 HTTP MCP 服务...")
                
                # 创建 OpenProject 客户端
                openproject_client = HTTPOpenProjectClient()
                
                # 初始化客户端（同步调用异步方法）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(openproject_client.initialize())
                finally:
                    loop.close()
                
                # 创建 MCP 处理器
                mcp_handler = MCPHandler(openproject_client)
                
                _services_initialized = True
                logger.info("HTTP MCP 服务初始化成功")
                
            except Exception as e:
                logger.error(f"服务初始化失败: {e}")
                raise


def cleanup_services():
    """清理服务资源"""
    global openproject_client
    
    if openproject_client:
        try:
            # 同步调用异步清理方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(openproject_client.cleanup())
            finally:
                loop.close()
            logger.info("服务资源清理完成")
        except Exception as e:
            logger.error(f"清理服务资源时出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    initialize_core_config()
    initialize_services()
    
    yield
    
    # 关闭时清理
    logger.info("清理 HTTP MCP 服务...")
    cleanup_services()


# 创建 FastAPI 应用
app = FastAPI(
    title="MCP OpenProject Server - HTTP Solution",
    description="基于 FastAPI 同步模式的 MCP OpenProject 服务器",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加信任主机中间件
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # 在生产环境中应该限制为特定主机
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=http_config.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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
        "framework": "FastAPI (Synchronous Mode)",
        "solution": "HTTP",
        "status": "running",
        "endpoints": {
            "mcp": "/mcp",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "features": [
            "Synchronous request-response pattern",
            "Simple REST API endpoints",
            "Minimal dependencies",
            "WSGI server deployment ready"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        # 检查服务状态
        services_status = {
            "mcp_handler": "ready" if mcp_handler else "not_ready",
            "openproject": "disconnected"
        }
        
        # 检查 OpenProject 连接（同步调用）
        if openproject_client:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                connection_ok = loop.run_until_complete(openproject_client.check_connection())
                services_status["openproject"] = "connected" if connection_ok else "disconnected"
            finally:
                loop.close()
        
        overall_status = "healthy" if all(
            status in ["ready", "connected"] for status in services_status.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "services": services_status,
            "config": {
                "openproject_url": http_config.openproject_url,
                "port": http_config.port,
                "log_level": http_config.log_level
            }
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """处理 MCP 请求 - 主要 API 端点"""
    try:
        # 确保服务已初始化
        if not _services_initialized:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        if not mcp_handler:
            raise HTTPException(status_code=503, detail="MCP handler not available")
        
        # 读取请求体
        request_data = await request.json()
        logger.info(f"收到 MCP 请求: {request_data.get('method', 'unknown')}")
        
        # 使用核心库的 MCP 处理器（同步调用异步方法）
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(mcp_handler.handle_request(request_data))
        finally:
            loop.close()
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"处理 MCP 请求失败: {e}")
        
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


@app.get("/api/projects")
async def get_projects():
    """获取项目列表 - REST API 端点"""
    try:
        if not openproject_client:
            raise HTTPException(status_code=503, detail="OpenProject client not available")
        
        # 同步调用异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            projects = loop.run_until_complete(openproject_client.get_projects())
        finally:
            loop.close()
        
        return [
            {
                "id": project.id,
                "name": project.name,
                "identifier": project.identifier,
                "description": project.description,
                "status": project.status,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            }
            for project in projects
        ]
        
    except Exception as e:
        logger.error(f"获取项目列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/work_packages")
async def get_work_packages(project_id: str):
    """获取项目工作包列表 - REST API 端点"""
    try:
        if not openproject_client:
            raise HTTPException(status_code=503, detail="OpenProject client not available")
        
        # 同步调用异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            work_packages = loop.run_until_complete(
                openproject_client.get_work_packages(project_id)
            )
        finally:
            loop.close()
        
        return [
            {
                "id": wp.id,
                "subject": wp.subject,
                "description": wp.description,
                "status": wp.status,
                "type": wp.type,
                "priority": wp.priority,
                "assigned_to": wp.assigned_to,
                "progress": wp.progress,
                "start_date": wp.start_date.isoformat() if wp.start_date else None,
                "due_date": wp.due_date.isoformat() if wp.due_date else None,
                "created_at": wp.created_at.isoformat() if wp.created_at else None,
                "updated_at": wp.updated_at.isoformat() if wp.updated_at else None
            }
            for wp in work_packages
        ]
        
    except Exception as e:
        logger.error(f"获取工作包列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 异常处理器
@app.exception_handler(MCPError)
async def mcp_error_handler(request: Request, exc: MCPError):
    """MCP 错误处理器"""
    logger.error(f"MCP 错误: {exc.message}")
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


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": -32603,
                "message": "Internal server error",
                "data": str(exc)
            }
        }
    )


def main():
    """主函数 - 启动 HTTP 服务器"""
    import uvicorn
    
    config = get_http_config()
    
    logger.info(f"启动 HTTP MCP 服务器（FastAPI 同步模式），端口: {config.port}")
    logger.info(f"服务地址:")
    logger.info(f"  - API 文档: http://localhost:{config.port}/docs")
    logger.info(f"  - 健康检查: http://localhost:{config.port}/health")
    logger.info(f"  - MCP 端点: http://localhost:{config.port}/mcp")
    logger.info(f"  - 项目列表: http://localhost:{config.port}/api/projects")
    logger.info(f"  - Web 界面: http://localhost:{config.port}/web/template_editor.html")
    
    # 使用 uvicorn 启动（WSGI 兼容）
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=False,  # 生产环境建议关闭
        log_level=config.log_level.lower(),
        workers=1,  # 同步模式使用单个工作进程
        timeout_keep_alive=config.request_timeout,
        limit_max_requests=config.max_connections
    )


if __name__ == "__main__":
    main()
