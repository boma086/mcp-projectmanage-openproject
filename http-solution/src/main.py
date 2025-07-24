#!/usr/bin/env python3
"""
简单的 HTTP MCP 服务器
避免复杂的版本兼容性问题
"""
import os
import json
import time
import uuid
import threading
from datetime import datetime
from dotenv import load_dotenv
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

from src.adapters.openproject import OpenProjectAdapter
from src.services.resource_service import ResourceService
from src.services.prompt_service import PromptService
from src.services.template_service import TemplateService
from src.utils.logger import mcp_logger
from src.utils.exceptions import (
    MCPError, ParseError, InvalidRequest, MethodNotFound,
    ConfigurationError, handle_exception, validate_json_rpc_request
)

# Load environment variables
load_dotenv()

# Initialize services (thread-safe)
openproject_adapter = None
resource_service = None
prompt_service = None
template_service = None
_services_initialized = False
_init_lock = threading.Lock()

def initialize_services():
    """线程安全的服务初始化"""
    global openproject_adapter, resource_service, prompt_service, template_service, _services_initialized
    
    with _init_lock:
        if not _services_initialized:
            try:
                openproject_adapter = OpenProjectAdapter(
                    url=os.getenv("OPENPROJECT_URL"),
                    api_key=os.getenv("OPENPROJECT_API_KEY")
                )
                resource_service = ResourceService(openproject_adapter)
                prompt_service = PromptService(openproject_adapter)
                template_service = TemplateService()

                # 创建默认模板
                template_service.create_default_templates()
                
                _services_initialized = True
                mcp_logger.logger.info("OpenProject 适配器和服务初始化成功")
            except Exception as e:
                mcp_logger.log_error("服务初始化失败", e)
                raise

