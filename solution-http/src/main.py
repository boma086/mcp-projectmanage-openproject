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

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv

# 导入本地模块
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from config import get_http_config, HTTPSolutionConfig
from dependencies import (
    get_openproject_adapter, get_mcp_handler, validate_openproject_connection,
    cleanup_dependencies, SyncAsyncAdapter
)
from routers import projects_router, work_packages_router, users_router
from monitoring import (
    get_monitoring, get_health_checker, update_health_checker_config,
    monitor_http_request, monitor_mcp_operation
)
from monitoring.error_tracking import (
    get_errors, get_error_stats, get_error_trends, 
    resolve_error, export_errors
)

# 导入核心库
from mcp_core import (
    MCPHandler, get_logger, Config, set_global_config,
    MCPError
)

# 加载环境变量
load_dotenv()

# 全局配置
http_config = get_http_config()
logger = get_logger("mcp.http")


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("启动 HTTP MCP 服务...")
    initialize_core_config()
    
    # 初始化监控
    logger.info("初始化监控系统...")
    monitoring = get_monitoring()
    health_checker = get_health_checker(http_config.openproject_url, http_config.openproject_api_key)
    logger.info("监控系统初始化完成")
    
    yield
    
    # 关闭时清理
    logger.info("清理 HTTP MCP 服务...")
    cleanup_dependencies()


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

# 注册路由器
app.include_router(projects_router)
app.include_router(work_packages_router)
app.include_router(users_router)

# 错误跟踪端点已通过函数导入


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
            "openapi": "/openapi.json",
            "projects": "/api/projects",
            "work_packages": "/api/work-packages",
            "users": "/api/users"
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
    """基本健康检查端点"""
    try:
        health_checker = get_health_checker(http_config.openproject_url, http_config.openproject_api_key)
        result = health_checker.check_liveness()
        
        return {
            "status": result.overall_status.value,
            "timestamp": result.timestamp,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "duration_ms": check.duration_ms,
                    "message": check.message
                }
                for check in result.results
            ]
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/health/ready")
async def readiness_check():
    """就绪检查端点"""
    try:
        health_checker = get_health_checker(http_config.openproject_url, http_config.openproject_api_key)
        result = health_checker.check_readiness()
        
        return {
            "status": result.overall_status.value,
            "timestamp": result.timestamp,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "duration_ms": check.duration_ms,
                    "message": check.message
                }
                for check in result.results
            ]
        }
        
    except Exception as e:
        logger.error(f"就绪检查失败: {e}")
        raise HTTPException(status_code=500, detail="Readiness check failed")


@app.get("/health/deep")
async def deep_health_check():
    """深度健康检查端点"""
    try:
        health_checker = get_health_checker(http_config.openproject_url, http_config.openproject_api_key)
        result = health_checker.check_deep_health()
        
        return {
            "status": result.overall_status.value,
            "timestamp": result.timestamp,
            "summary": {
                "total_checks": result.total_checks,
                "healthy_checks": result.healthy_checks,
                "degraded_checks": result.degraded_checks,
                "unhealthy_checks": result.unhealthy_checks
            },
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "duration_ms": check.duration_ms,
                    "message": check.message,
                    "details": check.details
                }
                for check in result.results
            ]
        }
        
    except Exception as e:
        logger.error(f"深度健康检查失败: {e}")
        raise HTTPException(status_code=500, detail="Deep health check failed")


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus 指标端点"""
    try:
        monitoring = get_monitoring()
        metrics_data = monitoring.metrics.get_metrics()
        
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=metrics_data,
            media_type="text/plain; version=0.0.4"
        )
        
    except Exception as e:
        logger.error(f"获取指标失败: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@app.get("/errors")
async def get_errors_endpoint(request: Request):
    """获取错误列表"""
    return get_errors(request)


@app.get("/errors/stats")
async def get_error_stats_endpoint(request: Request):
    """获取错误统计"""
    return get_error_stats(request)


@app.get("/errors/trends")
async def get_error_trends_endpoint(request: Request):
    """获取错误趋势"""
    return get_error_trends(request)


@app.post("/errors/resolve")
async def resolve_error_endpoint(request: Request):
    """解决错误"""
    return resolve_error(request)


@app.get("/errors/export")
async def export_errors_endpoint(request: Request):
    """导出错误"""
    return export_errors(request)


@app.post("/mcp")
async def handle_mcp_request(
    request: Request,
    mcp_handler: MCPHandler = Depends(get_mcp_handler)
):
    """处理 MCP 请求 - 主要 API 端点"""
    monitoring = get_monitoring()
    request_data = None
    
    # 使用监控中间件跟踪请求
    with monitoring.monitor_request(request) as metrics:
        try:
            # 读取请求体
            request_data = await request.json()
            method = request_data.get('method', 'unknown')
            
            # 使用监控装饰器跟踪 MCP 操作
            @monitor_mcp_operation("handle_request", "mcp_handler")
            def process_request():
                return mcp_handler.handle_request(request_data)
            
            response = process_request()
            
            # 更新响应状态码
            metrics.status_code = 200
            
            return JSONResponse(content=response)
            
        except Exception as e:
            # 更新错误指标
            metrics.status_code = 500
            metrics.error = str(e)
            
            logger.error(f"处理 MCP 请求失败: {e}")
            
            # 返回 JSON-RPC 错误响应
            error_response = {
                "jsonrpc": "2.0",
                "id": request_data.get("id") if request_data else None,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            return JSONResponse(content=error_response, status_code=500)




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
    logger.info(f"  - 项目 API: http://localhost:{config.port}/api/projects")
    logger.info(f"  - 工作包 API: http://localhost:{config.port}/api/work-packages")
    logger.info(f"  - 用户 API: http://localhost:{config.port}/api/users")
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
