"""
MCP 工具管理器
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta

from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import InvalidParams, NotFoundError
from mcp_core.shared.logger import get_logger


class MCPToolManager:
    """MCP 工具管理器"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
        self.logger = get_logger("mcp.tools")
    
    async def list_tools(self) -> Dict[str, Any]:
        """列出所有可用工具"""
        tools = [
            {
                "name": "generate_weekly_report",
                "description": "生成项目周报",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "项目 ID"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期 (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期 (YYYY-MM-DD)"
                        }
                    },
                    "required": ["project_id", "start_date", "end_date"]
                }
            },
            {
                "name": "generate_monthly_report",
                "description": "生成项目月报",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "项目 ID"
                        },
                        "year": {
                            "type": "integer",
                            "description": "年份"
                        },
                        "month": {
                            "type": "integer",
                            "description": "月份 (1-12)"
                        }
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
                        "project_id": {
                            "type": "string",
                            "description": "项目 ID"
                        }
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
                "name": "save_report_template",
                "description": "保存报告模板",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "模板 ID"
                        },
                        "template_data": {
                            "type": "object",
                            "description": "模板数据"
                        }
                    },
                    "required": ["template_id", "template_data"]
                }
            },
            {
                "name": "generate_report_from_template",
                "description": "使用模板生成报告",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_id": {
                            "type": "string",
                            "description": "模板 ID"
                        },
                        "project_id": {
                            "type": "string",
                            "description": "项目 ID"
                        },
                        "custom_data": {
                            "type": "object",
                            "description": "自定义数据（可选）"
                        }
                    },
                    "required": ["template_id", "project_id"]
                }
            },
            {
                "name": "generate_enhanced_weekly_report",
                "description": "生成增强型项目周报（支持多语言和详细指标）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "项目 ID"
                        },
                        "start_date": {
                            "type": "string",
                            "description": "开始日期 (YYYY-MM-DD)"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期 (YYYY-MM-DD)"
                        },
                        "language": {
                            "type": "string",
                            "description": "报告语言 (zh/ja/en)",
                            "enum": ["zh", "ja", "en"]
                        }
                    },
                    "required": ["project_id", "start_date", "end_date"]
                }
            },
            {
                "name": "generate_enhanced_monthly_report",
                "description": "生成增强型项目月报（支持多语言和详细指标）",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "project_id": {
                            "type": "string",
                            "description": "项目 ID"
                        },
                        "year": {
                            "type": "integer",
                            "description": "年份"
                        },
                        "month": {
                            "type": "integer",
                            "description": "月份 (1-12)"
                        },
                        "language": {
                            "type": "string",
                            "description": "报告语言 (zh/ja/en)",
                            "enum": ["zh", "ja", "en"]
                        }
                    },
                    "required": ["project_id", "year", "month"]
                }
            }
        ]
        
        return {"tools": tools}
    
    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定工具"""
        tool_name = params.get("name")
        if not tool_name:
            raise InvalidParams("Missing tool name")
        
        arguments = params.get("arguments", {})
        
        self.logger.info(f"Calling tool: {tool_name}")
        
        try:
            if tool_name == "generate_weekly_report":
                return await self._generate_weekly_report(arguments)
            elif tool_name == "generate_monthly_report":
                return await self._generate_monthly_report(arguments)
            elif tool_name == "assess_project_risks":
                return await self._assess_project_risks(arguments)
            elif tool_name == "list_report_templates":
                return await self._list_report_templates(arguments)
            elif tool_name == "save_report_template":
                return await self._save_report_template(arguments)
            elif tool_name == "generate_report_from_template":
                return await self._generate_report_from_template(arguments)
            elif tool_name == "generate_enhanced_weekly_report":
                return await self._generate_enhanced_weekly_report(arguments)
            elif tool_name == "generate_enhanced_monthly_report":
                return await self._generate_enhanced_monthly_report(arguments)
            else:
                raise InvalidParams(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed", e)
            raise
    
    
    async def _generate_weekly_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """生成周报"""
        project_id = arguments.get("project_id")
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        
        if not all([project_id, start_date, end_date]):
            raise InvalidParams("Missing required parameters: project_id, start_date, end_date")
        
        report = await self.client.generate_weekly_report(project_id, start_date, end_date)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": report.to_markdown()
                }
            ]
        }
    
    async def _generate_monthly_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """生成月报"""
        project_id = arguments.get("project_id")
        year = arguments.get("year")
        month = arguments.get("month")
        
        if not all([project_id, year, month]):
            raise InvalidParams("Missing required parameters: project_id, year, month")
        
        report = await self.client.generate_monthly_report(project_id, year, month)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": report.to_markdown()
                }
            ]
        }
    
    async def _assess_project_risks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """评估项目风险"""
        project_id = arguments.get("project_id")
        if not project_id:
            raise InvalidParams("Missing project_id")
        
        report = await self.client.assess_project_risks(project_id)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": report.to_markdown()
                }
            ]
        }

    async def _list_report_templates(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """获取报告模板列表"""
        import os
        import yaml

        templates = []
        templates_dir = os.path.join(os.path.dirname(__file__), "../../../../templates/reports")

        if os.path.exists(templates_dir):
            for root, dirs, files in os.walk(templates_dir):
                for file in files:
                    if file.endswith('.yaml') or file.endswith('.yml'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                template_data = yaml.safe_load(f)
                                if template_data and 'template_info' in template_data:
                                    template_info = template_data['template_info']
                                    templates.append({
                                        "id": os.path.splitext(file)[0],
                                        "name": template_info.get('name', file),
                                        "type": template_info.get('type', 'unknown'),
                                        "description": template_info.get('description', ''),
                                        "version": template_info.get('version', '1.0')
                                    })
                        except Exception as e:
                            self.logger.warning(f"Failed to load template {file_path}: {e}")

        # 格式化输出
        if templates:
            text = "可用的报告模板:\n\n"
            for template in templates:
                text += f"- {template['name']} (ID: {template['id']}, 类型: {template['type']})\n"
                if template['description']:
                    text += f"  描述: {template['description']}\n"
                text += "\n"
        else:
            text = "未找到任何报告模板"

        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }

    async def _save_report_template(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """保存报告模板"""
        import os
        import yaml
        from datetime import datetime

        template_id = arguments.get("template_id")
        template_data = arguments.get("template_data")

        if not template_id or not template_data:
            raise InvalidParams("Missing required parameters: template_id, template_data")

        # 添加时间戳
        if 'template_info' in template_data:
            template_data['template_info']['updated_at'] = datetime.now().isoformat()

        # 确定保存路径
        templates_dir = os.path.join(os.path.dirname(__file__), "../../../../templates/reports")
        template_type = template_data.get('template_info', {}).get('type', 'custom')
        type_dir = os.path.join(templates_dir, template_type)

        # 创建目录
        os.makedirs(type_dir, exist_ok=True)

        # 保存文件
        file_path = os.path.join(type_dir, f"{template_id}.yaml")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, allow_unicode=True)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"模板 {template_id} 保存成功"
                    }
                ]
            }
        except Exception as e:
            self.logger.error(f"Failed to save template {template_id}: {e}")
            raise InvalidParams(f"Failed to save template: {str(e)}")

    async def _generate_report_from_template(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """使用模板生成报告"""
        import os
        import yaml
        from jinja2 import Template, Environment
        from datetime import datetime, timedelta

        template_id = arguments.get("template_id")
        project_id = arguments.get("project_id")
        custom_data = arguments.get("custom_data", {})

        if not template_id or not project_id:
            raise InvalidParams("Missing required parameters: template_id, project_id")

        # 查找模板文件
        templates_dir = os.path.join(os.path.dirname(__file__), "../../../../templates/reports")
        template_file = None

        for root, dirs, files in os.walk(templates_dir):
            for file in files:
                if file == f"{template_id}.yaml" or file == f"{template_id}.yml":
                    template_file = os.path.join(root, file)
                    break
            if template_file:
                break

        if not template_file:
            raise InvalidParams(f"Template not found: {template_id}")

        # 加载模板
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
        except Exception as e:
            raise InvalidParams(f"Failed to load template: {str(e)}")

        # 获取项目数据
        project = await self.client.get_project(project_id)
        if not project:
            raise InvalidParams(f"Project not found: {project_id}")

        # 获取工作包数据
        work_packages = await self.client.get_work_packages(project_id)

        # 修复完成度计算逻辑 - 基于OpenProject实际状态
        completed_wps = 0
        in_progress_wps = 0
        new_wps = 0
        scheduled_wps = 0
        total_progress = 0

        # OpenProject状态映射
        status_mapping = {
            # 完成状态
            'closed': 100, 'resolved': 100, 'done': 100, 'completed': 100,
            'finished': 100, 'delivered': 100, '完成': 100, '已完成': 100,

            # 进行中状态
            'in progress': 50, 'in-progress': 50, 'active': 50, 'working': 50,
            'ongoing': 50, '进行中': 50, '处理中': 50,

            # 新建/未开始状态
            'new': 0, 'open': 0, 'created': 0, 'todo': 0, 'backlog': 0,
            'not started': 0, '新建': 0, '未开始': 0,

            # 计划中状态
            'scheduled': 10, 'planned': 10, 'to be scheduled': 5,
            '计划中': 10, '已计划': 10,

            # 其他状态
            'rejected': 0, 'cancelled': 0, 'on hold': 0, 'blocked': 0,
            '已拒绝': 0, '已取消': 0, '暂停': 0, '阻塞': 0
        }

        for wp in work_packages:
            status = wp.status.lower() if wp.status else 'unknown'

            # 获取状态对应的进度值
            if status in status_mapping:
                progress = status_mapping[status]
            elif wp.progress is not None and wp.progress >= 0:
                # 如果有具体进度信息，使用实际进度
                progress = wp.progress
            else:
                # 未知状态默认为0
                progress = 0

            total_progress += progress

            # 统计各状态数量
            if progress >= 100:
                completed_wps += 1
            elif progress >= 30:  # 进行中的阈值
                in_progress_wps += 1
            elif progress >= 5:   # 已计划的阈值
                scheduled_wps += 1
            else:
                new_wps += 1

        total_wps = len(work_packages)
        # 使用加权平均计算整体完成率
        completion_rate = round(total_progress / total_wps, 1) if total_wps > 0 else 0

        # 准备模板变量
        now = datetime.now()
        start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')

        # 分析工作包状态分布
        status_distribution = {}
        for wp in work_packages:
            status = wp.status or "未分配状态"
            status_distribution[status] = status_distribution.get(status, 0) + 1

        # 创建Jinja2环境并添加自定义过滤器
        def add_days_filter(date_str, days):
            """添加天数到日期字符串"""
            try:
                if isinstance(date_str, str):
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                else:
                    date_obj = date_str
                new_date = date_obj + timedelta(days=days)
                return new_date.strftime("%Y-%m-%d")
            except:
                return date_str

        def zfill_filter(value, width):
            """用零填充数字到指定宽度"""
            return str(value).zfill(width)

        # 创建Jinja2环境
        jinja_env = Environment()
        jinja_env.filters['add_days'] = add_days_filter
        jinja_env.filters['zfill'] = zfill_filter

        template_vars = {
            "project_name": project.name,
            "project_id": project.id,
            "project_description": project.description or "",
            "start_date": start_date,
            "end_date": end_date,
            "completion_rate": completion_rate,
            "completed_work_packages": completed_wps,
            "in_progress_work_packages": in_progress_wps,
            "new_work_packages": new_wps,
            "scheduled_work_packages": scheduled_wps,
            "total_work_packages": total_wps,
            "remaining_work_packages": total_wps - completed_wps,
            "status_distribution": status_distribution,
            "team_member_count": 5,  # 示例数据
            # 日本式报告需要的详细信息
            "report_date": end_date,
            "project_health_status": "良好" if completion_rate >= 70 else "要注意" if completion_rate >= 30 else "要対策",
            "work_packages_today": [],  # 今日的工作包（可以通过日期过滤）
            "quality_score": 95,  # 品质分数
            "budget_status": "予算内",  # 预算状态
            "risk_level": "低" if completion_rate >= 70 else "中" if completion_rate >= 30 else "高",
            **custom_data
        }

        # 渲染标题
        title_template = jinja_env.from_string(template_data.get('title_template', '{{project_name}} 报告'))
        title = title_template.render(**template_vars)

        # 渲染内容
        content = f"# {title}\n\n"

        sections = template_data.get('sections', [])
        for section in sorted(sections, key=lambda x: x.get('order', 999)):
            section_name = section.get('section_name', '')
            content_template = section.get('content_template', '')

            if content_template:
                try:
                    section_template = jinja_env.from_string(content_template)
                    section_content = section_template.render(**template_vars)
                    content += f"{section_content}\n\n"
                except Exception as e:
                    self.logger.warning(f"Failed to render section {section_name}: {e}")
                    content += f"## {section_name}\n\n渲染失败: {str(e)}\n\n"

        return {
            "content": [
                {
                    "type": "text",
                    "text": content
                }
            ]
        }
    
    async def _generate_enhanced_weekly_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """生成增强型周报"""
        project_id = arguments.get("project_id")
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        language_str = arguments.get("language", "ja")
        
        if not all([project_id, start_date, end_date]):
            raise InvalidParams("Missing required parameters: project_id, start_date, end_date")
        
        # 导入增强型报告生成器
        try:
            from app.services.enhanced_report_generator import EnhancedReportGeneratorService, ReportLanguage
            
            # 创建增强型报告生成器实例
            enhanced_generator = EnhancedReportGeneratorService(self.client)
            
            # 解析语言参数
            language_map = {
                "zh": ReportLanguage.CHINESE,
                "ja": ReportLanguage.JAPANESE,
                "en": ReportLanguage.ENGLISH
            }
            language = language_map.get(language_str.lower(), ReportLanguage.JAPANESE)
            
            # 生成增强型报告
            report = await enhanced_generator.generate_enhanced_weekly_report(
                project_id, start_date, end_date, language
            )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": report.to_markdown()
                    }
                ]
            }
            
        except ImportError:
            # 如果增强型报告生成器不可用，回退到基本报告
            self.logger.warning("Enhanced report generator not available, falling back to basic report")
            return await self._generate_weekly_report(arguments)
        except Exception as e:
            self.logger.error(f"Enhanced weekly report generation failed: {e}")
            raise
    
    async def _generate_enhanced_monthly_report(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """生成增强型月报"""
        project_id = arguments.get("project_id")
        year = arguments.get("year")
        month = arguments.get("month")
        language_str = arguments.get("language", "ja")
        
        if not all([project_id, year, month]):
            raise InvalidParams("Missing required parameters: project_id, year, month")
        
        # 导入增强型报告生成器
        try:
            from app.services.enhanced_report_generator import EnhancedReportGeneratorService, ReportLanguage
            
            # 创建增强型报告生成器实例
            enhanced_generator = EnhancedReportGeneratorService(self.client)
            
            # 解析语言参数
            language_map = {
                "zh": ReportLanguage.CHINESE,
                "ja": ReportLanguage.JAPANESE,
                "en": ReportLanguage.ENGLISH
            }
            language = language_map.get(language_str.lower(), ReportLanguage.JAPANESE)
            
            # 生成增强型报告
            report = await enhanced_generator.generate_enhanced_monthly_report(
                project_id, year, month, language
            )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": report.to_markdown()
                    }
                ]
            }
            
        except ImportError:
            # 如果增强型报告生成器不可用，回退到基本报告
            self.logger.warning("Enhanced report generator not available, falling back to basic report")
            return await self._generate_monthly_report(arguments)
        except Exception as e:
            self.logger.error(f"Enhanced monthly report generation failed: {e}")
            raise
