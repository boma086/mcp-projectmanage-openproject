#!/usr/bin/env python3
"""
简单的 HTTP MCP 服务器
避免复杂的版本兼容性问题
"""
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from adapters.openproject import OpenProjectAdapter

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenProject adapter
openproject_adapter = None

class MCPHandler(BaseHTTPRequestHandler):
    """MCP HTTP 请求处理器"""
    
    def do_POST(self):
        """处理 POST 请求"""
        global openproject_adapter
        
        # 初始化适配器
        if not openproject_adapter:
            try:
                openproject_adapter = OpenProjectAdapter(
                    url=os.getenv("OPENPROJECT_URL"),
                    api_key=os.getenv("OPENPROJECT_API_KEY")
                )
                logger.info("OpenProject 适配器初始化成功")
            except Exception as e:
                logger.error(f"OpenProject 适配器初始化失败: {e}")
                self.send_error_response(f"OpenProject 适配器初始化失败: {e}")
                return
        
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            logger.debug(f"收到请求: {request_data}")
            
            # 处理不同的 MCP 方法
            method = request_data.get('method')
            request_id = request_data.get('id')
            params = request_data.get('params', {})
            
            if method == 'initialize':
                response = self.handle_initialize(request_id, params)
            elif method == 'tools/list':
                response = self.handle_list_tools(request_id)
            elif method == 'tools/call':
                response = self.handle_call_tool(request_id, params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # 发送响应
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"处理请求时出错: {e}")
            self.send_error_response(str(e))
    
    def handle_initialize(self, request_id, params):
        """处理初始化请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "openproject-mcp",
                    "version": "1.0.0"
                }
            }
        }
    
    def handle_list_tools(self, request_id):
        """处理工具列表请求"""
        tools = [
            {
                "name": "get_projects",
                "description": "获取所有项目列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_project",
                "description": "根据项目ID获取项目详情",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID"}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "get_work_packages",
                "description": "获取工作包列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID（可选）"}
                    },
                    "required": []
                }
            },
            {
                "name": "generate_project_report",
                "description": "生成项目报告",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID"}
                    },
                    "required": ["project_id"]
                }
            }
        ]
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
    
    def handle_call_tool(self, request_id, params):
        """处理工具调用请求"""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})
        
        try:
            if tool_name == 'get_projects':
                projects = openproject_adapter.get_projects()
                result = [{"id": p.id, "name": p.name, "identifier": p.identifier} for p in projects]
                content = f"找到 {len(projects)} 个项目:\n" + "\n".join([f"- {p['name']} (ID: {p['id']})" for p in result])
            
            elif tool_name == 'get_project':
                project_id = arguments.get('project_id')
                project = openproject_adapter.get_project(project_id)
                if project:
                    content = f"项目详情:\n名称: {project.name}\nID: {project.id}\n标识符: {project.identifier}"
                else:
                    content = f"未找到项目 ID: {project_id}"
            
            elif tool_name == 'get_work_packages':
                project_id = arguments.get('project_id')
                work_packages = openproject_adapter.get_work_packages(project_id)
                if work_packages:
                    content = f"找到 {len(work_packages)} 个工作包:\n" + "\n".join([f"- {wp.subject} (ID: {wp.id})" for wp in work_packages])
                else:
                    content = "未找到工作包"
            
            elif tool_name == 'generate_project_report':
                project_id = arguments.get('project_id')
                report = openproject_adapter.generate_project_report(project_id)
                content = f"项目报告:\n{report.title}\n\n{report.summary}"
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": content
                        }
                    ]
                }
            }
            
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}"
                }
            }
    
    def send_json_response(self, data):
        """发送 JSON 响应"""
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_json.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, error_message):
        """发送错误响应"""
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": error_message
            }
        }
        self.send_json_response(error_response)
    
    def log_message(self, format, *args):
        """重写日志方法"""
        logger.info(f"{self.address_string()} - {format % args}")

def main():
    """主函数"""
    port = int(os.getenv("PORT", 8010))
    server_address = ('', port)
    
    httpd = HTTPServer(server_address, MCPHandler)
    logger.info(f"启动 HTTP MCP 服务器，端口: {port}")
    logger.info(f"测试 URL: http://localhost:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务器停止")
        httpd.server_close()

if __name__ == "__main__":
    main()
