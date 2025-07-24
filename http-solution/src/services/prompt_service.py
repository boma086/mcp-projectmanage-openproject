"""
MCP Prompts 服务
提供提示模板管理和生成功能
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.utils.logger import mcp_logger
from src.utils.exceptions import ValidationError, OpenProjectError


class PromptService:
    """MCP提示服务管理器"""
    
    def __init__(self, openproject_adapter):
        if openproject_adapter is None:
            raise ValueError("PromptService 初始化失败：openproject_adapter 不能为空！")
        self.openproject_adapter = openproject_adapter
        self._prompts = {}
        self._register_default_prompts()
    
    def _register_default_prompts(self):
        """注册默认的提示模板"""
        self._prompts = {
            "project_analysis": {
                "name": "project_analysis",
                "description": "分析项目状态和进度的提示模板",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "要分析的项目ID",
                        "required": True
                    },
                    {
                        "name": "focus_area",
                        "description": "分析重点领域 (progress, issues, timeline, resources)",
                        "required": False
                    }
                ]
            },
            "work_package_summary": {
                "name": "work_package_summary",
                "description": "生成工作包摘要的提示模板",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "项目ID",
                        "required": False
                    },
                    {
                        "name": "status_filter",
                        "description": "按状态过滤工作包 (open, closed, in_progress)",
                        "required": False
                    },
                    {
                        "name": "priority_filter",
                        "description": "按优先级过滤 (high, normal, low)",
                        "required": False
                    }
                ]
            },
            "project_report_generator": {
                "name": "project_report_generator",
                "description": "生成项目报告的提示模板",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "项目ID",
                        "required": True
                    },
                    {
                        "name": "report_type",
                        "description": "报告类型 (summary, detailed, executive)",
                        "required": False
                    },
                    {
                        "name": "include_metrics",
                        "description": "是否包含指标数据",
                        "required": False
                    }
                ]
            },
            "task_prioritization": {
                "name": "task_prioritization",
                "description": "任务优先级排序建议的提示模板",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "项目ID",
                        "required": True
                    },
                    {
                        "name": "criteria",
                        "description": "优先级排序标准 (deadline, importance, effort, dependencies)",
                        "required": False
                    }
                ]
            },
            "project_health_check": {
                "name": "project_health_check",
                "description": "项目健康状况检查的提示模板",
                "arguments": [
                    {
                        "name": "project_id",
                        "description": "项目ID",
                        "required": True
                    },
                    {
                        "name": "check_areas",
                        "description": "检查领域 (timeline, budget, resources, quality, risks)",
                        "required": False
                    }
                ]
            }
        }
    
    def list_prompts(self) -> List[Dict[str, Any]]:
        """列出所有可用的提示模板"""
        return list(self._prompts.values())
    
    def get_prompt(self, name: str, arguments: Dict[str, Any] = None, 
                   request_id: Optional[str] = None) -> Dict[str, Any]:
        """获取指定名称的提示内容"""
        if name not in self._prompts:
            raise ValidationError(f"Unknown prompt: {name}")
        
        prompt_info = self._prompts[name]
        arguments = arguments or {}
        
        mcp_logger.logger.debug(f"生成提示: {name}", extra={
            'request_id': request_id,
            'arguments': arguments
        })
        
        # 验证必需参数
        for arg in prompt_info.get("arguments", []):
            if arg.get("required", False) and arg["name"] not in arguments:
                raise ValidationError(f"Missing required argument '{arg['name']}' for prompt '{name}'")
        
        # 生成提示内容
        prompt_generators = {
            "project_analysis": self._generate_project_analysis_prompt,
            "work_package_summary": self._generate_work_package_summary_prompt,
            "project_report_generator": self._generate_project_report_prompt,
            "task_prioritization": self._generate_task_prioritization_prompt,
            "project_health_check": self._generate_project_health_check_prompt
        }
        try:
            if name in prompt_generators:
                return prompt_generators[name](arguments, request_id)
            else:
                raise ValidationError(f"Prompt generator not implemented for: {name}")
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            else:
                mcp_logger.log_error(f"生成提示失败: {name}", e, request_id)
                raise OpenProjectError(f"Failed to generate prompt: {str(e)}")
    
    def _generate_project_analysis_prompt(self, arguments: Dict[str, Any], 
                                        request_id: Optional[str] = None) -> Dict[str, Any]:
        """生成项目分析提示"""
        project_id = arguments["project_id"]
        focus_area = arguments.get("focus_area", "general")
        
        # 获取项目数据
        if not self.openproject_adapter:
            raise OpenProjectError("OpenProject adapter not initialized")
        
        project = self.openproject_adapter.get_project(project_id, request_id)
        if not project:
            raise ValidationError(f"Project not found: {project_id}")
        
        work_packages = self.openproject_adapter.get_work_packages(project_id, request_id)
        
        # 定义状态类别
        CLOSED_STATUSES = {"closed"}
        IN_PROGRESS_STATUSES = {"in progress", "active", "open"}
        
        # 工作包统计：精确匹配状态
        closed_count = len([
            wp for wp in work_packages 
            if wp.status and wp.status.strip().lower() in CLOSED_STATUSES
        ])
        in_progress_count = len([
            wp for wp in work_packages 
            if wp.status and wp.status.strip().lower() in IN_PROGRESS_STATUSES
        ])
        system_prompt = f"""你是一个项目管理专家，正在分析OpenProject中的项目。
