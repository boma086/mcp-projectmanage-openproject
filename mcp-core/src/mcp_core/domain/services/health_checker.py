"""
项目健康度检查领域服务
"""
from datetime import datetime
from typing import List, Dict, Any

from mcp_core.domain.models import Project, WorkPackage, Report, ReportSection
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import NotFoundError


class HealthCheckerService:
    """项目健康度检查服务"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
    
    async def check_project_health(self, project_id: str) -> Report:
        """检查项目健康度"""
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # 获取工作包
        work_packages = await self.client.get_work_packages(project_id)

        if not work_packages:
            return Report(
                title=f"{project.name} 项目健康度检查",
                project_name=project.name,
                period=f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                summary="项目暂无工作包"
            )

        # 健康度指标计算
        total_wps = len(work_packages)
        completed_wps = len([wp for wp in work_packages if wp.status == 'Closed'])
        in_progress_wps = len([wp for wp in work_packages if wp.status == 'In progress'])
        overdue_wps = len([wp for wp in work_packages
                         if wp.due_date and wp.due_date < datetime.now() and wp.status != 'Closed'])
        unassigned_wps = len([wp for wp in work_packages if not wp.assigned_to])
        high_priority_incomplete = len([wp for wp in work_packages
                                      if wp.priority in ['High', 'Immediate'] and wp.status != 'Closed'])

        # 计算健康度分数 (0-100)
        health_score = 100

        # 完成率影响 (40%)
        completion_rate = (completed_wps / total_wps) * 100
        if completion_rate < 30:
            health_score -= 40
        elif completion_rate < 60:
            health_score -= 20
        elif completion_rate < 80:
            health_score -= 10

        # 延期率影响 (30%)
        overdue_rate = (overdue_wps / total_wps) * 100
        if overdue_rate > 20:
            health_score -= 30
        elif overdue_rate > 10:
            health_score -= 20
        elif overdue_rate > 5:
            health_score -= 10

        # 分配率影响 (20%)
        assignment_rate = ((total_wps - unassigned_wps) / total_wps) * 100
        if assignment_rate < 70:
            health_score -= 20
        elif assignment_rate < 85:
            health_score -= 10
        elif assignment_rate < 95:
            health_score -= 5

        # 高优先级未完成影响 (10%)
        if high_priority_incomplete > 5:
            health_score -= 10
        elif high_priority_incomplete > 2:
            health_score -= 5

        # 确保分数在合理范围内
        health_score = max(0, min(100, health_score))

        # 确定健康等级
        if health_score >= 80:
            health_level = "优秀"
            health_emoji = "🟢"
        elif health_score >= 60:
            health_level = "良好"
            health_emoji = "🟡"
        elif health_score >= 40:
            health_level = "一般"
            health_emoji = "🟠"
        else:
            health_level = "需要关注"
            health_emoji = "🔴"

        # 生成报告内容
        sections = []

        # 健康度概览
        overview_content = f"{health_emoji} **项目健康度: {health_level} ({health_score:.1f}分)**\n\n"
        overview_content += f"**关键指标:**\n"
        overview_content += f"- 完成率: {completion_rate:.1f}% ({completed_wps}/{total_wps})\n"
        overview_content += f"- 延期率: {overdue_rate:.1f}% ({overdue_wps}/{total_wps})\n"
        overview_content += f"- 分配率: {assignment_rate:.1f}% ({total_wps - unassigned_wps}/{total_wps})\n"
        overview_content += f"- 进行中: {in_progress_wps} 个工作包"

        sections.append(ReportSection(
            title="健康度概览",
            content=overview_content
        ))

        # 问题分析
        issues = []
        recommendations = []

        if completion_rate < 60:
            issues.append(f"完成率偏低 ({completion_rate:.1f}%)")
            recommendations.append("加强项目执行力度，关注工作包完成情况")

        if overdue_rate > 10:
            issues.append(f"延期率过高 ({overdue_rate:.1f}%)")
            recommendations.append("重新评估工作包时间安排，优化资源配置")

        if assignment_rate < 85:
            issues.append(f"分配率不足 ({assignment_rate:.1f}%)")
            recommendations.append("及时分配未分配的工作包给合适的团队成员")

        if high_priority_incomplete > 2:
            issues.append(f"高优先级未完成项过多 ({high_priority_incomplete}个)")
            recommendations.append("优先处理高优先级工作包，确保关键任务按时完成")

        if issues:
            issues_content = "**发现的问题:**\n"
            for i, issue in enumerate(issues, 1):
                issues_content += f"{i}. {issue}\n"

            sections.append(ReportSection(
                title="问题分析",
                content=issues_content
            ))

            recommendations_content = "**改进建议:**\n"
            for i, rec in enumerate(recommendations, 1):
                recommendations_content += f"{i}. {rec}\n"

            sections.append(ReportSection(
                title="改进建议",
                content=recommendations_content
            ))
        else:
            sections.append(ReportSection(
                title="项目状态",
                content="✅ 项目整体运行良好，无明显问题。"
            ))

        # 统计数据
        statistics = {
            "health_score": round(health_score, 1),
            "health_level": health_level,
            "completion_rate": round(completion_rate, 1),
            "overdue_rate": round(overdue_rate, 1),
            "assignment_rate": round(assignment_rate, 1),
            "total_work_packages": total_wps,
            "completed_work_packages": completed_wps,
            "overdue_work_packages": overdue_wps,
            "unassigned_work_packages": unassigned_wps,
            "high_priority_incomplete": high_priority_incomplete,
            "issues_count": len(issues)
        }

        return Report(
            title=f"{project.name} 项目健康度检查",
            project_name=project.name,
            period=f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            summary=f"项目健康度: {health_level} ({health_score:.1f}分)",
            sections=sections,
            statistics=statistics
        )
