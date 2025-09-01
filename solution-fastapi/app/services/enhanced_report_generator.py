"""
增强型报告生成服务
支持多语言、敏捷指标、质量指标、团队分析等功能
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import asyncio

from mcp_core.domain.models import Project, WorkPackage, User, Report, ReportSection
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import NotFoundError

from app.i18n.translation_service import TranslationService
from app.services.reporting.metrics_calculator import MetricsCalculator
from app.services.reporting.section_factory import ReportSectionFactory
from app.services.reporting.report_context import ReportContext


class ReportLanguage(Enum):
    """报告语言选项"""
    CHINESE = "zh"
    JAPANESE = "ja"
    ENGLISH = "en"


class EnhancedReportGeneratorService:
    """增强型报告生成服务"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
        self.translation_service = TranslationService()
        self.metrics_calculator = MetricsCalculator()
        self.section_factory = ReportSectionFactory()
    
    async def generate_enhanced_weekly_report(self, project_id: str, 
                                            start_date: str, end_date: str,
                                            language: ReportLanguage = ReportLanguage.JAPANESE) -> Report:
        """生成增强型周报"""
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # 获取项目工作包
        work_packages = await self.client.get_work_packages(project_id)
        
        # 过滤指定日期范围内更新的工作包
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        filtered_wps = [wp for wp in work_packages 
                       if wp.updated_at and start_dt <= wp.updated_at <= end_dt]
        
        # 并行计算所有指标
        all_metrics = await self.metrics_calculator.calculate_all_metrics(work_packages, filtered_wps)
        
        # 创建报告上下文
        report_context = ReportContext(
            project=project,
            project_id=project_id,
            start_date=start_date,
            end_date=end_date,
            all_work_packages=work_packages,
            updated_work_packages=filtered_wps,
            all_metrics=all_metrics
        )
        
        # 使用工厂模式创建所有报告章节
        sections = []
        section_types = [
            "basic_info", "work_packages", "statistics", "agile_metrics",
            "quality_metrics", "team_analytics", "risk_analysis", 
            "compliance_check", "visualizations"
        ]
        
        for order, section_type in enumerate(section_types, 1):
            section_data = {
                "project_name": project.name,
                "start_date": start_date,
                "end_date": end_date,
                "work_packages": filtered_wps,
                "all_work_packages": work_packages,
                "updated_work_packages": filtered_wps,
                "agile_metrics": all_metrics.get("agile_metrics", {}),
                "quality_metrics": all_metrics.get("quality_metrics", {}),
                "team_analytics": all_metrics.get("team_analytics", {}),
                "risk_analysis": all_metrics.get("risk_analysis", {}),
                "compliance_check": all_metrics.get("compliance_check", {}),
                "all_metrics": all_metrics
            }
            
            section = await self.section_factory.create_section(
                section_type, section_data, language.value, order
            )
            sections.append(section)
        
        # 创建报告
        title = f"{project.name} {self.translation_service.translate('weekly_report', language.value)}: {start_date} - {end_date}"
        summary = await self._generate_summary(project, filtered_wps, all_metrics, language, is_monthly=False)
        
        return Report(
            title=title,
            project_name=project.name,
            period=f"{start_date} {self.translation_service.translate('to', language.value)} {end_date}",
            summary=summary,
            sections=sections,
            statistics=all_metrics
        )
    
    
    async def _generate_summary(self, project: Project, updated_wps: List[WorkPackage],
                              all_metrics: Dict[str, Any], language: ReportLanguage, 
                              is_monthly: bool = False) -> str:
        """生成报告摘要"""
        agile_metrics = all_metrics.get("agile_metrics", {})
        completion_rate = agile_metrics.get("completion_rate", 0)
        
        report_type_key = "monthly_report" if is_monthly else "weekly_report"
        template_key = "monthly_summary_template" if is_monthly else "summary_template"
        
        context = {
            "project_name": project.name,
            "report_type": self.translation_service.translate(report_type_key, language.value),
            "updated_count": len(updated_wps),
            "completion_rate": completion_rate
        }
        
        return self.translation_service.translate(template_key, language.value, context=context)

    async def generate_enhanced_monthly_report(self, project_id: str, year: int, month: int,
                                             language: ReportLanguage = ReportLanguage.JAPANESE) -> Report:
        """生成增强型月报"""
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        work_packages = await self.client.get_work_packages(project_id)
        
        # 计算月份的开始和结束日期
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        monthly_wps = [wp for wp in work_packages 
                      if wp.updated_at and start_date <= wp.updated_at <= end_date]
        
        # 并行计算所有指标
        all_metrics = await self.metrics_calculator.calculate_all_metrics(work_packages, monthly_wps)
        
        # 创建报告上下文
        report_context = ReportContext(
            project=project,
            project_id=project_id,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            all_work_packages=work_packages,
            updated_work_packages=monthly_wps,
            all_metrics=all_metrics
        )
        
        # 使用工厂模式创建所有报告章节
        sections = []
        section_types = [
            "basic_info", "work_packages", "statistics", "agile_metrics",
            "quality_metrics", "team_analytics", "risk_analysis", 
            "compliance_check", "visualizations"
        ]
        
        for order, section_type in enumerate(section_types, 1):
            section_data = {
                "project_name": project.name,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "work_packages": monthly_wps,
                "all_work_packages": work_packages,
                "updated_work_packages": monthly_wps,
                "agile_metrics": all_metrics.get("agile_metrics", {}),
                "quality_metrics": all_metrics.get("quality_metrics", {}),
                "team_analytics": all_metrics.get("team_analytics", {}),
                "risk_analysis": all_metrics.get("risk_analysis", {}),
                "compliance_check": all_metrics.get("compliance_check", {}),
                "all_metrics": all_metrics
            }
            
            section = await self.section_factory.create_section(
                section_type, section_data, language.value, order
            )
            sections.append(section)
        
        # 创建报告
        title = f"{project.name} {self.translation_service.translate('monthly_report', language.value)}: {year}-{month:02d}"
        summary = await self._generate_summary(project, monthly_wps, all_metrics, language, is_monthly=True)
        
        return Report(
            title=title,
            project_name=project.name,
            period=f"{start_date.strftime('%Y-%m-%d')} {self.translation_service.translate('to', language.value)} {end_date.strftime('%Y-%m-%d')}",
            summary=summary,
            sections=sections,
            statistics=all_metrics
        )