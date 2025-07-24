"""
报告模板服务
提供模板管理和渲染功能
"""
import os
import yaml
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Template, Environment, FileSystemLoader

from src.utils.logger import mcp_logger
from src.utils.exceptions import ValidationError


class TemplateService:
    """报告模板服务"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent.parent.parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
        
        # 初始化Jinja2环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        
        mcp_logger.logger.info("模板服务初始化完成")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板列表"""
        try:
            templates = []
            
            for template_file in self.templates_dir.glob("*.yaml"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = yaml.safe_load(f)
                    
                    template_info = template_data.get('template_info', {})
                    templates.append({
                        "template_id": template_file.stem,
                        "name": template_info.get('name', template_file.stem),
                        "type": template_info.get('type', 'unknown'),
                        "description": template_info.get('description', ''),
                        "version": template_info.get('version', '1.0'),
                        "created_by": template_info.get('created_by', 'system'),
                        "file_path": str(template_file)
                    })
                    
                except Exception as e:
                    mcp_logger.logger.warning(f"读取模板文件失败: {template_file} - {e}")
                    continue
            
            mcp_logger.logger.info(f"获取到 {len(templates)} 个模板")
            return templates
            
        except Exception as e:
            mcp_logger.log_error("获取模板列表失败", e)
            raise
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """获取指定模板"""
        try:
            template_file = self.templates_dir / f"{template_id}.yaml"
            
            if not template_file.exists():
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = yaml.safe_load(f)
            
            mcp_logger.logger.info(f"获取模板成功: {template_id}")
            return template_data
            
        except Exception as e:
            mcp_logger.log_error(f"获取模板失败: {template_id}", e)
            raise
    
    def save_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """保存模板"""
        try:
            # 验证模板数据
            self._validate_template_data(template_data)
            
            template_file = self.templates_dir / f"{template_id}.yaml"
            
            # 添加更新时间
            if 'template_info' not in template_data:
                template_data['template_info'] = {}
            
            template_data['template_info']['updated_at'] = datetime.now().isoformat()
            
            with open(template_file, 'w', encoding='utf-8') as f:
                yaml.dump(template_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            mcp_logger.logger.info(f"保存模板成功: {template_id}")
            return True
            
        except Exception as e:
            mcp_logger.log_error(f"保存模板失败: {template_id}", e)
            raise
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        try:
            template_file = self.templates_dir / f"{template_id}.yaml"
            
            if not template_file.exists():
                return False
            
            template_file.unlink()
            mcp_logger.logger.info(f"删除模板成功: {template_id}")
            return True
            
        except Exception as e:
            mcp_logger.log_error(f"删除模板失败: {template_id}", e)
            raise
    
    def render_template(self, template_id: str, data: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            template_data = self.get_template(template_id)
            if not template_data:
                raise ValueError(f"模板不存在: {template_id}")

            # 确保数据中有默认值
            default_data = {
                'project_name': '未知项目',
                'start_date': '2025-01-01',
                'end_date': '2025-01-07',
                'completion_rate': 0,
                'total_work_packages': 0,
                'completed_work_packages': 0,
                'in_progress_work_packages': 0
            }
            default_data.update(data)

            # 渲染标题
            title_template = template_data.get('title_template', '{{project_name}} 报告')
            try:
                title = Template(title_template).render(**default_data)
            except Exception as e:
                mcp_logger.logger.warning(f"标题渲染失败: {e}")
                title = f"{default_data.get('project_name', '未知项目')} 报告"

            # 渲染各个章节
            sections = template_data.get('sections', [])
            rendered_sections = []

            for section in sorted(sections, key=lambda x: x.get('order', 999)):
                if section.get('required', True) or self._should_include_section(section, data):
                    content_template = section.get('content_template', '')
                    try:
                        rendered_content = Template(content_template).render(**default_data)
                        rendered_sections.append({
                            'name': section.get('section_name', ''),
                            'content': rendered_content
                        })
                    except Exception as e:
                        mcp_logger.logger.warning(f"章节 {section.get('section_name')} 渲染失败: {e}")
                        rendered_sections.append({
                            'name': section.get('section_name', ''),
                            'content': f"[渲染错误: {str(e)}]"
                        })

            # 组合最终报告
            report_content = f"# {title}\n\n"
            for section in rendered_sections:
                report_content += f"{section['content']}\n\n"

            mcp_logger.logger.info(f"模板渲染成功: {template_id}")
            return report_content

        except Exception as e:
            mcp_logger.log_error(f"模板渲染失败: {template_id}", e)
            return f"模板渲染失败: {str(e)}"
    
    def get_template_variables(self, template_id: str) -> List[Dict[str, Any]]:
        """获取模板中使用的变量"""
        try:
            template_data = self.get_template(template_id)
            if not template_data:
                return []
            
            variables = []
            data_sources = template_data.get('data_sources', [])
            
            for source in data_sources:
                for field in source.get('fields', []):
                    variables.append({
                        'name': field,
                        'source': source.get('name'),
                        'description': source.get('description', '')
                    })
            
            # 添加可编辑字段
            editable_fields = template_data.get('editable_fields', [])
            for field in editable_fields:
                variables.append({
                    'name': field.get('field_name'),
                    'type': field.get('field_type'),
                    'label': field.get('field_label'),
                    'editable': True
                })
            
            return variables
            
        except Exception as e:
            mcp_logger.log_error(f"获取模板变量失败: {template_id}", e)
            raise
    
    def _validate_template_data(self, template_data: Dict[str, Any]) -> None:
        """验证模板数据格式"""
        required_fields = ['template_info', 'title_template', 'sections']
        
        for field in required_fields:
            if field not in template_data:
                raise ValidationError(f"模板缺少必需字段: {field}")
        
        # 验证章节格式
        sections = template_data.get('sections', [])
        if not isinstance(sections, list):
            raise ValidationError("sections必须是列表格式")
        
        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                raise ValidationError(f"第{i+1}个章节格式错误")
            
            if 'section_id' not in section:
                raise ValidationError(f"第{i+1}个章节缺少section_id")
    
    def _should_include_section(self, section: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """判断是否应该包含某个章节"""
        # 这里可以添加更复杂的逻辑来决定是否包含某个章节
        # 例如：根据数据内容、用户权限等
        return True
    
    def create_default_templates(self) -> None:
        """创建默认模板"""
        try:
            # 检查是否已有模板
            existing_templates = self.list_templates()
            if existing_templates:
                mcp_logger.logger.info("已存在模板，跳过创建默认模板")
                return
            
            # 创建默认周报模板
            weekly_template = {
                "template_info": {
                    "name": "标准周报模板",
                    "type": "weekly",
                    "description": "团队周报标准格式",
                    "created_by": "system",
                    "version": "1.0"
                },
                "title_template": "{{project_name}} 周报 ({{start_date}} - {{end_date}})",
                "sections": [
                    {
                        "section_id": "overview",
                        "section_name": "项目概览",
                        "order": 1,
                        "required": True,
                        "content_template": "## 项目概览\n\n**项目**: {{project_name}}\n**周期**: {{start_date}} - {{end_date}}\n**完成率**: {{completion_rate}}%"
                    }
                ],
                "data_sources": [
                    {
                        "name": "project_basic",
                        "description": "项目基础信息",
                        "fields": ["project_name", "start_date", "end_date", "completion_rate"]
                    }
                ]
            }
            
            self.save_template("default_weekly", weekly_template)
            mcp_logger.logger.info("创建默认模板成功")
            
        except Exception as e:
            mcp_logger.log_error("创建默认模板失败", e)
