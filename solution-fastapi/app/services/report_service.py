"""
Report Service for MCP Protocol

Handles report generation with async optimizations.
"""
from typing import Dict, Any
from mcp_core.domain.interfaces.openproject_client import IOpenProjectClient


class ReportService:
    """Service for managing MCP reports"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.openproject_client = openproject_client
    
    async def generate_report(self, report_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a report of specified type"""
        try:
            if report_type == "weekly":
                project_id = parameters.get("project_id")
                start_date = parameters.get("start_date")
                end_date = parameters.get("end_date")
                
                if not all([project_id, start_date, end_date]):
                    raise ValueError("project_id, start_date, and end_date are required")
                
                report = await self.openproject_client.generate_weekly_report(project_id, start_date, end_date)
                return {
                    "report_type": "weekly",
                    "project_id": project_id,
                    "period": f"{start_date} to {end_date}",
                    "content": report.dict() if hasattr(report, 'dict') else str(report)
                }
            
            elif report_type == "monthly":
                project_id = parameters.get("project_id")
                year = parameters.get("year")
                month = parameters.get("month")
                
                if not all([project_id, year, month]):
                    raise ValueError("project_id, year, and month are required")
                
                report = await self.openproject_client.generate_monthly_report(project_id, year, month)
                return {
                    "report_type": "monthly",
                    "project_id": project_id,
                    "period": f"{year}-{month:02d}",
                    "content": report.dict() if hasattr(report, 'dict') else str(report)
                }
            
            elif report_type == "risk_assessment":
                project_id = parameters.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                
                report = await self.openproject_client.assess_project_risks(project_id)
                return {
                    "report_type": "risk_assessment",
                    "project_id": project_id,
                    "content": report.dict() if hasattr(report, 'dict') else str(report)
                }
            
            elif report_type == "project_summary":
                project_id = parameters.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                
                project = await self.openproject_client.get_project(project_id)
                work_packages = await self.openproject_client.get_work_packages(project_id)
                
                # Generate summary report
                summary = {
                    "project": project.dict() if project else None,
                    "work_package_count": len(work_packages),
                    "status_distribution": {},
                    "progress_summary": {
                        "total": len(work_packages),
                        "completed": len([wp for wp in work_packages if wp.progress == 100]),
                        "in_progress": len([wp for wp in work_packages if wp.progress and 0 < wp.progress < 100]),
                        "not_started": len([wp for wp in work_packages if not wp.progress or wp.progress == 0])
                    }
                }
                
                # Calculate status distribution
                for wp in work_packages:
                    status = wp.status or "No Status"
                    summary["status_distribution"][status] = summary["status_distribution"].get(status, 0) + 1
                
                return {
                    "report_type": "project_summary",
                    "project_id": project_id,
                    "content": summary
                }
            
            elif report_type == "work_package_analysis":
                project_id = parameters.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                
                work_packages = await self.openproject_client.get_work_packages(project_id)
                
                analysis = {
                    "total_count": len(work_packages),
                    "by_status": {},
                    "by_priority": {},
                    "by_type": {},
                    "progress_analysis": {
                        "average_progress": 0,
                        "median_progress": 0,
                        "progress_distribution": {
                            "0-25%": 0,
                            "26-50%": 0,
                            "51-75%": 0,
                            "76-99%": 0,
                            "100%": 0
                        }
                    }
                }
                
                # Calculate various metrics
                progress_values = []
                for wp in work_packages:
                    # Status distribution
                    status = wp.status or "No Status"
                    analysis["by_status"][status] = analysis["by_status"].get(status, 0) + 1
                    
                    # Priority distribution
                    priority = wp.priority or "No Priority"
                    analysis["by_priority"][priority] = analysis["by_priority"].get(priority, 0) + 1
                    
                    # Type distribution
                    wp_type = wp.type or "No Type"
                    analysis["by_type"][wp_type] = analysis["by_type"].get(wp_type, 0) + 1
                    
                    # Progress analysis
                    progress = wp.progress or 0
                    progress_values.append(progress)
                    
                    if progress == 100:
                        analysis["progress_analysis"]["progress_distribution"]["100%"] += 1
                    elif progress >= 76:
                        analysis["progress_analysis"]["progress_distribution"]["76-99%"] += 1
                    elif progress >= 51:
                        analysis["progress_analysis"]["progress_distribution"]["51-75%"] += 1
                    elif progress >= 26:
                        analysis["progress_analysis"]["progress_distribution"]["26-50%"] += 1
                    else:
                        analysis["progress_analysis"]["progress_distribution"]["0-25%"] += 1
                
                # Calculate average and median progress
                if progress_values:
                    analysis["progress_analysis"]["average_progress"] = sum(progress_values) / len(progress_values)
                    sorted_progress = sorted(progress_values)
                    mid = len(sorted_progress) // 2
                    if len(sorted_progress) % 2 == 0:
                        analysis["progress_analysis"]["median_progress"] = (sorted_progress[mid - 1] + sorted_progress[mid]) / 2
                    else:
                        analysis["progress_analysis"]["median_progress"] = sorted_progress[mid]
                
                return {
                    "report_type": "work_package_analysis",
                    "project_id": project_id,
                    "content": analysis
                }
            
            else:
                raise ValueError(f"Unknown report type: {report_type}")
                
        except Exception as e:
            return {
                "report_type": report_type,
                "error": str(e),
                "content": f"Error generating {report_type} report: {str(e)}"
            }