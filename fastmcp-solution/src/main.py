import os
import asyncio
import logging
from dotenv import load_dotenv
from fastmcp import FastMCP

from adapters.openproject import OpenProjectAdapter
from models.schemas import Project, WorkPackage, Report

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastMCP application instance
mcp = FastMCP("OpenProject-MCP")

# Initialize OpenProject adapter
try:
    openproject_adapter = OpenProjectAdapter(
        url=os.getenv("OPENPROJECT_URL"),
        api_key=os.getenv("OPENPROJECT_API_KEY")
    )
    # Test connection
    test_projects = openproject_adapter.get_projects()
    logger.info(f"OpenProject 连接成功，找到 {len(test_projects)} 个项目")
except Exception as e:
    logger.error(f"OpenProject 初始化失败: {e}")
    openproject_adapter = None

# Define tools - 移除初始化检查
@mcp.tool()
def get_projects() -> list[Project]:
    """获取所有项目列表"""
    logger.debug("调用 get_projects 工具")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.get_projects()

@mcp.tool()
def get_project(project_id: str) -> Project:
    """根据项目ID获取项目详情"""
    logger.debug(f"调用 get_project 工具，project_id: {project_id}")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.get_project(project_id)

@mcp.tool()
def get_work_packages(project_id: str = None) -> list[WorkPackage]:
    """获取工作包列表，可选择指定项目ID"""
    logger.debug(f"调用 get_work_packages 工具，project_id: {project_id}")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.get_work_packages(project_id)

@mcp.tool()
def get_work_package(work_package_id: str) -> WorkPackage:
    """根据工作包ID获取工作包详情"""
    logger.debug(f"调用 get_work_package 工具，work_package_id: {work_package_id}")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.get_work_package(work_package_id)

@mcp.tool()
def create_work_package(project_id: str, subject: str, description: str = None, work_package_type: str = "Task") -> WorkPackage:
    """创建新的工作包"""
    logger.debug(f"调用 create_work_package 工具，project_id: {project_id}, subject: {subject}")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.create_work_package(project_id, subject, description, work_package_type)

@mcp.tool()
def update_work_package(work_package_id: str, subject: str = None, description: str = None, status: str = None) -> WorkPackage:
    """更新工作包信息"""
    logger.debug(f"调用 update_work_package 工具，work_package_id: {work_package_id}")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.update_work_package(work_package_id, subject, description, status)

@mcp.tool()
def generate_project_report(project_id: str) -> Report:
    """生成项目报告"""
    logger.debug(f"调用 generate_project_report 工具，project_id: {project_id}")
    if not openproject_adapter:
        raise Exception("OpenProject 适配器未初始化")
    return openproject_adapter.generate_project_report(project_id)

@mcp.resource("openproject://docs")
def get_openproject_docs():
    """
    OpenProject API 文档和使用指南
    
    本资源提供了 OpenProject API 的完整文档，包括：
    - 项目管理功能
    - 工作包操作
    - 用户和权限管理
    - API 认证方式
    
    详细文档请参考: https://www.openproject.org/docs/api/
    """

# Start server
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8010))
    logger.info(f"正在启动 FastMCP 服务，端口: {port}")
    
    try:
        logger.info(f"FastMCP 服务启动成功，监听端口: {port}")
        logger.debug("调试：准备调用 mcp.run()")
        # 使用 HTTP 传输，更稳定可靠
        mcp.run(
            transport="http",  # 使用 HTTP 传输
            port=port,
            host="0.0.0.0"
        )
    except Exception as e:
        logger.error(f"FastMCP 服务启动失败: {e}")
        import traceback
        traceback.print_exc()