class MCPHandler(BaseHTTPRequestHandler):
    """MCP HTTP 请求处理器"""

    def do_GET(self):
        """处理 GET 请求 - 用于静态文件服务"""
        try:
            if self.path == '/':
                # 重定向到模板编辑器
                self.send_response(302)
                self.send_header('Location', '/web/template_editor.html')
                self.end_headers()
                return

            elif self.path.startswith('/web/'):
                # 服务静态文件
                file_path = self.path[1:]  # 移除开头的 '/'
                full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file_path)

                if os.path.exists(full_path) and os.path.isfile(full_path):
                    # 确定MIME类型
                    if full_path.endswith('.html'):
                        content_type = 'text/html; charset=utf-8'
                    elif full_path.endswith('.css'):
                        content_type = 'text/css'
                    elif full_path.endswith('.js'):
                        content_type = 'application/javascript'
                    else:
                        content_type = 'text/plain'

                    # 读取并发送文件
                    with open(full_path, 'rb') as f:
                        content = f.read()

                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                else:
                    self.send_error(404, "File not found")
                    return

            else:
                self.send_error(404, "Not found")

        except Exception as e:
            mcp_logger.log_error("处理GET请求时出现错误", e)
            self.send_error(500, "Internal server error")

    def do_POST(self):
        """处理 POST 请求"""
        # 确保服务已初始化
        if not _services_initialized:
            initialize_services()

        # 生成请求ID和记录开始时间
        request_id = str(uuid.uuid4())
        start_time = time.time()
        client_ip = self.client_address[0]

        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                raise InvalidRequest("Empty request body")

            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            # 验证JSON-RPC请求格式
            validate_json_rpc_request(request_data)

            # 使用请求中的ID，如果没有则使用生成的ID
            json_rpc_id = request_data.get('id', request_id)
            method = request_data.get('method')
            params = request_data.get('params', {})

            # 记录请求日志
            mcp_logger.log_request("POST", self.path, client_ip, json_rpc_id,
                                 {"method": method, "params_keys": list(params.keys())})

            # 处理不同的 MCP 方法
            if method == 'initialize':
                response = self.handle_initialize(json_rpc_id, params)
            elif method == 'tools/list':
                response = self.handle_list_tools(json_rpc_id)
            elif method == 'tools/call':
                response = self.handle_call_tool(json_rpc_id, params)
            elif method == 'resources/list':
                response = self.handle_list_resources(json_rpc_id)
            elif method == 'resources/templates/list':
                response = self.handle_list_resource_templates(json_rpc_id)
            elif method == 'resources/read':
                response = self.handle_read_resource(json_rpc_id, params)
            elif method == 'prompts/list':
                response = self.handle_list_prompts(json_rpc_id)
            elif method == 'prompts/get':
                response = self.handle_get_prompt(json_rpc_id, params)
            else:
                raise MethodNotFound(method)

            # 发送响应
            self.send_json_response(response)

            # 记录成功响应
            response_time = time.time() - start_time
            mcp_logger.log_response(json_rpc_id, 200, response_time)

        except json.JSONDecodeError as e:
            mcp_logger.log_error("JSON 解析错误", e, request_id)
            error_response = handle_exception(ParseError("Invalid JSON"), request_id)
            self.send_json_response(error_response)
        except MCPError as e:
            mcp_logger.log_error(f"MCP错误: {e.message}", e, request_id)
            error_response = handle_exception(e, request_id)
            self.send_json_response(error_response)
        except Exception as e:
            mcp_logger.log_error("处理请求时出现未知错误", e, request_id)
            error_response = handle_exception(e, request_id)
            self.send_json_response(error_response)
    
    def handle_initialize(self, request_id, params):
        """处理初始化请求"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {
                        "subscribe": False,
                        "listChanged": False
                    },
                    "prompts": {
                        "listChanged": False
                    }
                },
                "serverInfo": {
                    "name": "openproject-mcp",
                    "version": "1.0.0",
                    "description": "OpenProject MCP服务器，支持工具、资源、提示和模板功能"
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
            },
            {
                "name": "generate_monthly_report",
                "description": "生成月度项目报告",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID"},
                        "year": {"type": "integer", "description": "年份"},
                        "month": {"type": "integer", "description": "月份 (1-12)"}
                    },
                    "required": ["project_id", "year", "month"]
                }
            },
            {
                "name": "assess_project_risks",
                "description": "评估项目风险",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID"}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "analyze_team_workload",
                "description": "分析团队工作负载",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID"}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "check_project_health",
                "description": "检查项目健康度",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {"type": "string", "description": "项目ID"}
                    },
                    "required": ["project_id"]
                }
            },
            {
                "name": "list_report_templates",
                "description": "获取所有报告模板列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "get_report_template",
                "description": "获取指定报告模板",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string", "description": "模板ID"}
                    },
                    "required": ["template_id"]
                }
            },
            {
                "name": "save_report_template",
                "description": "保存报告模板",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string", "description": "模板ID"},
                        "template_data": {"type": "object", "description": "模板数据"}
                    },
                    "required": ["template_id", "template_data"]
                }
            },
            {
                "name": "generate_report_from_template",
                "description": "基于模板生成报告",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {"type": "string", "description": "模板ID"},
                        "project_id": {"type": "string", "description": "项目ID"},
                        "custom_data": {"type": "object", "description": "自定义数据"}
                    },
                    "required": ["template_id", "project_id"]
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
        from src.utils.exceptions import ToolExecutionError, InvalidParams, validate_tool_arguments

        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        if not tool_name:
            raise InvalidParams("Missing 'name' parameter for tool call")

        start_time = time.time()

        try:
            if tool_name == 'get_projects':
                validate_tool_arguments(tool_name, arguments, [])
                projects = openproject_adapter.get_projects(request_id)
                result = [{"id": p.id, "name": p.name, "identifier": p.identifier} for p in projects]
                content = f"找到 {len(projects)} 个项目:\n" + "\n".join([f"- {p['name']} (ID: {p['id']})" for p in result])

            elif tool_name == 'get_project':
                validate_tool_arguments(tool_name, arguments, ['project_id'])
                project_id = arguments.get('project_id')
                project = openproject_adapter.get_project(project_id, request_id)
                if project:
                    content = f"项目详情:\n名称: {project.name}\nID: {project.id}\n标识符: {project.identifier}"
                    if project.description:
                        content += f"\n描述: {project.description}"
                else:
                    content = f"未找到项目 ID: {project_id}"

            elif tool_name == 'get_work_packages':
                validate_tool_arguments(tool_name, arguments, [], ['project_id'])
                project_id = arguments.get('project_id')
                work_packages = openproject_adapter.get_work_packages(project_id, request_id)
                if work_packages:
                    content = f"找到 {len(work_packages)} 个工作包:\n" + "\n".join([
                        f"- {wp.subject} (ID: {wp.id}, 状态: {wp.status or '未知'})"
                        for wp in work_packages
                    ])
                else:
                    content = "未找到工作包"

            elif tool_name == 'generate_project_report':
                validate_tool_arguments(tool_name, arguments, ['project_id'])
                project_id = arguments.get('project_id')
                report = openproject_adapter.generate_project_report(project_id, request_id)
                content = "项目报告:\n" + format_report_content(report)

            elif tool_name == 'generate_monthly_report':
                validate_tool_arguments(tool_name, arguments, ['project_id', 'year', 'month'])
                project_id = arguments.get('project_id')
                year = arguments.get('year')
                month = arguments.get('month')
                report = openproject_adapter.generate_monthly_report(project_id, year, month)
                content = "月度报告:\n" + format_report_content(report)

            elif tool_name == 'assess_project_risks':
                validate_tool_arguments(tool_name, arguments, ['project_id'])
                project_id = arguments.get('project_id')
                report = openproject_adapter.assess_project_risks(project_id)
                content = "风险评估报告:\n" + format_report_content(report)

            elif tool_name == 'analyze_team_workload':
                validate_tool_arguments(tool_name, arguments, ['project_id'])
                project_id = arguments.get('project_id')
                report = openproject_adapter.analyze_team_workload(project_id)
                content = "团队工作负载分析:\n" + format_report_content(report)

            elif tool_name == 'check_project_health':
                validate_tool_arguments(tool_name, arguments, ['project_id'])
                project_id = arguments.get('project_id')
                report = openproject_adapter.check_project_health(project_id)
                content = "项目健康度检查:\n" + format_report_content(report)

            elif tool_name == 'list_report_templates':
                validate_tool_arguments(tool_name, arguments, [])
                templates = template_service.list_templates()
                content = f"找到 {len(templates)} 个报告模板:\n" + "\n".join([
                    f"- {t['name']} (ID: {t['template_id']}, 类型: {t['type']})"
                    for t in templates
                ])

            elif tool_name == 'get_report_template':
                validate_tool_arguments(tool_name, arguments, ['template_id'])
                template_id = arguments.get('template_id')
                template_data = template_service.get_template(template_id)
                if template_data:
                    template_info = template_data.get('template_info', {})
                    content = f"模板详情:\n名称: {template_info.get('name', template_id)}\n类型: {template_info.get('type', 'unknown')}\n描述: {template_info.get('description', '')}"
                else:
                    content = f"未找到模板 ID: {template_id}"

            elif tool_name == 'save_report_template':
                validate_tool_arguments(tool_name, arguments, ['template_id', 'template_data'])
                template_id = arguments.get('template_id')
                template_data = arguments.get('template_data')
                success = template_service.save_template(template_id, template_data)
                if success:
                    content = f"模板 {template_id} 保存成功"
                else:
                    content = f"模板 {template_id} 保存失败"

            elif tool_name == 'generate_report_from_template':
                validate_tool_arguments(tool_name, arguments, ['template_id', 'project_id'], ['custom_data'])
                template_id = arguments.get('template_id')
                project_id = arguments.get('project_id')
                custom_data = arguments.get('custom_data', {})

                # 获取项目数据
                project = openproject_adapter.get_project(project_id, request_id)
                work_packages = openproject_adapter.get_work_packages(project_id, request_id)

                # 准备模板数据
                template_data = {
                    'project_name': project.name if project else f'项目{project_id}',
                    'project_id': project_id,
                    'start_date': datetime.now().strftime('%Y-%m-%d'),
                    'end_date': datetime.now().strftime('%Y-%m-%d'),
                    'total_work_packages': len(work_packages),
                    'completed_work_packages': len([wp for wp in work_packages if wp.status == 'Closed']),
                    'in_progress_work_packages': len([wp for wp in work_packages if wp.status == 'In progress']),
                    'completion_rate': round(len([wp for wp in work_packages if wp.status == 'Closed']) / len(work_packages) * 100, 1) if work_packages else 0,
                    **custom_data
                }

                content = template_service.render_template(template_id, template_data)

            else:
                raise ToolExecutionError(tool_name, f"Unknown tool: {tool_name}")

            # 记录成功的工具调用
            execution_time = time.time() - start_time
            mcp_logger.log_tool_call(tool_name, arguments, request_id, True, execution_time)

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
            # 记录失败的工具调用
            execution_time = time.time() - start_time
            mcp_logger.log_tool_call(tool_name, arguments, request_id, False, execution_time)

            # 重新抛出异常，让上层处理
            if isinstance(e, (InvalidParams, ToolExecutionError)):
                raise
            else:
                raise ToolExecutionError(tool_name, str(e), e)

    def send_json_response(self, data):
        """发送 JSON 响应"""
        response_json = json.dumps(data, ensure_ascii=False, indent=2)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_json.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(response_json.encode('utf-8'))

    def handle_list_resources(self, request_id):
        """处理资源列表请求"""
        try:
            resources = resource_service.list_resources()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resources": resources
                }
            }
        except Exception as e:
            mcp_logger.log_error("获取资源列表失败", e, request_id)
            raise

    def handle_list_resource_templates(self, request_id):
        """处理资源模板列表请求"""
        try:
            templates = resource_service.list_resource_templates()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "resourceTemplates": templates
                }
            }
        except Exception as e:
            mcp_logger.log_error("获取资源模板列表失败", e, request_id)
            raise

    def handle_read_resource(self, request_id, params):
        """处理读取资源请求"""
        from src.utils.exceptions import InvalidParams

        uri = params.get('uri')
        if not uri:
            raise InvalidParams("Missing 'uri' parameter for resource read")

        try:
            content = resource_service.read_resource(str(uri), request_id)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "contents": [content]
                }
            }
        except Exception as e:
            mcp_logger.log_error(f"读取资源失败: {uri}", e, request_id)
            raise

    def handle_list_prompts(self, request_id):
        """处理提示列表请求"""
        try:
            prompts = prompt_service.list_prompts()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": prompts
                }
            }
        except Exception as e:
            mcp_logger.log_error("获取提示列表失败", e, request_id)
            raise

    def handle_get_prompt(self, request_id, params):
        """处理获取提示请求"""
        from src.utils.exceptions import InvalidParams

        name = params.get('name')
        if not name:
            raise InvalidParams("Missing 'name' parameter for prompt get")

        arguments = params.get('arguments', {})

        try:
            prompt_content = prompt_service.get_prompt(name, arguments, request_id)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": prompt_content
            }
        except Exception as e:
            mcp_logger.log_error(f"获取提示失败: {name}", e, request_id)
            raise

    def log_message(self, format, *args):
        """重写日志方法"""
        mcp_logger.logger.info(f"{self.address_string()} - {format % args}")

def format_report_content(report):
    """
    Helper to format report content consistently.
    """
    # Handle Report objects (Pydantic models)
    title = getattr(report, 'title', '')
    summary = getattr(report, 'summary', '')
    sections = getattr(report, 'sections', [])

    content = f"{title}\n\n{summary}"
    if sections:
        content += "\n\n详细信息:"
        for section in sections:
            # Sections are ReportSection objects (Pydantic models)
            section_title = getattr(section, 'title', '')
            section_content = getattr(section, 'content', '')
            content += f"\n\n## {section_title}\n{section_content}"
    return content

def main():
    """主函数"""
    port = int(os.getenv("PORT", 8010))
    server_address = ('', port)

    httpd = HTTPServer(server_address, MCPHandler)
    mcp_logger.logger.info(f"启动 HTTP MCP 服务器，端口: {port}")
    mcp_logger.logger.info(f"测试 URL: http://localhost:{port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        mcp_logger.logger.info("服务器停止")
        httpd.server_close()

if __name__ == "__main__":
    main()
