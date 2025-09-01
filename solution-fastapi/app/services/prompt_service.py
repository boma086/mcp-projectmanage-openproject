"""
Prompt Service for MCP Protocol

Handles prompt listing and retrieval with async optimizations.
"""
from typing import List, Dict, Any
from mcp_core.domain.interfaces.openproject_client import IOpenProjectClient


class PromptService:
    """Service for managing MCP prompts"""
    
    def __init__(self, openproject_client: IOpenProjectClient):
        self.openproject_client = openproject_client
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """List available MCP prompts"""
        return [
            {
                "name": "project_summary",
                "description": "Generate a summary of a specific project",
                "arguments": [
                    {"name": "project_id", "description": "Project ID", "required": True}
                ]
            },
            {
                "name": "work_package_analysis",
                "description": "Analyze work packages for a project",
                "arguments": [
                    {"name": "project_id", "description": "Project ID", "required": True}
                ]
            },
            {
                "name": "weekly_report_template",
                "description": "Template for weekly project report",
                "arguments": [
                    {"name": "project_id", "description": "Project ID", "required": True},
                    {"name": "start_date", "description": "Start date (YYYY-MM-DD)", "required": True},
                    {"name": "end_date", "description": "End date (YYYY-MM-DD)", "required": True}
                ]
            },
            {
                "name": "monthly_report_template",
                "description": "Template for monthly project report",
                "arguments": [
                    {"name": "project_id", "description": "Project ID", "required": True},
                    {"name": "year", "description": "Year", "required": True},
                    {"name": "month", "description": "Month (1-12)", "required": True}
                ]
            },
            {
                "name": "risk_assessment",
                "description": "Assess project risks",
                "arguments": [
                    {"name": "project_id", "description": "Project ID", "required": True}
                ]
            }
        ]
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt with template arguments"""
        try:
            if name == "project_summary":
                project_id = arguments.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                
                project = await self.openproject_client.get_project(project_id)
                work_packages = await self.openproject_client.get_work_packages(project_id)
                
                prompt = f"""
                Please provide a comprehensive summary of the project "{project.name if project else 'Unknown Project'}".
                
                Project Details:
                - ID: {project_id}
                - Name: {project.name if project else 'N/A'}
                - Description: {project.description if project and project.description else 'No description available'}
                - Status: {project.status if project else 'N/A'}
                
                Work Packages ({len(work_packages)} total):
                """
                
                for wp in work_packages[:10]:  # Show first 10 work packages
                    prompt += f"\n- {wp.subject}: {wp.status or 'No status'} ({wp.progress or 0}% complete)"
                
                if len(work_packages) > 10:
                    prompt += f"\n- ... and {len(work_packages) - 10} more work packages"
                
                prompt += """
                
                Please analyze:
                1. Project health and progress
                2. Key work package statuses
                3. Potential risks or issues
                4. Recommendations for next steps
                """
                
                return {"prompt": prompt.strip()}
            
            elif name == "work_package_analysis":
                project_id = arguments.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                
                project = await self.openproject_client.get_project(project_id)
                work_packages = await self.openproject_client.get_work_packages(project_id)
                
                prompt = f"""
                Analyze the work packages for project "{project.name if project else 'Unknown Project'}".
                
                Total Work Packages: {len(work_packages)}
                
                Work Package Breakdown:
                """
                
                status_counts = {}
                for wp in work_packages:
                    status = wp.status or "No Status"
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    prompt += f"\n- {status}: {count} work packages"
                
                prompt += """
                
                Please provide:
                1. Status distribution analysis
                2. Progress assessment
                3. Bottleneck identification
                4. Priority recommendations
                5. Risk assessment for delayed items
                """
                
                return {"prompt": prompt.strip()}
            
            elif name == "weekly_report_template":
                project_id = arguments.get("project_id")
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                
                if not all([project_id, start_date, end_date]):
                    raise ValueError("project_id, start_date, and end_date are required")
                
                project = await self.openproject_client.get_project(project_id)
                
                prompt = f"""
                Weekly Project Report Template
                
                Project: {project.name if project else 'Unknown Project'}
                Period: {start_date} to {end_date}
                
                Please generate a comprehensive weekly report including:
                
                1. Executive Summary
                - Key accomplishments this week
                - Major challenges faced
                - Overall project status
                
                2. Work Package Progress
                - Completed work packages
                - In-progress work packages
                - Blocked/delayed items
                - New work packages created
                
                3. Metrics and KPIs
                - Progress percentage
                - Work package completion rate
                - Resource utilization
                - Risk assessment
                
                4. Next Week Planning
                - Priority tasks
                - Resource requirements
                - Risk mitigation strategies
                - Dependencies and constraints
                
                5. Recommendations
                - Action items for stakeholders
                - Process improvements
                - Risk management suggestions
                """
                
                return {"prompt": prompt.strip()}
            
            elif name == "monthly_report_template":
                project_id = arguments.get("project_id")
                year = arguments.get("year")
                month = arguments.get("month")
                
                if not all([project_id, year, month]):
                    raise ValueError("project_id, year, and month are required")
                
                project = await self.openproject_client.get_project(project_id)
                
                prompt = f"""
                Monthly Project Report Template
                
                Project: {project.name if project else 'Unknown Project'}
                Period: {year}-{month:02d}
                
                Please generate a comprehensive monthly report including:
                
                1. Monthly Overview
                - Key achievements and milestones
                - Budget and resource utilization
                - Schedule performance
                - Quality metrics
                
                2. Detailed Progress Analysis
                - Work package completion status
                - Team performance and velocity
                - Risk and issue tracking
                - Change management summary
                
                3. Financial Summary
                - Budget vs actual spending
                - Resource allocation efficiency
                - Cost performance indicators
                - Forecast for next month
                
                4. Stakeholder Management
                - Communication effectiveness
                - Stakeholder satisfaction
                - Feedback and improvement areas
                
                5. Strategic Recommendations
                - Process optimization suggestions
                - Resource planning for next month
                - Risk mitigation strategies
                - Continuous improvement initiatives
                """
                
                return {"prompt": prompt.strip()}
            
            elif name == "risk_assessment":
                project_id = arguments.get("project_id")
                if not project_id:
                    raise ValueError("project_id is required")
                
                project = await self.openproject_client.get_project(project_id)
                work_packages = await self.openproject_client.get_work_packages(project_id)
                
                prompt = f"""
                Project Risk Assessment
                
                Project: {project.name if project else 'Unknown Project'}
                
                Please conduct a comprehensive risk assessment including:
                
                1. Current Risk Profile
                - Analyze {len(work_packages)} work packages for potential risks
                - Identify delayed or blocked items
                - Assess resource constraints
                
                2. Risk Categorization
                - Schedule risks (timeline delays)
                - Technical risks (implementation challenges)
                - Resource risks (team availability, skills)
                - External risks (dependencies, market changes)
                
                3. Risk Impact Analysis
                - Probability assessment for each identified risk
                - Impact analysis on project objectives
                - Risk severity prioritization
                
                4. Mitigation Strategies
                - Preventive measures for high-probability risks
                - Contingency plans for high-impact risks
                - Risk monitoring and tracking mechanisms
                
                5. Recommendations
                - Immediate action items
                - Long-term risk management strategies
                - Stakeholder communication plan for risks
                """
                
                return {"prompt": prompt.strip()}
            
            else:
                raise ValueError(f"Unknown prompt: {name}")
                
        except Exception as e:
            return {"prompt": f"Error generating prompt: {str(e)}"}