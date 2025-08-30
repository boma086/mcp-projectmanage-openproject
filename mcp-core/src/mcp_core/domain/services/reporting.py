"""
报告引擎服务 - 支持多语言报告生成和指标计算
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import json
import yaml
import jinja2
from pathlib import Path

from mcp_core.domain.models import Project, WorkPackage, Report, ReportSection
from mcp_core.domain.interfaces import IOpenProjectClient, ITemplateEngine
from mcp_core.shared.exceptions import NotFoundError, ValidationError
from mcp_core.shared.logger import get_logger


class ReportLanguage(str, Enum):
    """支持的报告语言"""
    CHINESE = "zh"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"


class ReportFormat(str, Enum):
    """支持的报告格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PLAIN_TEXT = "plain"


class ReportType(str, Enum):
    """报告类型"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    DAILY = "daily"
    PROGRESS = "progress"
    CUSTOM = "custom"


class ReportingService:
    """报告引擎服务 - 支持多语言报告生成和指标计算"""
    
    def __init__(self, openproject_client: IOpenProjectClient, template_engine: ITemplateEngine):
        self.client = openproject_client
        self.template_engine = template_engine
        self.logger = get_logger(__name__)
        self._jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                Path(__file__).parent.parent.parent.parent / "templates"
            ),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            extensions=['jinja2.ext.i18n']
        )
        
        # 多语言支持
        self._translations = self._load_translations()
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """加载多语言翻译"""
        translations = {
            "zh": {
                "weekly_report": "周报",
                "monthly_report": "月报", 
                "daily_report": "日报",
                "progress_report": "进度报告",
                "overview": "项目概览",
                "progress": "进度统计",
                "achievements": "本周成果",
                "issues": "问题与风险",
                "next_week": "下周计划",
                "team_status": "团队状态",
                "metrics": "关键指标",
                "next_focus": "下周关注点",
                "project": "项目",
                "period": "周期",
                "generated_at": "生成时间",
                "total_work_packages": "总工作包数",
                "completed_work_packages": "已完成工作包",
                "in_progress_work_packages": "进行中工作包",
                "completion_rate": "完成率",
                "weekly_new": "本周新增",
                "weekly_completed": "本周完成",
                "team_members": "团队成员",
                "workload_per_person": "人均工作负载",
                "team_morale": "团队士气",
                "collaboration_efficiency": "协作效率",
                "support_needed": "需要的支持"
            },
            "en": {
                "weekly_report": "Weekly Report",
                "monthly_report": "Monthly Report",
                "daily_report": "Daily Report", 
                "progress_report": "Progress Report",
                "overview": "Overview",
                "progress": "Progress Statistics",
                "achievements": "This Week's Achievements",
                "issues": "Issues and Risks",
                "next_week": "Next Week Plan",
                "team_status": "Team Status",
                "metrics": "Key Metrics",
                "next_focus": "Next Week Focus",
                "project": "Project",
                "period": "Period",
                "generated_at": "Generated At",
                "total_work_packages": "Total Work Packages",
                "completed_work_packages": "Completed Work Packages",
                "in_progress_work_packages": "In Progress Work Packages",
                "completion_rate": "Completion Rate",
                "weekly_new": "Weekly New",
                "weekly_completed": "Weekly Completed",
                "team_members": "Team Members",
                "workload_per_person": "Workload Per Person",
                "team_morale": "Team Morale",
                "collaboration_efficiency": "Collaboration Efficiency",
                "support_needed": "Support Needed"
            },
            "ja": {
                "weekly_report": "週次レポート",
                "monthly_report": "月次レポート",
                "daily_report": "日次レポート",
                "progress_report": "進捗レポート",
                "overview": "プロジェクト概要",
                "progress": "進捗統計",
                "achievements": "今週の成果",
                "issues": "問題とリスク",
                "next_week": "来週の計画",
                "team_status": "チーム状況",
                "metrics": "主要指標",
                "next_focus": "来週の焦点",
                "project": "プロジェクト",
                "period": "期間",
                "generated_at": "生成時間",
                "total_work_packages": "総作業パッケージ数",
                "completed_work_packages": "完了作業パッケージ",
                "in_progress_work_packages": "進行中作業パッケージ",
                "completion_rate": "完了率",
                "weekly_new": "今週新規",
                "weekly_completed": "今週完了",
                "team_members": "チームメンバー",
                "workload_per_person": "一人当たりの作業負荷",
                "team_morale": "チーム士気",
                "collaboration_efficiency": "協業効率",
                "support_needed": "必要なサポート"
            },
            "ko": {
                "weekly_report": "주간 보고서",
                "monthly_report": "월간 보고서", 
                "daily_report": "일일 보고서",
                "progress_report": "진행 보고서",
                "overview": "프로젝트 개요",
                "progress": "진행 통계",
                "achievements": "이번 주 성과",
                "issues": "문제와 위험",
                "next_week": "다음 주 계획",
                "team_status": "팀 상태",
                "metrics": "주요 지표",
                "next_focus": "다음 주 중점",
                "project": "프로젝트",
                "period": "기간",
                "generated_at": "생성 시간",
                "total_work_packages": "총 작업 패키지 수",
                "completed_work_packages": "완료된 작업 패키지",
                "in_progress_work_packages": "진행 중 작업 패키지",
                "completion_rate": "완료율",
                "weekly_new": "주간 신규",
                "weekly_completed": "주간 완료",
                "team_members": "팀 멤버",
                "workload_per_person": "인당 작업 부하",
                "team_morale": "팀 사기",
                "collaboration_efficiency": "협업 효율",
                "support_needed": "필요한 지원"
            }
        }
        return translations
    
    def translate(self, key: str, language: ReportLanguage = ReportLanguage.CHINESE) -> str:
        """翻译文本"""
        lang_dict = self._translations.get(language.value, self._translations["zh"])
        return lang_dict.get(key, key)
    
    async def generate_report(
        self,
        project_id: str,
        report_type: ReportType,
        language: ReportLanguage = ReportLanguage.CHINESE,
        format: ReportFormat = ReportFormat.MARKDOWN,
        template_id: Optional[str] = None,
        **kwargs
    ) -> Report:
        """
        生成报告 - 支持多语言和多格式
        
        Args:
            project_id: 项目ID
            report_type: 报告类型
            language: 报告语言
            format: 输出格式
            template_id: 模板ID（可选）
            **kwargs: 额外参数
            
        Returns:
            Report: 生成的报告对象
        """
        self.logger.info(f"Generating {language.value} {report_type.value} report for project {project_id}")
        
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")
        
        # 获取工作包数据
        work_packages = await self.client.get_work_packages(project_id)
        
        # 计算指标
        metrics = await self._calculate_metrics(work_packages, report_type, **kwargs)
        
        # 根据报告类型生成报告
        if report_type == ReportType.WEEKLY:
            report = await self._generate_weekly_report(project, work_packages, metrics, language, **kwargs)
        elif report_type == ReportType.MONTHLY:
            report = await self._generate_monthly_report(project, work_packages, metrics, language, **kwargs)
        elif report_type == ReportType.DAILY:
            report = await self._generate_daily_report(project, work_packages, metrics, language, **kwargs)
        elif report_type == ReportType.PROGRESS:
            report = await self._generate_progress_report(project, work_packages, metrics, language, **kwargs)
        else:
            report = await self._generate_custom_report(project, work_packages, metrics, language, template_id, **kwargs)
        
        # 转换格式
        if format != ReportFormat.MARKDOWN:
            report = await self._convert_format(report, format)
        
        return report
    
    async def _calculate_metrics(
        self, 
        work_packages: List[WorkPackage], 
        report_type: ReportType,
        **kwargs
    ) -> Dict[str, Any]:
        """计算项目指标"""
        metrics = {
            "total_work_packages": len(work_packages),
            "completed_work_packages": len([wp for wp in work_packages if wp.status == 'Closed']),
            "in_progress_work_packages": len([wp for wp in work_packages if wp.status == 'In progress']),
            "not_started_work_packages": len([wp for wp in work_packages if wp.status == 'New']),
            "blocked_work_packages": len([wp for wp in work_packages if wp.status == 'Blocked']),
        }
        
        # 计算完成率
        metrics["completion_rate"] = round(
            (metrics["completed_work_packages"] / metrics["total_work_packages"] * 100) 
            if metrics["total_work_packages"] > 0 else 0, 1
        )
        
        # 计算进度率（完成+进行中）
        metrics["progress_rate"] = round(
            ((metrics["completed_work_packages"] + metrics["in_progress_work_packages"]) / 
             metrics["total_work_packages"] * 100) 
            if metrics["total_work_packages"] > 0 else 0, 1
        )
        
        # 计算平均进度（如果工作包有进度字段）
        progress_values = [wp.progress for wp in work_packages if wp.progress is not None]
        metrics["average_progress"] = round(sum(progress_values) / len(progress_values), 1) if progress_values else 0
        
        # 时间相关的指标
        now = datetime.now()
        
        if report_type == ReportType.WEEKLY:
            # 本周新增和完成的工作包
            week_start = now - timedelta(days=now.weekday())
            metrics["weekly_new_work_packages"] = len([
                wp for wp in work_packages 
                if wp.created_at and wp.created_at >= week_start
            ])
            metrics["weekly_completed_work_packages"] = len([
                wp for wp in work_packages 
                if wp.status == 'Closed' and wp.updated_at and wp.updated_at >= week_start
            ])
            
        elif report_type == ReportType.MONTHLY:
            # 本月新增和完成的工作包
            month_start = datetime(now.year, now.month, 1)
            metrics["monthly_new_work_packages"] = len([
                wp for wp in work_packages 
                if wp.created_at and wp.created_at >= month_start
            ])
            metrics["monthly_completed_work_packages"] = len([
                wp for wp in work_packages 
                if wp.status == 'Closed' and wp.updated_at and wp.updated_at >= month_start
            ])
        
        # 风险指标
        metrics["risk_score"] = self._calculate_risk_score(metrics)
        metrics["health_status"] = self._get_health_status(metrics["completion_rate"])
        
        return metrics
    
    def _calculate_risk_score(self, metrics: Dict[str, Any]) -> int:
        """计算风险分数 (0-100, 越高风险越大)"""
        risk_score = 0
        
        # 完成率低的风险
        if metrics["completion_rate"] < 30:
            risk_score += 40
        elif metrics["completion_rate"] < 60:
            risk_score += 20
        
        # 阻塞工作包多的风险
        blocked_ratio = metrics["blocked_work_packages"] / metrics["total_work_packages"] if metrics["total_work_packages"] > 0 else 0
        if blocked_ratio > 0.2:
            risk_score += 30
        elif blocked_ratio > 0.1:
            risk_score += 15
        
        # 未开始工作包多的风险
        not_started_ratio = metrics["not_started_work_packages"] / metrics["total_work_packages"] if metrics["total_work_packages"] > 0 else 0
        if not_started_ratio > 0.5:
            risk_score += 30
        elif not_started_ratio > 0.3:
            risk_score += 15
        
        return min(risk_score, 100)
    
    def _get_health_status(self, completion_rate: float) -> str:
        """根据完成率获取健康状态"""
        if completion_rate >= 80:
            return "excellent"
        elif completion_rate >= 60:
            return "good"
        elif completion_rate >= 40:
            return "fair"
        else:
            return "poor"
    
    async def _generate_weekly_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        **kwargs
    ) -> Report:
        """生成周报"""
        start_date = kwargs.get('start_date', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date = kwargs.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        # 使用模板或默认生成
        template_id = kwargs.get('template_id', f"weekly_{language.value}")
        try:
            return await self._generate_from_template(
                template_id, project, metrics, language, start_date=start_date, end_date=end_date
            )
        except Exception:
            # 模板失败时使用默认生成
            return await self._generate_default_weekly_report(project, work_packages, metrics, language, start_date, end_date)
    
    async def _generate_default_weekly_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        start_date: str,
        end_date: str
    ) -> Report:
        """生成默认周报"""
        title = f"{project.name} {self.translate('weekly_report', language)}: {start_date} - {end_date}"
        
        sections = []
        
        # 概览部分
        overview_content = f"**{self.translate('project', language)}**: {project.name}\n"
        overview_content += f"**{self.translate('period', language)}**: {start_date} - {end_date}\n"
        overview_content += f"**{self.translate('total_work_packages', language)}**: {metrics['total_work_packages']}\n"
        overview_content += f"**{self.translate('completion_rate', language)}**: {metrics['completion_rate']}%\n"
        
        sections.append(ReportSection(
            title=self.translate('overview', language),
            content=overview_content,
            order=1
        ))
        
        # 进度部分
        progress_content = f"| {self.translate('total_work_packages', language)} | {self.translate('completed_work_packages', language)} | {self.translate('in_progress_work_packages', language)} | {self.translate('completion_rate', language)} |\n"
        progress_content += "|------|------|------|------|\n"
        progress_content += f"| {metrics['total_work_packages']} | {metrics['completed_work_packages']} | {metrics['in_progress_work_packages']} | {metrics['completion_rate']}% |\n"
        
        sections.append(ReportSection(
            title=self.translate('progress', language),
            content=progress_content,
            order=2
        ))
        
        # 本周活动
        weekly_activity = f"**{self.translate('weekly_new', language)}**: {metrics.get('weekly_new_work_packages', 0)}\n"
        weekly_activity += f"**{self.translate('weekly_completed', language)}**: {metrics.get('weekly_completed_work_packages', 0)}\n"
        
        sections.append(ReportSection(
            title=self.translate('achievements', language),
            content=weekly_activity,
            order=3
        ))
        
        summary = f"{self.translate('weekly_report', language)} for {project.name} from {start_date} to {end_date}"
        
        return Report(
            title=title,
            project_name=project.name,
            period=f"{start_date} - {end_date}",
            summary=summary,
            sections=sections,
            statistics=metrics
        )
    
    async def _generate_monthly_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        **kwargs
    ) -> Report:
        """生成月报"""
        # 实现类似周报的逻辑
        year = kwargs.get('year', datetime.now().year)
        month = kwargs.get('month', datetime.now().month)
        
        template_id = kwargs.get('template_id', f"monthly_{language.value}")
        try:
            return await self._generate_from_template(
                template_id, project, metrics, language, year=year, month=month
            )
        except Exception:
            return await self._generate_default_monthly_report(project, work_packages, metrics, language, year, month)
    
    async def _generate_default_monthly_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        year: int,
        month: int
    ) -> Report:
        """生成默认月报"""
        # 简化的月报实现
        title = f"{project.name} {self.translate('monthly_report', language)}: {year}-{month:02d}"
        
        sections = [
            ReportSection(
                title=self.translate('overview', language),
                content=f"Monthly report for {project.name} in {year}-{month:02d}",
                order=1
            )
        ]
        
        return Report(
            title=title,
            project_name=project.name,
            period=f"{year}-{month:02d}",
            summary=f"Monthly summary for {project.name}",
            sections=sections,
            statistics=metrics
        )
    
    async def _generate_daily_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        **kwargs
    ) -> Report:
        """生成日报"""
        # 简化的日报实现
        date = kwargs.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        title = f"{project.name} {self.translate('daily_report', language)}: {date}"
        
        sections = [
            ReportSection(
                title=self.translate('overview', language),
                content=f"Daily report for {project.name} on {date}",
                order=1
            )
        ]
        
        return Report(
            title=title,
            project_name=project.name,
            period=date,
            summary=f"Daily summary for {project.name}",
            sections=sections,
            statistics=metrics
        )
    
    async def _generate_progress_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        **kwargs
    ) -> Report:
        """生成进度报告"""
        # 简化的进度报告实现
        title = f"{project.name} {self.translate('progress_report', language)}"
        
        sections = [
            ReportSection(
                title=self.translate('progress', language),
                content=f"Progress report for {project.name}",
                order=1
            )
        ]
        
        return Report(
            title=title,
            project_name=project.name,
            period=datetime.now().strftime('%Y-%m-%d'),
            summary=f"Progress summary for {project.name}",
            sections=sections,
            statistics=metrics
        )
    
    async def _generate_custom_report(
        self,
        project: Project,
        work_packages: List[WorkPackage],
        metrics: Dict[str, Any],
        language: ReportLanguage,
        template_id: Optional[str],
        **kwargs
    ) -> Report:
        """生成自定义报告"""
        if not template_id:
            raise ValidationError("Template ID is required for custom reports")
        
        return await self._generate_from_template(
            template_id, project, metrics, language, **kwargs
        )
    
    async def _generate_from_template(
        self,
        template_id: str,
        project: Project,
        metrics: Dict[str, Any],
        language: ReportLanguage,
        **kwargs
    ) -> Report:
        """使用模板生成报告"""
        try:
            # 从模板引擎获取模板
            template_data = await self.template_engine.get_template(template_id)
            if not template_data:
                raise NotFoundError(f"Template not found: {template_id}")
            
            # 准备模板数据
            template_context = {
                'project': project,
                'metrics': metrics,
                'language': language.value,
                'translations': self._translations.get(language.value, {}),
                'now': datetime.now(),
                **kwargs
            }
            
            # 渲染模板
            rendered_content = await self.template_engine.render_template(template_id, template_context)
            
            # 解析渲染内容为报告对象
            # 这里简化处理，实际应该根据模板格式解析
            return Report(
                title=f"{project.name} Report",
                project_name=project.name,
                period=kwargs.get('period', datetime.now().strftime('%Y-%m-%d')),
                summary="Generated from template",
                sections=[ReportSection(title="Content", content=rendered_content)],
                statistics=metrics
            )
            
        except Exception as e:
            self.logger.error(f"Template generation failed: {e}")
            raise
    
    async def _convert_format(self, report: Report, format: ReportFormat) -> Report:
        """转换报告格式"""
        if format == ReportFormat.MARKDOWN:
            return report
        
        # 这里简化处理，实际应该实现完整的格式转换
        converted_report = report.copy()
        
        if format == ReportFormat.HTML:
            # 将markdown转换为HTML
            converted_report.summary = f"<p>{report.summary}</p>"
            for section in converted_report.sections:
                section.content = f"<div>{section.content}</div>"
        elif format == ReportFormat.JSON:
            # 转换为JSON格式
            converted_report.summary = json.dumps({"summary": report.summary})
            for section in converted_report.sections:
                section.content = json.dumps({"title": section.title, "content": section.content})
        elif format == ReportFormat.PLAIN_TEXT:
            # 转换为纯文本
            converted_report.summary = report.summary.replace('**', '').replace('###', '')
            for section in converted_report.sections:
                section.content = section.content.replace('**', '').replace('###', '')
        
        return converted_report
    
    async def get_available_templates(self, report_type: Optional[ReportType] = None) -> List[Dict[str, Any]]:
        """获取可用模板列表"""
        templates = await self.template_engine.list_templates()
        
        if report_type:
            templates = [t for t in templates if t.get('type') == report_type.value]
        
        return templates
    
    async def validate_template(self, template_data: Dict[str, Any]) -> bool:
        """验证模板格式"""
        return await self.template_engine.validate_template(template_data)
    
    async def create_default_templates(self) -> None:
        """创建默认模板"""
        await self.template_engine.create_default_templates()
    
    async def export_report(self, report: Report, format: ReportFormat) -> str:
        """导出报告到指定格式"""
        if format == ReportFormat.MARKDOWN:
            return report.to_markdown()
        elif format == ReportFormat.JSON:
            return report.json()
        elif format == ReportFormat.HTML:
            # 简化的HTML导出
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report.title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #333; }}
                    .section {{ margin-bottom: 30px; }}
                </style>
            </head>
            <body>
                <h1>{report.title}</h1>
                <p><strong>Project:</strong> {report.project_name}</p>
                <p><strong>Period:</strong> {report.period}</p>
                <p><strong>Generated:</strong> {report.generated_at}</p>
                
                <div class="summary">
                    <h2>Summary</h2>
                    <p>{report.summary}</p>
                </div>
                
                {"".join(f'<div class="section"><h2>{section.title}</h2><div>{section.content}</div></div>' for section in report.sections)}
            </body>
            </html>
            """
            return html_content
        else:
            return str(report)