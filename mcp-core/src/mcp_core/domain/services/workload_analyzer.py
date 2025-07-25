"""
工作负载分析领域服务
"""
from datetime import datetime
from typing import List, Dict, Any

from mcp_core.domain.models import Project, WorkPackage, Report, ReportSection
from mcp_core.domain.interfaces import IOpenProjectClient
from mcp_core.shared.exceptions import NotFoundError


class WorkloadAnalyzerService:
    """工作负载分析服务"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.client = openproject_client
    
    async def analyze_team_workload(self, project_id: str) -> Report:
        """分析团队工作负载"""
        # 获取项目信息
        project = await self.client.get_project(project_id)
        if not project:
            raise NotFoundError(f"Project not found: {project_id}")

        # 获取工作包
        work_packages = await self.client.get_work_packages(project_id)

        # 按负责人分组统计
        workload_by_user = {}
        unassigned_count = 0

        for wp in work_packages:
            if wp.assigned_to:
                if wp.assigned_to not in workload_by_user:
                    workload_by_user[wp.assigned_to] = {
                        "total": 0,
                        "in_progress": 0,
                        "completed": 0,
                        "overdue": 0,
                        "high_priority": 0,
                        "work_packages": []
                    }

                workload_by_user[wp.assigned_to]["total"] += 1
                workload_by_user[wp.assigned_to]["work_packages"].append(wp)

                if wp.status == 'Closed':
                    workload_by_user[wp.assigned_to]["completed"] += 1
                elif wp.status == 'In progress':
                    workload_by_user[wp.assigned_to]["in_progress"] += 1

                # 检查是否延期
                if wp.due_date and wp.due_date < datetime.now() and wp.status != 'Closed':
                    workload_by_user[wp.assigned_to]["overdue"] += 1

                # 检查高优先级
                if wp.priority in ['High', 'Immediate']:
                    workload_by_user[wp.assigned_to]["high_priority"] += 1
            else:
                unassigned_count += 1

        # 生成报告内容
        sections = []

        # 团队概览
        total_members = len(workload_by_user)
        total_assigned_wps = sum([data["total"] for data in workload_by_user.values()])

        overview_content = f"团队成员数量: {total_members}\n"
        overview_content += f"已分配工作包: {total_assigned_wps}\n"
        overview_content += f"未分配工作包: {unassigned_count}\n"
        overview_content += f"总工作包数: {len(work_packages)}"

        sections.append(ReportSection(
            title="团队概览",
            content=overview_content
        ))

        # 成员工作负载详情
        if workload_by_user:
            # 按工作负载排序
            sorted_users = sorted(workload_by_user.items(),
                                key=lambda x: x[1]["total"], reverse=True)

            workload_content = "**成员工作负载分布:**\n\n"
            
            overloaded_users = []
            underloaded_users = []
            
            for user, data in sorted_users:
                workload_content += f"**{user}**\n"
                workload_content += f"- 总工作包: {data['total']}\n"
                workload_content += f"- 进行中: {data['in_progress']}\n"
                workload_content += f"- 已完成: {data['completed']}\n"
                workload_content += f"- 延期: {data['overdue']}\n"
                workload_content += f"- 高优先级: {data['high_priority']}\n"
                
                # 判断工作负载状态
                if data['total'] > 10:  # 超过10个工作包认为过载
                    workload_content += "  ⚠️ **工作负载过重**\n"
                    overloaded_users.append(user)
                elif data['total'] < 3:  # 少于3个工作包认为负载不足
                    workload_content += "  💡 工作负载较轻\n"
                    underloaded_users.append(user)
                else:
                    workload_content += "  ✅ 工作负载适中\n"
                
                workload_content += "\n"

            sections.append(ReportSection(
                title="成员工作负载",
                content=workload_content
            ))

            # 负载平衡建议
            if overloaded_users or underloaded_users:
                suggestions_content = "**负载平衡建议:**\n\n"
                
                if overloaded_users:
                    suggestions_content += f"**过载成员 ({len(overloaded_users)}人):**\n"
                    for user in overloaded_users:
                        suggestions_content += f"- {user}: 考虑重新分配部分工作包\n"
                    suggestions_content += "\n"
                
                if underloaded_users:
                    suggestions_content += f"**负载较轻成员 ({len(underloaded_users)}人):**\n"
                    for user in underloaded_users:
                        suggestions_content += f"- {user}: 可以承担更多工作包\n"
                    suggestions_content += "\n"
                
                if unassigned_count > 0:
                    suggestions_content += f"**未分配工作包:** {unassigned_count}个\n"
                    suggestions_content += "建议优先分配给负载较轻的成员。\n"

                sections.append(ReportSection(
                    title="负载平衡建议",
                    content=suggestions_content
                ))

        # 统计数据
        statistics = {
            "total_members": total_members,
            "total_work_packages": len(work_packages),
            "assigned_work_packages": total_assigned_wps,
            "unassigned_work_packages": unassigned_count,
            "overloaded_members": len(overloaded_users) if 'overloaded_users' in locals() else 0,
            "underloaded_members": len(underloaded_users) if 'underloaded_users' in locals() else 0,
            "assignment_rate": round(total_assigned_wps / len(work_packages) * 100, 1) if work_packages else 0
        }

        return Report(
            title=f"{project.name} 团队工作负载分析",
            project_name=project.name,
            period=f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            summary=f"项目 {project.name} 的团队工作负载分析结果",
            sections=sections,
            statistics=statistics
        )
