"""
报告上下文数据类
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from mcp_core.domain.models import Project, WorkPackage


@dataclass
class ReportContext:
    """报告生成上下文数据"""
    project: Project
    project_id: str
    start_date: str
    end_date: str
    all_work_packages: List[WorkPackage]
    updated_work_packages: List[WorkPackage]
    all_metrics: Dict[str, Any]
    generated_at: datetime = datetime.now()
    
    @property
    def project_name(self) -> str:
        return self.project.name
    
    @property  
    def agile_metrics(self) -> Dict[str, Any]:
        return self.all_metrics.get("agile_metrics", {})
    
    @property
    def quality_metrics(self) -> Dict[str, Any]:
        return self.all_metrics.get("quality_metrics", {})
    
    @property
    def team_analytics(self) -> Dict[str, Any]:
        return self.all_metrics.get("team_analytics", {})
    
    @property
    def risk_analysis(self) -> Dict[str, Any]:
        return self.all_metrics.get("risk_analysis", {})
    
    @property
    def compliance_check(self) -> Dict[str, Any]:
        return self.all_metrics.get("compliance_check", {})