"""
Projects Router - HTTP Solution
Synchronous REST API endpoints for OpenProject project operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import dependencies and core models
from ..dependencies import SyncAsyncAdapter, validate_openproject_connection, get_basic_adapter
from mcp_core.domain.models import Project, Report
from mcp_core.shared.exceptions import OpenProjectError, NotFoundError, AuthenticationError
from mcp_core.shared.logger import get_logger

logger = get_logger("http.routers.projects")

# Create router instance
router = APIRouter(
    prefix="/api/projects",
    tags=["projects"],
    responses={
        404: {"description": "Project not found"},
        401: {"description": "Authentication failed"},
        503: {"description": "OpenProject service unavailable"}
    }
)

# Response models
class ProjectResponse(BaseModel):
    """Project response model"""
    id: str
    name: str
    identifier: str
    description: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProjectListResponse(BaseModel):
    """Project list response model"""
    projects: List[ProjectResponse]
    total: int
    
class ReportResponse(BaseModel):
    """Report response model"""
    id: str
    title: str
    content: str
    generated_at: datetime
    project_id: str
    report_type: str

# Project CRUD Endpoints

@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="Get all projects",
    description="Retrieve a list of all projects from OpenProject"
)
def get_projects(
    offset: int = Query(0, ge=0, description="Number of projects to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of projects to return"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> ProjectListResponse:
    """
    Get all projects with pagination support
    
    Returns:
        ProjectListResponse: List of projects with total count
        
    Raises:
        HTTPException: 500 for server errors, 503 for service unavailable
    """
    try:
        logger.info(f"Fetching projects with offset={offset}, limit={limit}")
        
        # Get all projects using the adapter
        projects = adapter.get_projects()
        
        # Apply pagination
        total = len(projects)
        paginated_projects = projects[offset:offset + limit]
        
        # Convert to response models
        project_responses = [
            ProjectResponse(
                id=project.id,
                name=project.name,
                identifier=project.identifier,
                description=project.description,
                status=project.status,
                created_at=project.created_at,
                updated_at=project.updated_at
            )
            for project in paginated_projects
        ]
        
        logger.info(f"Successfully retrieved {len(project_responses)} projects out of {total}")
        
        return ProjectListResponse(
            projects=project_responses,
            total=total
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a specific project by its ID"
)
def get_project(
    project_id: str = Path(..., description="The ID of the project to retrieve"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> ProjectResponse:
    """
    Get a specific project by ID
    
    Args:
        project_id: The project ID to retrieve
        
    Returns:
        ProjectResponse: The requested project
        
    Raises:
        HTTPException: 404 for not found, 500 for server errors
    """
    try:
        logger.info(f"Fetching project with ID: {project_id}")
        
        # Get project using the adapter
        project = adapter.get_project(project_id)
        
        if project is None:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
        
        logger.info(f"Successfully retrieved project: {project.name}")
        
        return ProjectResponse(
            id=project.id,
            name=project.name,
            identifier=project.identifier,
            description=project.description,
            status=project.status,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except NotFoundError as e:
        logger.warning(f"Project not found: {e}")
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch project: {str(e)}")


# Project Reporting Endpoints

@router.post(
    "/{project_id}/reports/weekly",
    response_model=ReportResponse,
    summary="Generate weekly report",
    description="Generate a weekly report for the specified project"
)
def generate_weekly_report(
    project_id: str = Path(..., description="The ID of the project"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD format)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD format)"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> ReportResponse:
    """
    Generate a weekly report for a project
    
    Args:
        project_id: The project ID
        start_date: Report start date in YYYY-MM-DD format
        end_date: Report end date in YYYY-MM-DD format
        
    Returns:
        ReportResponse: The generated report
    """
    try:
        logger.info(f"Generating weekly report for project {project_id} from {start_date} to {end_date}")
        
        # Validate date format
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
        
        # Generate report using the adapter
        report = adapter.generate_weekly_report(project_id, start_date, end_date)
        
        logger.info(f"Successfully generated weekly report: {report.title}")
        
        return ReportResponse(
            id=report.id,
            title=report.title,
            content=report.content,
            generated_at=report.generated_at,
            project_id=project_id,
            report_type="weekly"
        )
        
    except HTTPException:
        raise
    except NotFoundError as e:
        logger.warning(f"Project not found for report: {e}")
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate weekly report: {str(e)}")


@router.post(
    "/{project_id}/reports/monthly",
    response_model=ReportResponse,
    summary="Generate monthly report",
    description="Generate a monthly report for the specified project"
)
def generate_monthly_report(
    project_id: str = Path(..., description="The ID of the project"),
    year: int = Query(..., description="Year for the report"),
    month: int = Query(..., ge=1, le=12, description="Month for the report (1-12)"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> ReportResponse:
    """
    Generate a monthly report for a project
    
    Args:
        project_id: The project ID
        year: Report year
        month: Report month (1-12)
        
    Returns:
        ReportResponse: The generated report
    """
    try:
        logger.info(f"Generating monthly report for project {project_id} for {year}-{month:02d}")
        
        # Generate report using the adapter
        report = adapter.generate_monthly_report(project_id, year, month)
        
        logger.info(f"Successfully generated monthly report: {report.title}")
        
        return ReportResponse(
            id=report.id,
            title=report.title,
            content=report.content,
            generated_at=report.generated_at,
            project_id=project_id,
            report_type="monthly"
        )
        
    except NotFoundError as e:
        logger.warning(f"Project not found for report: {e}")
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to generate monthly report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate monthly report: {str(e)}")


@router.post(
    "/{project_id}/reports/risk-assessment",
    response_model=ReportResponse,
    summary="Generate risk assessment",
    description="Generate a risk assessment report for the specified project"
)
def assess_project_risks(
    project_id: str = Path(..., description="The ID of the project"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> ReportResponse:
    """
    Generate a risk assessment report for a project
    
    Args:
        project_id: The project ID
        
    Returns:
        ReportResponse: The generated risk assessment report
    """
    try:
        logger.info(f"Generating risk assessment for project {project_id}")
        
        # Generate risk assessment using the adapter
        report = adapter.assess_project_risks(project_id)
        
        logger.info(f"Successfully generated risk assessment: {report.title}")
        
        return ReportResponse(
            id=report.id,
            title=report.title,
            content=report.content,
            generated_at=report.generated_at,
            project_id=project_id,
            report_type="risk_assessment"
        )
        
    except NotFoundError as e:
        logger.warning(f"Project not found for risk assessment: {e}")
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to generate risk assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate risk assessment: {str(e)}")


# Health check endpoint for projects service
@router.get(
    "/health",
    summary="Projects service health check",
    description="Check the health of the projects service"
)
def projects_health_check(
    adapter: SyncAsyncAdapter = Depends(get_basic_adapter)
) -> Dict[str, Any]:
    """
    Check the health of the projects service
    
    Returns:
        Dict: Health status information
    """
    try:
        # Test basic connectivity
        projects = adapter.get_projects()
        project_count = len(projects)
        
        return {
            "status": "healthy",
            "service": "projects",
            "project_count": project_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Projects service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "projects",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }