import os
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

from src.models.schemas import Project, WorkPackage, Report, ReportSection
from src.utils.logger import mcp_logger
from src.utils.exceptions import OpenProjectError, AuthenticationError

class OpenProjectAdapter:
    def __init__(self, url: str, api_key: str):
        """初始化OpenProject适配器
        
        Args:
            url: OpenProject实例URL
            api_key: API密钥
        """
        self.base_url = url.rstrip('/')
        self.api_key = api_key
        # 移除错误的 Authorization 头设置
        self.headers = {
            'Content-Type': 'application/json'
        }
        # 使用正确的 Basic Auth 格式：用户名为 'apikey'，密码为 API 密钥
        self.auth = ('apikey', api_key)
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None,
                     request_id: Optional[str] = None) -> Dict:
        """发送API请求"""
        url = f"{self.base_url}/api/v3{endpoint}"
        start_time = time.time()

        try:
            # 使用 auth 参数进行 Basic Auth 认证
            if method in ['POST', 'PATCH', 'PUT']:
                # 对于写操作，使用 json 参数
                response = requests.request(method, url, headers=self.headers, json=params, auth=self.auth, timeout=30)
            else:
                # 对于读操作，使用 params 参数
                response = requests.request(method, url, headers=self.headers, params=params, auth=self.auth, timeout=30)

            response_time = time.time() - start_time

            # 检查HTTP状态码
            if response.status_code == 401:
                mcp_logger.log_openproject_api(endpoint, method, False, response_time, request_id)
                raise AuthenticationError("OpenProject API authentication failed")
            elif response.status_code == 404:
                mcp_logger.log_openproject_api(endpoint, method, False, response_time, request_id)
                raise OpenProjectError(f"Resource not found: {endpoint}", response.status_code)
            elif not response.ok:
                mcp_logger.log_openproject_api(endpoint, method, False, response_time, request_id)
                raise OpenProjectError(
                    f"OpenProject API error: {response.status_code} - {response.text}",
                    response.status_code,
                    {"response_text": response.text}
                )

            # 记录成功的API调用
            mcp_logger.log_openproject_api(endpoint, method, True, response_time, request_id)

            return response.json()

        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            mcp_logger.log_openproject_api(endpoint, method, False, response_time, request_id)
            raise OpenProjectError(f"Request timeout for {endpoint}")
        except requests.exceptions.ConnectionError:
            response_time = time.time() - start_time
            mcp_logger.log_openproject_api(endpoint, method, False, response_time, request_id)
            raise OpenProjectError(f"Connection error for {endpoint}")
        except (AuthenticationError, OpenProjectError):
            # 重新抛出已知的错误
            raise
        except Exception as e:
            response_time = time.time() - start_time
            mcp_logger.log_openproject_api(endpoint, method, False, response_time, request_id)
            raise OpenProjectError(f"Unexpected error calling {endpoint}: {str(e)}")
    
    def get_projects(self, request_id: Optional[str] = None) -> List[Project]:
        """获取所有项目"""
        try:
            data = self._make_request('/projects', request_id=request_id)
            projects = []

            if '_embedded' in data and 'elements' in data['_embedded']:
                for project_data in data['_embedded']['elements']:
                    projects.append(Project(
                        id=str(project_data.get('id', '')),
                        name=project_data.get('name', ''),
                        identifier=project_data.get('identifier', ''),
                        description=project_data.get('description', {}).get('raw', '') if project_data.get('description') else None,
                        created_at=datetime.fromisoformat(project_data['createdAt'].replace('Z', '+00:00')) if project_data.get('createdAt') else None,
                        updated_at=datetime.fromisoformat(project_data['updatedAt'].replace('Z', '+00:00')) if project_data.get('updatedAt') else None,
                        status=project_data.get('status', 'active')
                    ))

            mcp_logger.logger.info(f"成功获取 {len(projects)} 个项目", extra={'request_id': request_id})
            return projects

        except (AuthenticationError, OpenProjectError):
            # 重新抛出已知错误
            raise
        except Exception as e:
            mcp_logger.log_error("获取项目列表时出现未知错误", e, request_id)
            raise OpenProjectError(f"Failed to get projects: {str(e)}")
    
    def get_project(self, project_id: str, request_id: Optional[str] = None) -> Optional[Project]:
        """获取特定项目"""
        try:
            data = self._make_request(f'/projects/{project_id}', request_id=request_id)
            if data:
                return Project(
                    id=str(data.get('id', '')),
                    name=data.get('name', ''),
                    identifier=data.get('identifier', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    status=data.get('status', 'active')
                )
            return None
        except (AuthenticationError, OpenProjectError):
            # 重新抛出已知错误
            raise
        except Exception as e:
            mcp_logger.log_error(f"获取项目 {project_id} 时出现未知错误", e, request_id)
            raise OpenProjectError(f"Failed to get project {project_id}: {str(e)}")
    
    def get_work_packages(self, project_id: str = None, request_id: Optional[str] = None) -> List[WorkPackage]:
        """获取项目的工作包"""
        try:
            if project_id:
                params = {'filters': f'[{{"project":{{"operator":"=","values":["{project_id}"]}}}}]'}
            else:
                params = {}
            data = self._make_request('/work_packages', params=params, request_id=request_id)
            work_packages = []
            
            if '_embedded' in data and 'elements' in data['_embedded']:
                for wp_data in data['_embedded']['elements']:
                    work_packages.append(WorkPackage(
                        id=str(wp_data.get('id', '')),
                        subject=wp_data.get('subject', ''),
                        description=wp_data.get('description', {}).get('raw', '') if wp_data.get('description') else None,
                        status=wp_data.get('_links', {}).get('status', {}).get('title', '') if wp_data.get('_links') else None,
                        type=wp_data.get('_links', {}).get('type', {}).get('title', '') if wp_data.get('_links') else None,
                        priority=wp_data.get('_links', {}).get('priority', {}).get('title', '') if wp_data.get('_links') else None,
                        assigned_to=wp_data.get('_links', {}).get('assignee', {}).get('title', '') if wp_data.get('_links') else None,
                        created_at=datetime.fromisoformat(wp_data['createdAt'].replace('Z', '+00:00')) if wp_data.get('createdAt') else None,
                        updated_at=datetime.fromisoformat(wp_data['updatedAt'].replace('Z', '+00:00')) if wp_data.get('updatedAt') else None,
                        start_date=datetime.fromisoformat(wp_data['startDate']) if wp_data.get('startDate') else None,
                        due_date=datetime.fromisoformat(wp_data['dueDate']) if wp_data.get('dueDate') else None,
                        progress=wp_data.get('percentageDone', 0)
                    ))
            return work_packages
        except Exception as e:
            print(f"获取项目 {project_id} 的工作包时出错: {e}")
            return []
    
    def get_work_package(self, work_package_id: str) -> Optional[WorkPackage]:
        """获取特定工作包"""
        try:
            data = self._make_request(f'/work_packages/{work_package_id}')
            if data:
                return WorkPackage(
                    id=str(data.get('id', '')),
                    subject=data.get('subject', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    status=data.get('_links', {}).get('status', {}).get('title', '') if data.get('_links') else None,
                    type=data.get('_links', {}).get('type', {}).get('title', '') if data.get('_links') else None,
                    priority=data.get('_links', {}).get('priority', {}).get('title', '') if data.get('_links') else None,
                    assigned_to=data.get('_links', {}).get('assignee', {}).get('title', '') if data.get('_links') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    start_date=datetime.fromisoformat(data['startDate']) if data.get('startDate') else None,
                    due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
                    progress=data.get('percentageDone', 0)
                )
        except Exception as e:
            print(f"获取工作包 {work_package_id} 时出错: {e}")
            return None

    def create_work_package(self, project_id: str, subject: str, description: str = None, work_package_type: str = "Task") -> Optional[WorkPackage]:
        """创建新的工作包"""
        try:
            payload = {
                "subject": subject,
                "_links": {
                    "project": {"href": f"/api/v3/projects/{project_id}"},
                    "type": {"href": f"/api/v3/types/1"}  # 默认类型，可能需要根据实际情况调整
                }
            }
            if description:
                payload["description"] = {"raw": description}

            data = self._make_request('/work_packages', method='POST', params=payload)
            if data:
                return WorkPackage(
                    id=str(data.get('id', '')),
                    subject=data.get('subject', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    status=data.get('_links', {}).get('status', {}).get('title', '') if data.get('_links') else None,
                    type=data.get('_links', {}).get('type', {}).get('title', '') if data.get('_links') else None,
                    priority=data.get('_links', {}).get('priority', {}).get('title', '') if data.get('_links') else None,
                    assigned_to=data.get('_links', {}).get('assignee', {}).get('title', '') if data.get('_links') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    start_date=datetime.fromisoformat(data['startDate']) if data.get('startDate') else None,
                    due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
                    progress=data.get('percentageDone', 0)
                )
        except Exception as e:
            print(f"创建工作包时出错: {e}")
            return None

    def update_work_package(self, work_package_id: str, subject: str = None, description: str = None, status: str = None) -> Optional[WorkPackage]:
        """更新工作包信息"""
        try:
            payload = {}
            if subject:
                payload["subject"] = subject
            if description:
                payload["description"] = {"raw": description}
            # 状态更新需要特殊处理，这里简化处理

            data = self._make_request(f'/work_packages/{work_package_id}', method='PATCH', params=payload)
            if data:
                return WorkPackage(
                    id=str(data.get('id', '')),
                    subject=data.get('subject', ''),
                    description=data.get('description', {}).get('raw', '') if data.get('description') else None,
                    status=data.get('_links', {}).get('status', {}).get('title', '') if data.get('_links') else None,
                    type=data.get('_links', {}).get('type', {}).get('title', '') if data.get('_links') else None,
                    priority=data.get('_links', {}).get('priority', {}).get('title', '') if data.get('_links') else None,
                    assigned_to=data.get('_links', {}).get('assignee', {}).get('title', '') if data.get('_links') else None,
                    created_at=datetime.fromisoformat(data['createdAt'].replace('Z', '+00:00')) if data.get('createdAt') else None,
                    updated_at=datetime.fromisoformat(data['updatedAt'].replace('Z', '+00:00')) if data.get('updatedAt') else None,
                    start_date=datetime.fromisoformat(data['startDate']) if data.get('startDate') else None,
                    due_date=datetime.fromisoformat(data['dueDate']) if data.get('dueDate') else None,
                    progress=data.get('percentageDone', 0)
                )
        except Exception as e:
            print(f"更新工作包 {work_package_id} 时出错: {e}")
            return None

    def generate_project_report(self, project_id: str, request_id: Optional[str] = None) -> Report:
        """生成项目报告"""
        # 生成最近一周的报告
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        return self.generate_weekly_report(
            project_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            request_id
        )

    def generate_weekly_report(self, project_id: str, start_date: str, end_date: str, request_id: Optional[str] = None) -> Report:
        """生成项目周报"""
        try:
            # 获取项目信息
            project = self.get_project(project_id, request_id)
            if not project:
                raise ValueError(f"找不到项目 {project_id}")

            # 获取项目工作包
            work_packages = self.get_work_packages(project_id, request_id)
            
            # 过滤指定日期范围内更新的工作包
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # 过滤在日期范围内更新的工作包
            filtered_wps = [wp for wp in work_packages if wp.updated_at and start_dt <= wp.updated_at <= end_dt]
            
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
            
        except Exception as e:
            print(f"生成周报时出错: {e}")
            # 返回一个错误报告
            return Report(
                title="生成报告出错",
                project_name=f"项目 {project_id}",
                period=f"{start_date} 至 {end_date}",
                summary=f"生成报告时出错: {str(e)}",
                sections=[],
                statistics={}
            )

    def generate_monthly_report(self, project_id: str, year: int, month: int, request_id: Optional[str] = None) -> Report:
        """生成月度项目报告"""
        try:
            # 获取项目信息
            project = self.get_project(project_id, request_id=request_id)
            if not project:
                raise ValueError(f"项目 {project_id} 不存在")

            # 计算月份的开始和结束日期
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)

            # 获取工作包
            work_packages = self.get_work_packages(project_id, request_id=request_id)

            # 过滤本月相关的工作包
            monthly_created = []
            monthly_completed = []
            monthly_updated = []

            for wp in work_packages:
                # 本月创建的工作包
                if wp.created_at and start_date <= wp.created_at.replace(tzinfo=None) <= end_date:
                    monthly_created.append(wp)

                # 本月完成的工作包
                if (wp.status == 'Closed' and wp.updated_at and
                    start_date <= wp.updated_at.replace(tzinfo=None) <= end_date):
                    monthly_completed.append(wp)

                # 本月有更新的工作包
                if wp.updated_at and start_date <= wp.updated_at.replace(tzinfo=None) <= end_date:
                    monthly_updated.append(wp)

            # 统计信息
            total_work_packages = len(work_packages)
            completed_work_packages = len([wp for wp in work_packages if wp.status == 'Closed'])
            in_progress_work_packages = len([wp for wp in work_packages if wp.status == 'In progress'])

            # 状态分布
            status_distribution = {}
            for wp in work_packages:
                status = wp.status or 'Unknown'
                status_distribution[status] = status_distribution.get(status, 0) + 1

            # 优先级分布
            priority_distribution = {}
            for wp in work_packages:
                priority = wp.priority or 'Unknown'
                priority_distribution[priority] = priority_distribution.get(priority, 0) + 1

            # 计算完成率
            completion_rate = (completed_work_packages / total_work_packages * 100) if total_work_packages > 0 else 0

            # 生成统计数据
            statistics = {
                "total_work_packages": total_work_packages,
                "completed_work_packages": completed_work_packages,
                "in_progress_work_packages": in_progress_work_packages,
                "completion_rate": round(completion_rate, 1),
                "monthly_created": len(monthly_created),
                "monthly_completed": len(monthly_completed),
                "monthly_updated": len(monthly_updated),
                "status_distribution": status_distribution,
                "priority_distribution": priority_distribution
            }

            # 生成报告章节
            sections = [
                ReportSection(
                    title="月度概览",
                    content=f"本月新建 {len(monthly_created)} 个工作包，完成 {len(monthly_completed)} 个工作包，活跃工作包 {len(monthly_updated)} 个。"
                ),
                ReportSection(
                    title="整体进度",
                    content=f"项目总共有 {total_work_packages} 个工作包，其中 {completed_work_packages} 个已完成，{in_progress_work_packages} 个正在进行中，完成率为 {completion_rate:.1f}%。"
                ),
                ReportSection(
                    title="状态分布",
                    content="、".join([f"{status}: {count}个" for status, count in status_distribution.items()])
                ),
                ReportSection(
                    title="优先级分布",
                    content="、".join([f"{priority}: {count}个" for priority, count in priority_distribution.items()])
                )
            ]

            return Report(
                title=f"{project.name} 月度报告",
                project_name=project.name,
                period=f"{year}年{month}月",
                summary=f"项目 {project.name} 在 {year}年{month}月 的进展情况",
                sections=sections,
                statistics=statistics
            )

        except Exception as e:
            mcp_logger.log_error(f"生成月度报告失败: {e}", e, request_id)
            # 返回一个错误报告
            return Report(
                title="生成月度报告出错",
                project_name=f"项目 {project_id}",
                period=f"{year}年{month}月",
                summary=f"生成月度报告时出错: {str(e)}",
                sections=[],
                statistics={}
            )

    def assess_project_risks(self, project_id: str, request_id: Optional[str] = None) -> Report:
        """评估项目风险"""
        try:
            # 获取项目信息
            project = self.get_project(project_id, request_id=request_id)
            if not project:
                raise ValueError(f"项目 {project_id} 不存在")

            # 获取工作包
            work_packages = self.get_work_packages(project_id, request_id=request_id)

            # 风险评估
            risks = []
            high_risk_count = 0
            medium_risk_count = 0
            low_risk_count = 0

            current_date = datetime.now()

            for wp in work_packages:
                risk_level = "低"
                risk_factors = []

                # 检查延期风险
                # 确保日期为同一时区
                if wp.due_date:
                    if wp.due_date.tzinfo is None:
                        due_date = wp.due_date.replace(tzinfo=timezone.utc)
                    else:
                        due_date = wp.due_date.astimezone(timezone.utc)
                    if current_date.tzinfo is None:
                        current_dt = current_date.replace(tzinfo=timezone.utc)
                    else:
                        current_dt = current_date.astimezone(timezone.utc)
                else:
                    due_date = None
                    current_dt = None

                if due_date and due_date < current_dt and wp.status != 'Closed':
                    risk_factors.append("已延期")
                    risk_level = "高"
                elif due_date and (due_date - current_dt).days <= 3 and wp.status != 'Closed':
                    risk_factors.append("即将到期")
                    if risk_level == "低":
                        risk_level = "中"

                # 检查进度风险
                if wp.progress is not None and wp.progress < 50 and due_date and (due_date - current_dt).days <= 7:
                    risk_factors.append("进度滞后")
                    if risk_level == "低":
                        risk_level = "中"

                # 检查无负责人风险
                if not wp.assigned_to:
                    risk_factors.append("无负责人")
                    if risk_level == "低":
                        risk_level = "中"

                # 检查高优先级风险
                if wp.priority in ['High', 'Immediate'] and wp.status != 'Closed':
                    risk_factors.append("高优先级未完成")
                    if risk_level == "低":
                        risk_level = "中"

                if risk_factors:
                    risks.append({
                        "work_package": wp.subject,
                        "id": wp.id,
                        "risk_level": risk_level,
                        "risk_factors": risk_factors,
                        "status": wp.status,
                        "due_date": wp.due_date.strftime("%Y-%m-%d") if wp.due_date else None,
                        "assigned_to": wp.assigned_to
                    })

                    if risk_level == "高":
                        high_risk_count += 1
                    elif risk_level == "中":
                        medium_risk_count += 1
                    else:
                        low_risk_count += 1

            # 生成风险报告内容
            sections = []

            # 风险概览
            overview_content = f"项目共发现 {len(risks)} 个风险项：\n"
            overview_content += f"- 高风险: {high_risk_count} 个\n"
            overview_content += f"- 中风险: {medium_risk_count} 个\n"
            overview_content += f"- 低风险: {low_risk_count} 个"

            sections.append(ReportSection(
                title="风险概览",
                content=overview_content
            ))

            # 高风险项目
            if high_risk_count > 0:
                high_risk_items = [r for r in risks if r["risk_level"] == "高"]
                high_risk_content = ""
                for item in high_risk_items:
                    high_risk_content += f"- **{item['work_package']}** (ID: {item['id']})\n"
                    high_risk_content += f"  - 风险因素: {', '.join(item['risk_factors'])}\n"
                    high_risk_content += f"  - 状态: {item['status']}\n"
                    high_risk_content += f"  - 截止日期: {item['due_date']}\n" if item['due_date'] else ""
                    high_risk_content += f"  - 负责人: {item['assigned_to']}\n" if item['assigned_to'] else ""
                    high_risk_content += "\n"

                sections.append(ReportSection(
                    title="高风险项目",
                    content=high_risk_content
                ))

            # 中风险项目
            if medium_risk_count > 0:
                medium_risk_items = [r for r in risks if r["risk_level"] == "中"]
                medium_risk_content = ""
                for item in medium_risk_items[:5]:  # 只显示前5个
                    medium_risk_content += f"- **{item['work_package']}** (ID: {item['id']})\n"
                    medium_risk_content += f"  - 风险因素: {', '.join(item['risk_factors'])}\n"
                    medium_risk_content += f"  - 状态: {item['status']}\n"
                    medium_risk_content += "\n"

                if len(medium_risk_items) > 5:
                    medium_risk_content += f"... 还有 {len(medium_risk_items) - 5} 个中风险项目"

                sections.append(ReportSection(
                    title="中风险项目",
                    content=medium_risk_content
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

        except Exception as e:
            mcp_logger.log_error(f"风险评估失败: {e}", e, request_id)
            return Report(
                title="风险评估出错",
                project_name=f"项目 {project_id}",
                period=f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                summary=f"风险评估时出错: {str(e)}",
                sections=[],
                statistics={}
            )

    def analyze_team_workload(self, project_id: str, request_id: Optional[str] = None) -> Report:
        """分析团队工作负载"""
        try:
            # 获取项目信息
            project = self.get_project(project_id, request_id=request_id)
            if not project:
                raise ValueError(f"项目 {project_id} 不存在")

            # 获取工作包
            work_packages = self.get_work_packages(project_id, request_id=request_id)

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

                workload_content = ""
                for user, data in sorted_users:
                    completion_rate = (data["completed"] / data["total"] * 100) if data["total"] > 0 else 0

                    workload_content += f"**{user}**\n"
                    workload_content += f"- 总工作包: {data['total']}\n"
                    workload_content += f"- 进行中: {data['in_progress']}\n"
                    workload_content += f"- 已完成: {data['completed']} ({completion_rate:.1f}%)\n"
                    workload_content += f"- 延期: {data['overdue']}\n"
                    workload_content += f"- 高优先级: {data['high_priority']}\n"

                    # 工作负载评估
                    if data["total"] > 10:
                        workload_content += f"- 负载状态: 🔴 超负荷\n"
                    elif data["total"] > 5:
                        workload_content += f"- 负载状态: 🟡 较重\n"
                    else:
                        workload_content += f"- 负载状态: 🟢 正常\n"

                    workload_content += "\n"

                sections.append(ReportSection(
                    title="成员工作负载",
                    content=workload_content
                ))

            # 负载预警
            warnings = []
            overloaded_users = []
            underloaded_users = []

            for user, data in workload_by_user.items():
                if data["total"] > 10:
                    overloaded_users.append(user)
                    warnings.append(f"{user}: 工作包过多 ({data['total']}个)")
                elif data["total"] < 2:
                    underloaded_users.append(user)

                if data["overdue"] > 0:
                    warnings.append(f"{user}: 有 {data['overdue']} 个延期工作包")

            if warnings:
                warning_content = "⚠️ 发现以下问题:\n\n"
                warning_content += "\n".join([f"- {w}" for w in warnings])

                if overloaded_users:
                    warning_content += f"\n\n建议重新分配 {', '.join(overloaded_users)} 的部分工作包"

                sections.append(ReportSection(
                    title="负载预警",
                    content=warning_content
                ))

            # 统计数据
            statistics = {
                "total_members": total_members,
                "total_work_packages": len(work_packages),
                "assigned_work_packages": total_assigned_wps,
                "unassigned_work_packages": unassigned_count,
                "overloaded_members": len(overloaded_users),
                "underloaded_members": len(underloaded_users),
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

        except Exception as e:
            mcp_logger.log_error(f"团队工作负载分析失败: {e}", e, request_id)
            return Report(
                title="团队工作负载分析出错",
                project_name=f"项目 {project_id}",
                period=f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                summary=f"团队工作负载分析时出错: {str(e)}",
                sections=[],
                statistics={}
            )

    def check_project_health(self, project_id: str, request_id: Optional[str] = None) -> Report:
        """检查项目健康度"""
        try:
            # 获取项目信息
            project = self.get_project(project_id, request_id=request_id)
            if not project:
                raise ValueError(f"项目 {project_id} 不存在")

            # 获取工作包
            work_packages = self.get_work_packages(project_id, request_id=request_id)

            if not work_packages:
                return Report(
                    title=f"{project.name} 项目健康度检查",
                    project_name=project.name,
                    period=f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    summary="项目暂无工作包",
                    sections=[],
                    statistics={}
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

            # 高优先级完成情况影响 (10%)
            if high_priority_incomplete > 0:
                high_priority_total = len([wp for wp in work_packages if wp.priority in ['High', 'Immediate']])
                if high_priority_total > 0:
                    high_priority_completion = ((high_priority_total - high_priority_incomplete) / high_priority_total) * 100
                    if high_priority_completion < 50:
                        health_score -= 10
                    elif high_priority_completion < 80:
                        health_score -= 5

            # 确保分数在0-100范围内
            health_score = max(0, min(100, health_score))

            # 健康度等级
            if health_score >= 90:
                health_level = "优秀"
                health_emoji = "🟢"
            elif health_score >= 75:
                health_level = "良好"
                health_emoji = "🟡"
            elif health_score >= 60:
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
                recommendations.append("及时分配未指派的工作包，明确责任人")

            if high_priority_incomplete > 0:
                issues.append(f"有 {high_priority_incomplete} 个高优先级工作包未完成")
                recommendations.append("优先处理高优先级工作包，确保关键任务按时完成")

            if issues:
                issues_content = "**发现的问题:**\n"
                issues_content += "\n".join([f"- {issue}" for issue in issues])
                issues_content += "\n\n**改进建议:**\n"
                issues_content += "\n".join([f"- {rec}" for rec in recommendations])

                sections.append(ReportSection(
                    title="问题分析与建议",
                    content=issues_content
                ))
            else:
                sections.append(ReportSection(
                    title="项目状态",
                    content="✅ 项目运行良好，未发现明显问题"
                ))

            # 趋势分析 (基于最近更新的工作包)
            recent_updates = [wp for wp in work_packages
                            if wp.updated_at and (datetime.now() - wp.updated_at.replace(tzinfo=None)).days <= 7]

            if recent_updates:
                trend_content = f"**最近7天活跃度:**\n"
                trend_content += f"- 有更新的工作包: {len(recent_updates)} 个\n"
                trend_content += f"- 活跃度: {len(recent_updates) / total_wps * 100:.1f}%\n"

                if len(recent_updates) / total_wps > 0.3:
                    trend_content += "- 趋势: 📈 项目活跃度较高"
                elif len(recent_updates) / total_wps > 0.1:
                    trend_content += "- 趋势: 📊 项目活跃度正常"
                else:
                    trend_content += "- 趋势: 📉 项目活跃度较低，需要关注"

                sections.append(ReportSection(
                    title="活跃度分析",
                    content=trend_content
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
                "recent_activity": len(recent_updates),
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

        except Exception as e:
            mcp_logger.log_error(f"项目健康度检查失败: {e}", e, request_id)
            return Report(
                title="项目健康度检查出错",
                project_name=f"项目 {project_id}",
                period=f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                summary=f"项目健康度检查时出错: {str(e)}",
                sections=[],
                statistics={}
            )