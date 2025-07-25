"""
报告领域模型
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class ReportSection(BaseModel):
    """报告章节"""
    
    title: str = Field(..., description="章节标题")
    content: str = Field(..., description="章节内容")
    order: Optional[int] = Field(None, description="章节顺序")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('章节标题不能为空')
        return v.strip()
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('章节内容不能为空')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "title": "项目概览",
                "content": "本周项目进展顺利，完成了3个主要功能模块的开发。",
                "order": 1
            }
        }


class Report(BaseModel):
    """报告实体"""
    
    title: str = Field(..., description="报告标题")
    project_name: str = Field(..., description="项目名称")
    period: str = Field(..., description="报告周期")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成时间")
    summary: str = Field(..., description="报告摘要")
    sections: List[ReportSection] = Field(default_factory=list, description="报告章节")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计数据")
    template_id: Optional[str] = Field(None, description="使用的模板ID")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('报告标题不能为空')
        return v.strip()
    
    @validator('project_name')
    def project_name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('项目名称不能为空')
        return v.strip()
    
    @validator('summary')
    def summary_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('报告摘要不能为空')
        return v.strip()
    
    def add_section(self, title: str, content: str, order: Optional[int] = None) -> None:
        """添加报告章节"""
        if order is None:
            order = len(self.sections) + 1
        
        section = ReportSection(title=title, content=content, order=order)
        self.sections.append(section)
        
        # 按顺序排序
        self.sections.sort(key=lambda x: x.order or 999)
    
    def get_section_by_title(self, title: str) -> Optional[ReportSection]:
        """根据标题获取章节"""
        for section in self.sections:
            if section.title == title:
                return section
        return None
    
    def get_total_sections(self) -> int:
        """获取章节总数"""
        return len(self.sections)
    
    def get_word_count(self) -> int:
        """获取报告字数（估算）"""
        total_words = len(self.title.split()) + len(self.summary.split())
        for section in self.sections:
            total_words += len(section.title.split()) + len(section.content.split())
        return total_words
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"# {self.title}",
            "",
            f"**项目**: {self.project_name}",
            f"**周期**: {self.period}",
            f"**生成时间**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"## 概述",
            self.summary,
            ""
        ]
        
        # 添加章节
        for section in sorted(self.sections, key=lambda x: x.order or 999):
            lines.extend([
                f"## {section.title}",
                section.content,
                ""
            ])
        
        # 添加统计数据
        if self.statistics:
            lines.extend([
                "## 统计数据",
                ""
            ])
            for key, value in self.statistics.items():
                if isinstance(value, dict):
                    lines.append(f"**{key}**:")
                    for sub_key, sub_value in value.items():
                        lines.append(f"- {sub_key}: {sub_value}")
                else:
                    lines.append(f"- {key}: {value}")
            lines.append("")
        
        return "\n".join(lines)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "title": "示例项目周报",
                "project_name": "示例项目",
                "period": "2025-01-20 至 2025-01-26",
                "summary": "本周项目进展顺利，完成了主要功能开发。",
                "sections": [
                    {
                        "title": "完成的工作",
                        "content": "1. 完成用户登录功能\n2. 实现数据导出功能",
                        "order": 1
                    }
                ],
                "statistics": {
                    "total_work_packages": 10,
                    "completed_work_packages": 7
                }
            }
        }
