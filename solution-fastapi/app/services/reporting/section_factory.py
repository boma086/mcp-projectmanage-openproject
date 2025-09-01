"""
报告章节工厂 - 使用工厂模式创建报告章节
"""
from typing import Dict, Any, List, Optional
from datetime import datetime

from mcp_core.domain.models import ReportSection, WorkPackage
from app.i18n.translation_service import translation_service


class ReportSectionFactory:
    """报告章节工厂"""
    
    def __init__(self):
        self.section_builders = {
            "basic_info": self._build_basic_info_section,
            "work_packages": self._build_work_packages_section,
            "statistics": self._build_statistics_section,
            "agile_metrics": self._build_agile_metrics_section,
            "quality_metrics": self._build_quality_metrics_section,
            "team_analytics": self._build_team_analytics_section,
            "risk_analysis": self._build_risk_analysis_section,
            "compliance_check": self._build_compliance_section,
            "visualizations": self._build_visualizations_section
        }
    
    async def create_section(self, section_type: str, data: Dict[str, Any], 
                           locale: str, order: int) -> ReportSection:
        """创建指定类型的章节"""
        builder = self.section_builders.get(section_type)
        if not builder:
            raise ValueError(f"Unknown section type: {section_type}")
        
        content = await builder(data, locale)
        title = translation_service.translate(section_type, locale)
        
        return ReportSection(title=title, content=content, order=order)
    
    async def _build_basic_info_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建基本信息章节"""
        context = {
            "project": translation_service.translate("project", locale),
            "period": translation_service.translate("period", locale),
            "generated_at": translation_service.translate("generated_at", locale),
            "project_name": data.get("project_name", ""),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        template = translation_service.translate("basic_info_section", locale, context=context)
        return template
    
    async def _build_work_packages_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建工作包章节"""
        work_packages: List[WorkPackage] = data.get("work_packages", [])
        
        # 按状态分组
        status_groups = {}
        for wp in work_packages:
            status = wp.status or "Unknown"
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(wp)
        
        content = f"**{translation_service.translate('work_packages', locale)}**: {len(work_packages)}\n\n"
        
        for status, wps in status_groups.items():
            content += f"### {status} ({len(wps)})\n\n"
            for wp in wps:
                content += f"- **{wp.subject}** (ID: {wp.id})\n"
                if wp.assigned_to:
                    content += f"  - {translation_service.translate('assignee', locale)}: {wp.assigned_to}\n"
                if wp.progress is not None:
                    content += f"  - {translation_service.translate('progress', locale)}: {wp.progress}%\n"
                if wp.description:
                    desc_summary = wp.description[:100] + "..." if len(wp.description) > 100 else wp.description
                    content += f"  - {translation_service.translate('description', locale)}: {desc_summary}\n"
                content += "\n"
        
        return content
    
    async def _build_statistics_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建统计数据章节"""
        all_wps = data.get("all_work_packages", [])
        updated_wps = data.get("updated_work_packages", [])
        
        # 状态分布统计
        status_stats = {}
        for wp in all_wps:
            status = wp.status or "Unknown"
            status_stats[status] = status_stats.get(status, 0) + 1
        
        content = f"**{translation_service.translate('total_work_packages', locale)}**: {len(all_wps)}\n"
        content += f"**{translation_service.translate('updated_work_packages', locale)}**: {len(updated_wps)}\n\n"
        
        content += f"**{translation_service.translate('status_distribution', locale)}**:\n"
        for status, count in status_stats.items():
            percentage = (count / len(all_wps) * 100) if len(all_wps) > 0 else 0
            content += f"- {status}: {count} ({translation_service.format_percentage(percentage, locale)})\n"
        
        return content
    
    async def _build_agile_metrics_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建敏捷指标章节"""
        metrics = data.get("agile_metrics", {})
        
        content = f"**{translation_service.translate('velocity', locale)}**: {metrics.get('velocity', 0)}\n"
        content += f"**{translation_service.translate('completion_rate', locale)}**: {translation_service.format_percentage(metrics.get('completion_rate', 0), locale)}\n"
        content += f"**{translation_service.translate('work_in_progress', locale)}**: {metrics.get('work_in_progress', 0)}\n"
        content += f"**{translation_service.translate('throughput', locale)}**: {metrics.get('throughput', 0)}\n"
        
        return content
    
    async def _build_quality_metrics_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建质量指标章节"""
        metrics = data.get("quality_metrics", {})
        
        content = f"**{translation_service.translate('defect_density', locale)}**: {translation_service.format_percentage(metrics.get('defect_density', 0), locale)}\n"
        content += f"**{translation_service.translate('test_coverage', locale)}**: {translation_service.format_percentage(metrics.get('test_coverage', 0), locale)}\n"
        content += f"**{translation_service.translate('code_review_rate', locale)}**: {translation_service.format_percentage(metrics.get('code_review_rate', 0), locale)}\n"
        content += f"**{translation_service.translate('pr_merge_time', locale)}**: {metrics.get('pr_merge_time', 0)} hours\n"
        
        return content
    
    async def _build_team_analytics_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建团队分析章节"""
        analytics = data.get("team_analytics", {})
        workload = analytics.get("team_member_workload", {})
        
        content = f"**{translation_service.translate('team_members', locale)}**: {len(workload)}\n\n"
        
        if workload:
            content += f"**{translation_service.translate('work_distribution', locale)}**:\n"
            for member, count in workload.items():
                content += f"- {member}: {count} {translation_service.translate('work_packages', locale, count=count)}\n"
        
        return content
    
    async def _build_risk_analysis_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建风险分析章节"""
        risks = data.get("risk_analysis", {})
        
        content = f"**{translation_service.translate('delay_risk', locale)}**: {risks.get('delay_risk', 'Low')}\n"
        content += f"**{translation_service.translate('overdue_work_packages', locale)}**: {risks.get('overdue_work_packages', 0)}\n"
        content += f"**{translation_service.translate('resource_bottlenecks', locale)}**: {risks.get('resource_bottlenecks', 0)}\n"
        content += f"**{translation_service.translate('dependency_risks', locale)}**: {risks.get('dependency_risks', 0)}\n"
        
        return content
    
    async def _build_compliance_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建合规性检查章节"""
        compliance = data.get("compliance_check", {})
        
        content = f"**{translation_service.translate('security_standards', locale)}**: {translation_service.format_percentage(compliance.get('security_standards_compliance', 0), locale)}\n"
        content += f"**{translation_service.translate('coding_standards', locale)}**: {translation_service.format_percentage(compliance.get('coding_standards_compliance', 0), locale)}\n"
        content += f"**{translation_service.translate('documentation_completeness', locale)}**: {translation_service.format_percentage(compliance.get('documentation_completeness', 0), locale)}\n"
        content += f"**{translation_service.translate('missing_documentation', locale)}**: {compliance.get('work_packages_missing_docs', 0)}\n"
        
        return content
    
    async def _build_visualizations_section(self, data: Dict[str, Any], locale: str) -> str:
        """构建可视化章节"""
        content = f"**{translation_service.translate('charts_available', locale)}**:\n"
        content += f"- {translation_service.translate('burndown_chart', locale)}\n"
        content += f"- {translation_service.translate('status_pie_chart', locale)}\n"
        content += f"- {translation_service.translate('progress_trend_chart', locale)}\n"
        content += f"- {translation_service.translate('team_velocity_chart', locale)}\n"
        
        # 添加图表数据
        content += f"\n**{translation_service.translate('chart_data', locale)}**:\n"
        for key, value in data.get("all_metrics", {}).items():
            if isinstance(value, (int, float, str)):
                content += f"- {key}: {value}\n"
        
        return content