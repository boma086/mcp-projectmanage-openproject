"""
Template Service for MCP Protocol

Handles template management and creation with async optimizations.
"""
from typing import List, Dict, Any


class TemplateService:
    """Service for managing MCP templates"""
    
    def __init__(self):
        self.templates_created = False
    
    async def create_default_templates(self) -> None:
        """Create default templates for MCP operations"""
        if not self.templates_created:
            # Default templates are defined in code, no need for external storage
            self.templates_created = True
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List available templates"""
        await self.create_default_templates()
        
        return [
            {
                "name": "weekly_report",
                "description": "Weekly project report template",
                "parameters": [
                    {"name": "project_id", "type": "string", "required": True},
                    {"name": "start_date", "type": "string", "required": True},
                    {"name": "end_date", "type": "string", "required": True}
                ]
            },
            {
                "name": "monthly_report",
                "description": "Monthly project report template",
                "parameters": [
                    {"name": "project_id", "type": "string", "required": True},
                    {"name": "year", "type": "integer", "required": True},
                    {"name": "month", "type": "integer", "required": True}
                ]
            },
            {
                "name": "project_status",
                "description": "Project status update template",
                "parameters": [
                    {"name": "project_id", "type": "string", "required": True}
                ]
            },
            {
                "name": "risk_assessment",
                "description": "Project risk assessment template",
                "parameters": [
                    {"name": "project_id", "type": "string", "required": True}
                ]
            },
            {
                "name": "work_package_summary",
                "description": "Work package summary template",
                "parameters": [
                    {"name": "project_id", "type": "string", "required": True}
                ]
            }
        ]
    
    async def get_template(self, template_name: str) -> Dict[str, Any]:
        """Get a specific template"""
        await self.create_default_templates()
        
        templates = {
            "weekly_report": {
                "name": "weekly_report",
                "content": """
                # Weekly Project Report: {{project_name}}
                
                ## Period: {{start_date}} to {{end_date}}
                
                ## Executive Summary
                {{executive_summary}}
                
                ## Work Package Progress
                {{work_package_progress}}
                
                ## Key Metrics
                - Total Work Packages: {{total_work_packages}}
                - Completed: {{completed_count}}
                - In Progress: {{in_progress_count}}
                - Not Started: {{not_started_count}}
                - Overall Progress: {{overall_progress}}%
                
                ## Risks and Issues
                {{risks_and_issues}}
                
                ## Next Week Priorities
                {{next_week_priorities}}
                """
            },
            "monthly_report": {
                "name": "monthly_report",
                "content": """
                # Monthly Project Report: {{project_name}}
                
                ## Period: {{year}}-{{month}}
                
                ## Monthly Overview
                {{monthly_overview}}
                
                ## Key Achievements
                {{key_achievements}}
                
                ## Financial Summary
                - Budget Utilization: {{budget_utilization}}%
                - Actual Spending: {{actual_spending}}
                - Forecast: {{forecast}}
                
                ## Team Performance
                {{team_performance}}
                
                ## Strategic Recommendations
                {{strategic_recommendations}}
                """
            },
            "project_status": {
                "name": "project_status",
                "content": """
                # Project Status: {{project_name}}
                
                ## Current Status
                - Overall Progress: {{overall_progress}}%
                - Health: {{project_health}}
                - Timeline: {{timeline_status}}
                
                ## Key Updates
                {{key_updates}}
                
                ## Upcoming Milestones
                {{upcoming_milestones}}
                
                ## Action Items
                {{action_items}}
                """
            },
            "risk_assessment": {
                "name": "risk_assessment",
                "content": """
                # Risk Assessment: {{project_name}}
                
                ## Risk Summary
                - Total Risks Identified: {{total_risks}}
                - High Priority: {{high_risk_count}}
                - Medium Priority: {{medium_risk_count}}
                - Low Priority: {{low_risk_count}}
                
                ## Detailed Risk Analysis
                {{detailed_risk_analysis}}
                
                ## Mitigation Strategies
                {{mitigation_strategies}}
                
                ## Risk Monitoring
                {{risk_monitoring}}
                """
            },
            "work_package_summary": {
                "name": "work_package_summary",
                "content": """
                # Work Package Summary: {{project_name}}
                
                ## Overview
                - Total Work Packages: {{total_count}}
                - By Status: {{status_distribution}}
                - By Priority: {{priority_distribution}}
                - By Type: {{type_distribution}}
                
                ## Progress Analysis
                - Average Progress: {{average_progress}}%
                - Median Progress: {{median_progress}}%
                - Progress Distribution: {{progress_distribution}}
                
                ## Top Priorities
                {{top_priorities}}
                
                ## Bottlenecks
                {{bottlenecks}}
                """
            }
        }
        
        template = templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        return template