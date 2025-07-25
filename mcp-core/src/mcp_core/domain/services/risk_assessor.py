"""
风险评估领域服务
"""
from datetime import datetime
from typing import List, Dict, Any

from mcp_core.domain.models import Project, WorkPackage, Report, ReportSection
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import NotFoundError


class RiskAssessorService:
    """风险评估服务"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
    
    async def assess_project_risks(self, project_id: str) -> Report:
        """评估项目风险"""
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # 获取工作包
        work_packages = await self.client.get_work_packages(project_id)
        
        if not work_packages:
            return Report(
                title=f"{project.name} 风险评估报告",
                project_name=project.name,
                period=f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                summary="项目暂无工作包，无法进行风险评估"
            )

        # 风险评估逻辑
        risks = []
        current_date = datetime.now()
        
        # 1. 延期风险
        overdue_wps = [wp for wp in work_packages 
                      if wp.due_date and wp.due_date < current_date and wp.status != 'Closed']
        
        if overdue_wps:
            risk_level = "高" if len(overdue_wps) > len(work_packages) * 0.2 else "中"
            risks.append({
                "type": "延期风险",
                "level": risk_level,
                "description": f"有 {len(overdue_wps)} 个工作包已延期",
                "work_packages": overdue_wps[:5]  # 只显示前5个
            })
        
        # 2. 资源分配风险
        unassigned_wps = [wp for wp in work_packages if not wp.assigned_to]
        if unassigned_wps:
            risk_level = "高" if len(unassigned_wps) > len(work_packages) * 0.3 else "中"
            risks.append({
                "type": "资源分配风险",
                "level": risk_level,
                "description": f"有 {len(unassigned_wps)} 个工作包未分配负责人",
                "work_packages": unassigned_wps[:5]
            })
        
        # 3. 高优先级未完成风险
        high_priority_incomplete = [wp for wp in work_packages 
                                  if wp.priority in ['High', 'Immediate'] and wp.status != 'Closed']
        if high_priority_incomplete:
            risk_level = "高" if len(high_priority_incomplete) > 3 else "中"
            risks.append({
                "type": "高优先级未完成风险",
                "level": risk_level,
                "description": f"有 {len(high_priority_incomplete)} 个高优先级工作包未完成",
                "work_packages": high_priority_incomplete[:5]
            })
        
        # 4. 进度停滞风险
        stagnant_wps = []
        for wp in work_packages:
            if (wp.status == 'In progress' and wp.updated_at and 
                (current_date - wp.updated_at).days > 7):
                stagnant_wps.append(wp)
        
        if stagnant_wps:
            risk_level = "中" if len(stagnant_wps) > 2 else "低"
            risks.append({
                "type": "进度停滞风险",
                "level": risk_level,
                "description": f"有 {len(stagnant_wps)} 个工作包超过7天未更新",
                "work_packages": stagnant_wps[:5]
            })

        # 生成报告内容
        sections = []
        
        # 风险概览
        high_risk_count = len([r for r in risks if r["level"] == "高"])
        medium_risk_count = len([r for r in risks if r["level"] == "中"])
        low_risk_count = len([r for r in risks if r["level"] == "低"])
        
        overview_content = f"**风险评估结果:**\n"
        overview_content += f"- 高风险项: {high_risk_count}\n"
        overview_content += f"- 中风险项: {medium_risk_count}\n"
        overview_content += f"- 低风险项: {low_risk_count}\n"
        overview_content += f"- 总风险项: {len(risks)}\n"
        
        if not risks:
            overview_content += "\n✅ 项目当前无明显风险。"
        elif high_risk_count > 0:
            overview_content += "\n⚠️ 项目存在高风险项，需要立即关注。"
        else:
            overview_content += "\n⚡ 项目存在一些风险，建议持续监控。"
        
        sections.append(ReportSection(
            title="风险概览",
            content=overview_content
        ))
        
        # 详细风险分析
        if risks:
            for risk in risks:
                risk_emoji = "🔴" if risk["level"] == "高" else "🟡" if risk["level"] == "中" else "🟢"
                content = f"{risk_emoji} **风险等级: {risk['level']}**\n\n"
                content += f"{risk['description']}\n\n"
                
                if risk["work_packages"]:
                    content += "**相关工作包:**\n"
                    for wp in risk["work_packages"]:
                        content += f"- {wp.subject} (ID: {wp.id})\n"
                        if wp.due_date and risk["type"] == "延期风险":
                            days_overdue = (current_date - wp.due_date).days
                            content += f"  延期 {days_overdue} 天\n"
                    
                    if len(risk["work_packages"]) == 5:
                        content += "...\n"
                
                sections.append(ReportSection(
                    title=risk["type"],
                    content=content
                ))

        # 统计数据
        statistics = {
            "total_risks": len(risks),
            "high_risk_count": high_risk_count,
            "medium_risk_count": medium_risk_count,
            "low_risk_count": low_risk_count,
            "total_work_packages": len(work_packages),
            "risk_percentage": round(len(risks) / len(work_packages) * 100, 1) if work_packages else 0
        }

        return Report(
            title=f"{project.name} 风险评估报告",
            project_name=project.name,
            period=f"评估时间: {current_date.strftime('%Y-%m-%d %H:%M')}",
            summary=f"项目 {project.name} 的风险评估结果",
            sections=sections,
            statistics=statistics
        )
