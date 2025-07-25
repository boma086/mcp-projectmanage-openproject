#!/usr/bin/env python3
"""
精简的 HTTP MCP 服务器 - 使用核心库
"""
import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
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

# 初始化配置
# 1. HTTP 解决方案专用配置
http_config = get_http_config()

# 2. 核心库配置（使用基础配置，不包含解决方案特定字段）
logger = get_logger("mcp.http")
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
    logger.info("配置初始化成功")
except Exception as e:
    logger.error(f"配置初始化失败: {e}")
    raise MCPError(f"Failed to initialize config: {e}")

# 全局服务实例
openproject_client = None
mcp_handler = None
_services_initialized = False
_init_lock = threading.Lock()


def initialize_services():
    """线程安全的服务初始化"""
    global openproject_client, mcp_handler, _services_initialized
    
    with _init_lock:
        if not _services_initialized:
            try:
                # 创建 OpenProject 客户端
                openproject_client = HTTPOpenProjectClient()
                
                # 创建 MCP 处理器
                mcp_handler = MCPHandler(openproject_client)
                
                _services_initialized = True
                logger.info("服务初始化成功")
            except Exception as e:
                logger.error("服务初始化失败", e)
                raise


class HTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    def do_GET(self):
        """处理 GET 请求 - 用于静态文件和健康检查"""
        try:
            if self.path == '/':
                # 返回服务信息
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                info = {
                    "name": "MCP OpenProject Server",
                    "version": "1.0.0",
                    "status": "running",
                    "endpoints": {
                        "mcp": "/mcp",
                        "health": "/health"
                    }
                }
                self.wfile.write(json.dumps(info, ensure_ascii=False).encode('utf-8'))
                
            elif self.path == '/health':
                # 健康检查
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                
                health = {
                    "status": "healthy",
                    "services": {
                        "openproject": "connected" if openproject_client else "disconnected",
                        "mcp_handler": "ready" if mcp_handler else "not_ready"
                    }
                }
                self.wfile.write(json.dumps(health, ensure_ascii=False).encode('utf-8'))
                
            elif self.path.startswith('/web/'):
                # 服务静态文件（从共享 Web 目录）
                self.serve_static_file()
                
            else:
                self.send_error(404, "Not found")
                
        except Exception as e:
            logger.error("处理 GET 请求失败", e)
            self.send_error(500, "Internal server error")

    def do_POST(self):
        """处理 POST 请求 - MCP 协议"""
        # 确保服务已初始化
        if not _services_initialized:
            initialize_services()

        try:
            if self.path == '/mcp':
                self.handle_mcp_request()
            else:
                self.send_error(404, "Not found")

        except Exception as e:
            logger.error("处理 POST 请求失败", e)
            self.send_error(500, "Internal server error")

    def handle_mcp_request(self):
        """处理 MCP 请求"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            # 解析 JSON
            request_data = json.loads(request_body)
            
            # 使用核心库的 MCP 处理器（在线程中运行异步代码）
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(mcp_handler.handle_request(request_data))
            finally:
                loop.close()
            
            # 发送响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            response_json = json.dumps(response, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            
        except json.JSONDecodeError as e:
            logger.error("JSON 解析错误", e)
            self.send_json_error(-32700, "Parse error")
        except Exception as e:
            logger.error("处理 MCP 请求失败", e)
            self.send_json_error(-32603, "Internal error")

    def do_OPTIONS(self):
        """处理 OPTIONS 请求 - CORS 预检"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def serve_static_file(self):
        """服务静态文件"""
        try:
            # 从共享 Web 目录服务文件
            file_path = self.path[5:]  # 移除 '/web/' 前缀
            full_path = os.path.join('shared-web', file_path)
            
            if os.path.exists(full_path) and os.path.isfile(full_path):
                with open(full_path, 'rb') as f:
                    content = f.read()
                
                # 设置 Content-Type
                if file_path.endswith('.html'):
                    content_type = 'text/html'
                elif file_path.endswith('.css'):
                    content_type = 'text/css'
                elif file_path.endswith('.js'):
                    content_type = 'application/javascript'
                else:
                    content_type = 'application/octet-stream'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_error(404, "File not found")
                
        except Exception as e:
            logger.error(f"服务静态文件失败: {self.path}", e)
            self.send_error(500, "Internal server error")

    def send_json_error(self, code: int, message: str, request_id=None):
        """发送 JSON-RPC 错误响应"""
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        response_json = json.dumps(error_response, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))

    def log_message(self, format, *args):
        """重写日志方法"""
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    """主函数"""
    # 使用 HTTP 解决方案配置
    config = get_http_config()

    # 初始化服务
    initialize_services()

    # 启动 HTTP 服务器
    server_address = (config.host, config.port)
    httpd = HTTPServer(server_address, HTTPRequestHandler)
    
    logger.info(f"启动 HTTP MCP 服务器，地址: {config.host}:{config.port}")
    logger.info(f"服务地址:")
    logger.info(f"  - 主页: http://localhost:{config.port}/")
    logger.info(f"  - 健康检查: http://localhost:{config.port}/health")
    logger.info(f"  - MCP 端点: http://localhost:{config.port}/mcp")
    logger.info(f"  - Web 界面: http://localhost:{config.port}/web/template_editor.html")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器停止")
        httpd.server_close()


if __name__ == "__main__":
    main()
