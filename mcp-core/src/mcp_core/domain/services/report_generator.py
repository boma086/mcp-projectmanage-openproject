"""
报告生成领域服务
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any

from mcp_core.domain.models import Project, WorkPackage, Report, ReportSection
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import NotFoundError


class ReportGeneratorService:
    """报告生成服务"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
    
    async def generate_weekly_report(self, project_id: str, 
                                   start_date: str, end_date: str) -> Report:
        """生成项目周报"""
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
        
        # 按状态分组
        status_groups = {}
        for wp in filtered_wps:
            status = wp.status or "未知状态"
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(wp)
        
        # 生成报告各部分
        sections = []
        
        # 添加概述部分
        summary = f"本周期内（{start_date} 至 {end_date}）共有 {len(filtered_wps)} 个工作包有更新。"
        
        # 添加各状态的工作包部分
        for status, wps in status_groups.items():
            content = f"### {status}工作包（{len(wps)}个）\n\n"
            for wp in wps:
                content += f"- **{wp.subject}** (ID: {wp.id})\n"
                if wp.assigned_to:
                    content += f"  - 负责人: {wp.assigned_to}\n"
                if wp.progress is not None:
                    content += f"  - 进度: {wp.progress}%\n"
                if wp.description:
                    desc_summary = wp.description[:100] + "..." if len(wp.description) > 100 else wp.description
                    content += f"  - 描述: {desc_summary}\n"
                content += "\n"
            
            sections.append(ReportSection(
                title=f"{status}工作包",
                content=content
            ))
        
        # 添加统计信息
        statistics = {
            "total_work_packages": len(work_packages),
            "updated_work_packages": len(filtered_wps),
            "status_distribution": {status: len(wps) for status, wps in status_groups.items()}
        }
        
        # 创建报告
        return Report(
            title=f"{project.name} 周报: {start_date} 至 {end_date}",
            project_name=project.name,
            period=f"{start_date} 至 {end_date}",
            summary=summary,
            sections=sections,
            statistics=statistics
        )
    
    async def generate_monthly_report(self, project_id: str, year: int, month: int) -> Report:
        """生成项目月报"""
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # 获取项目工作包
        work_packages = await self.client.get_work_packages(project_id)
        
        # 计算月份的开始和结束日期
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # 过滤在该月份内更新的工作包
        monthly_wps = [wp for wp in work_packages 
                      if wp.updated_at and start_date <= wp.updated_at <= end_date]
        
        # 生成报告各部分
        sections = []
        
        # 月度概览
        total_wps = len(work_packages)
        completed_wps = len([wp for wp in work_packages if wp.status == 'Closed'])
        in_progress_wps = len([wp for wp in work_packages if wp.status == 'In progress'])
        
        overview_content = f"**项目总体情况:**\n"
        overview_content += f"- 总工作包数: {total_wps}\n"
        overview_content += f"- 已完成: {completed_wps} ({completed_wps/total_wps*100:.1f}%)\n" if total_wps > 0 else "- 已完成: 0 (0%)\n"
        overview_content += f"- 进行中: {in_progress_wps}\n"
        overview_content += f"- 本月更新: {len(monthly_wps)}\n"
        
        sections.append(ReportSection(
            title="月度概览",
            content=overview_content
        ))
        
        # 按状态分组统计
        status_stats = {}
        for wp in work_packages:
            status = wp.status or "未知状态"
            status_stats[status] = status_stats.get(status, 0) + 1
        
        status_content = "**工作包状态分布:**\n"
        for status, count in status_stats.items():
            percentage = (count / total_wps * 100) if total_wps > 0 else 0
            status_content += f"- {status}: {count} ({percentage:.1f}%)\n"
        
        sections.append(ReportSection(
            title="状态分布",
            content=status_content
        ))
        
        # 本月活动
        if monthly_wps:
            activity_content = f"**本月活跃工作包 ({len(monthly_wps)}个):**\n\n"
            for wp in monthly_wps[:10]:  # 限制显示数量
                activity_content += f"- **{wp.subject}** (ID: {wp.id})\n"
                activity_content += f"  - 状态: {wp.status or '未知'}\n"
                if wp.assigned_to:
                    activity_content += f"  - 负责人: {wp.assigned_to}\n"
                activity_content += "\n"
            
            if len(monthly_wps) > 10:
                activity_content += f"... 还有 {len(monthly_wps) - 10} 个工作包\n"
        else:
            activity_content = "本月暂无工作包更新活动。"
        
        sections.append(ReportSection(
            title="本月活动",
            content=activity_content
        ))
        
        # 统计数据
        statistics = {
            "total_work_packages": total_wps,
            "completed_work_packages": completed_wps,
            "in_progress_work_packages": in_progress_wps,
            "monthly_updates": len(monthly_wps),
            "completion_rate": round(completed_wps / total_wps * 100, 1) if total_wps > 0 else 0,
            "status_distribution": status_stats
        }

        return Report(
            title=f"{project.name} 月度报告",
            project_name=project.name,
            period=f"{year}年{month}月",
            summary=f"项目 {project.name} 在 {year}年{month}月 的进展情况",
            sections=sections,
            statistics=statistics
        )