请基于提供的项目数据进行深入分析，重点关注{focus_area}方面。

项目信息：
- 名称：{project.name}
- 标识符：{project.identifier}
- 描述：{project.description or '无描述'}
- 状态：{project.status}

工作包统计：
- 总数：{len(work_packages)}
- 已完成：{closed_count}
- 进行中：{in_progress_count}

请提供详细的分析报告，包括：
1. 项目整体状况评估
2. 进度分析
3. 潜在问题识别
4. 改进建议
"""

        user_message = f"请分析项目 '{project.name}' (ID: {project_id}) 的当前状况。"
        if focus_area != "general":
            user_message += f" 特别关注{focus_area}方面。"

        return {
            "description": f"分析项目 {project.name} 的状况",
            "messages": [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": system_prompt
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": user_message
                    }
                }
            ]
        }
    
    def _generate_work_package_summary_prompt(self, arguments: Dict[str, Any], 
                                            request_id: Optional[str] = None) -> Dict[str, Any]:
        """生成工作包摘要提示"""
        project_id = arguments.get("project_id")
        status_filter = arguments.get("status_filter")
        priority_filter = arguments.get("priority_filter")
        
        if not self.openproject_adapter:
            raise OpenProjectError("OpenProject adapter not initialized")
        
        # 获取工作包数据
        work_packages = self.openproject_adapter.get_work_packages(project_id, request_id)
        
        # 应用过滤器
        if status_filter:
            work_packages = [
                wp for wp in work_packages
                if wp.status and wp.status.strip().lower() == status_filter.strip().lower()
            ]
        if priority_filter:
            work_packages = [
                wp for wp in work_packages
                if wp.priority and wp.priority.strip().lower() == priority_filter.strip().lower()
            ]
        
        # 构建工作包信息
        wp_info = []
        for wp in work_packages[:20]:  # 限制数量避免提示过长
            wp_info.append(f"- {wp.subject} (ID: {wp.id}, 状态: {wp.status or '未知'}, 优先级: {wp.priority or '未知'})")
        
        system_prompt = f"""你是一个项目管理助手，需要为工作包列表生成简洁的摘要。

当前工作包列表（共{len(work_packages)}个）：
{chr(10).join(wp_info)}

请生成一个结构化的摘要，包括：
1. 工作包总体概况
2. 按状态分类统计
3. 按优先级分类统计
4. 关键发现和建议
"""

        filter_desc = []
        if status_filter:
            filter_desc.append(f"状态: {status_filter}")
        if priority_filter:
            filter_desc.append(f"优先级: {priority_filter}")
        
        user_message = "请为这些工作包生成摘要报告。"
        if filter_desc:
            user_message += f" 过滤条件: {', '.join(filter_desc)}"

        return {
            "description": f"工作包摘要 ({len(work_packages)}个项目)",
            "messages": [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": system_prompt
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": user_message
                    }
                }
            ]
        }
    
    def _generate_project_report_prompt(self, arguments: Dict[str, Any], 
                                      request_id: Optional[str] = None) -> Dict[str, Any]:
        """生成项目报告提示"""
        project_id = arguments["project_id"]
        report_type = arguments.get("report_type", "summary")
        include_metrics = arguments.get("include_metrics", True)
        
        if not self.openproject_adapter:
            raise OpenProjectError("OpenProject adapter not initialized")
        
        # 获取项目报告数据
        report = self.openproject_adapter.generate_project_report(project_id, request_id)
        
        system_prompt = f"""你是一个专业的项目报告分析师，需要基于OpenProject数据生成{report_type}类型的项目报告。

项目报告数据：
标题：{report.title}
项目：{report.project_name}
期间：{report.period}
摘要：{report.summary}

详细信息：
{chr(10).join([f"{section.title}: {section.content}" for section in report.sections])}
"""

        if include_metrics and report.statistics:
            system_prompt += f"\n统计数据：\n{chr(10).join([f'{k}: {v}' for k, v in report.statistics.items()])}"

        system_prompt += f"""

请生成一个专业的{report_type}项目报告，包括：
1. 执行摘要
2. 项目状态概览
3. 关键成就和里程碑
4. 风险和问题
5. 下一步行动计划
"""

        return {
            "description": f"{report.project_name} - {report_type}报告",
            "messages": [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": system_prompt
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"请为项目 '{report.project_name}' 生成{report_type}报告。"
                    }
                }
            ]
        }
    
    def _generate_task_prioritization_prompt(self, arguments: Dict[str, Any], 
                                           request_id: Optional[str] = None) -> Dict[str, Any]:
        """生成任务优先级排序提示（需实现：应根据project_id获取项目数据并生成提示）"""
        project_id = arguments.get("project_id")
        # TODO: 实现应根据project_id获取项目数据并生成任务优先级排序提示
        raise NotImplementedError("_generate_task_prioritization_prompt 需根据 project_id 获取项目数据并生成提示。当前为占位实现。")

    def _generate_project_health_check_prompt(self, arguments: Dict[str, Any], 
                                            request_id: Optional[str] = None) -> Dict[str, Any]:
        """生成项目健康检查提示（需实现：应根据project_id获取项目数据并生成提示）"""
        project_id = arguments.get("project_id")
        # TODO: 实现应根据project_id获取项目数据并生成健康检查提示
        raise NotImplementedError("_generate_project_health_check_prompt 需根据 project_id 获取项目数据并生成提示。当前为占位实现。")
