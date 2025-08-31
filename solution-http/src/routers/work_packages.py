"""
Work Packages Router - HTTP Solution
Synchronous REST API endpoints for OpenProject work package operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import dependencies and core models
from ..dependencies import SyncAsyncAdapter, validate_openproject_connection, get_basic_adapter
from mcp_core.domain.models import WorkPackage
from mcp_core.shared.exceptions import OpenProjectError, NotFoundError, AuthenticationError, ValidationError
from mcp_core.shared.logger import get_logger

logger = get_logger("http.routers.work_packages")

# Create router instance
router = APIRouter(
    prefix="/api/work-packages",
    tags=["work_packages"],
    responses={
        404: {"description": "Work package not found"},
        401: {"description": "Authentication failed"},
        503: {"description": "OpenProject service unavailable"}
    }
)

# Request and Response models
class WorkPackageResponse(BaseModel):
    """Work package response model"""
    id: str
    subject: str
    description: Optional[str] = None
    status: str
    type: str
    priority: str
    assigned_to: Optional[str] = None
    progress: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    project_id: Optional[str] = None

class WorkPackageListResponse(BaseModel):
    """Work package list response model"""
    work_packages: List[WorkPackageResponse]
    total: int
    project_id: Optional[str] = None

class WorkPackageCreateRequest(BaseModel):
    """Work package creation request model"""
    subject: str = Field(..., min_length=1, max_length=255, description="Work package subject")
    description: Optional[str] = Field(None, description="Work package description")
    type: str = Field(..., description="Work package type")
    priority: Optional[str] = Field("Normal", description="Work package priority")
    assigned_to: Optional[str] = Field(None, description="Assignee user ID")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")
    project_id: str = Field(..., description="Project ID this work package belongs to")

class WorkPackageUpdateRequest(BaseModel):
    """Work package update request model"""
    subject: Optional[str] = Field(None, min_length=1, max_length=255, description="Work package subject")
    description: Optional[str] = Field(None, description="Work package description")
    status: Optional[str] = Field(None, description="Work package status")
    type: Optional[str] = Field(None, description="Work package type")
    priority: Optional[str] = Field(None, description="Work package priority")
    assigned_to: Optional[str] = Field(None, description="Assignee user ID")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Work package progress (0-100)")
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    due_date: Optional[str] = Field(None, description="Due date in YYYY-MM-DD format")

# Work Package CRUD Endpoints

@router.get(
    "/",
    response_model=WorkPackageListResponse,
    summary="Get all work packages",
    description="Retrieve a list of all work packages, optionally filtered by project"
)
def get_work_packages(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    offset: int = Query(0, ge=0, description="Number of work packages to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of work packages to return"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> WorkPackageListResponse:
    """
    Get all work packages with optional project filtering and pagination
    
    Args:
        project_id: Optional project ID to filter work packages
        offset: Number of work packages to skip for pagination
        limit: Maximum number of work packages to return
        
    Returns:
        WorkPackageListResponse: List of work packages with total count
    """
    try:
        logger.info(f"Fetching work packages for project_id={project_id}, offset={offset}, limit={limit}")
        
        # Get work packages using the adapter
        work_packages = adapter.get_work_packages(project_id)
        
        # Apply pagination
        total = len(work_packages)
        paginated_work_packages = work_packages[offset:offset + limit]
        
        # Convert to response models
        work_package_responses = [
            WorkPackageResponse(
                id=wp.id,
                subject=wp.subject,
                description=wp.description,
                status=wp.status,
                type=wp.type,
                priority=wp.priority,
                assigned_to=wp.assigned_to,
                progress=wp.progress,
                start_date=wp.start_date,
                due_date=wp.due_date,
                created_at=wp.created_at,
                updated_at=wp.updated_at,
                project_id=getattr(wp, 'project_id', None)
            )
            for wp in paginated_work_packages
        ]
        
        logger.info(f"Successfully retrieved {len(work_package_responses)} work packages out of {total}")
        
        return WorkPackageListResponse(
            work_packages=work_package_responses,
            total=total,
            project_id=project_id
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching work packages: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch work packages: {str(e)}")


@router.get(
    "/{work_package_id}",
    response_model=WorkPackageResponse,
    summary="Get work package by ID",
    description="Retrieve a specific work package by its ID"
)
def get_work_package(
    work_package_id: str = Path(..., description="The ID of the work package to retrieve"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> WorkPackageResponse:
    """
    Get a specific work package by ID
    
    Args:
        work_package_id: The work package ID to retrieve
        
    Returns:
        WorkPackageResponse: The requested work package
    """
    try:
        logger.info(f"Fetching work package with ID: {work_package_id}")
        
        # Get work package using the adapter
        work_package = adapter.get_work_package(work_package_id)
        
        if work_package is None:
            logger.warning(f"Work package not found: {work_package_id}")
            raise HTTPException(status_code=404, detail=f"Work package with ID {work_package_id} not found")
        
        logger.info(f"Successfully retrieved work package: {work_package.subject}")
        
        return WorkPackageResponse(
            id=work_package.id,
            subject=work_package.subject,
            description=work_package.description,
            status=work_package.status,
            type=work_package.type,
            priority=work_package.priority,
            assigned_to=work_package.assigned_to,
            progress=work_package.progress,
            start_date=work_package.start_date,
            due_date=work_package.due_date,
            created_at=work_package.created_at,
            updated_at=work_package.updated_at,
            project_id=getattr(work_package, 'project_id', None)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except NotFoundError as e:
        logger.warning(f"Work package not found: {e}")
        raise HTTPException(status_code=404, detail=f"Work package with ID {work_package_id} not found")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching work package {work_package_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch work package: {str(e)}")


@router.post(
    "/",
    response_model=WorkPackageResponse,
    status_code=201,
    summary="Create work package",
    description="Create a new work package in OpenProject"
)
def create_work_package(
    work_package_data: WorkPackageCreateRequest = Body(..., description="Work package creation data"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> WorkPackageResponse:
    """
    Create a new work package
    
    Args:
        work_package_data: The work package creation data
        
    Returns:
        WorkPackageResponse: The created work package
    """
    try:
        logger.info(f"Creating work package: {work_package_data.subject}")
        
        # Validate date formats if provided
        if work_package_data.start_date:
            try:
                datetime.strptime(work_package_data.start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if work_package_data.due_date:
            try:
                datetime.strptime(work_package_data.due_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_date format. Use YYYY-MM-DD")
        
        # Convert to dictionary for adapter
        work_package_dict = {
            "subject": work_package_data.subject,
            "description": work_package_data.description,
            "type": work_package_data.type,
            "priority": work_package_data.priority,
            "assigned_to": work_package_data.assigned_to,
            "start_date": work_package_data.start_date,
            "due_date": work_package_data.due_date,
            "project_id": work_package_data.project_id
        }
        
        # Remove None values
        work_package_dict = {k: v for k, v in work_package_dict.items() if v is not None}
        
        # Create work package using the adapter
        created_work_package = adapter.create_work_package(work_package_dict)
        
        logger.info(f"Successfully created work package: {created_work_package.id}")
        
        return WorkPackageResponse(
            id=created_work_package.id,
            subject=created_work_package.subject,
            description=created_work_package.description,
            status=created_work_package.status,
            type=created_work_package.type,
            priority=created_work_package.priority,
            assigned_to=created_work_package.assigned_to,
            progress=created_work_package.progress,
            start_date=created_work_package.start_date,
            due_date=created_work_package.due_date,
            created_at=created_work_package.created_at,
            updated_at=created_work_package.updated_at,
            project_id=getattr(created_work_package, 'project_id', None)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValidationError as e:
        logger.warning(f"Validation error creating work package: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create work package: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create work package: {str(e)}")


@router.put(
    "/{work_package_id}",
    response_model=WorkPackageResponse,
    summary="Update work package",
    description="Update an existing work package in OpenProject"
)
def update_work_package(
    work_package_id: str = Path(..., description="The ID of the work package to update"),
    work_package_data: WorkPackageUpdateRequest = Body(..., description="Work package update data"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> WorkPackageResponse:
    """
    Update an existing work package
    
    Args:
        work_package_id: The work package ID to update
        work_package_data: The work package update data
        
    Returns:
        WorkPackageResponse: The updated work package
    """
    try:
        logger.info(f"Updating work package: {work_package_id}")
        
        # Validate date formats if provided
        if work_package_data.start_date:
            try:
                datetime.strptime(work_package_data.start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        
        if work_package_data.due_date:
            try:
                datetime.strptime(work_package_data.due_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid due_date format. Use YYYY-MM-DD")
        
        # Convert to dictionary for adapter, excluding None values
        update_dict = {}
        for field, value in work_package_data.dict(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        # Update work package using the adapter
        updated_work_package = adapter.update_work_package(work_package_id, update_dict)
        
        logger.info(f"Successfully updated work package: {work_package_id}")
        
        return WorkPackageResponse(
            id=updated_work_package.id,
            subject=updated_work_package.subject,
            description=updated_work_package.description,
            status=updated_work_package.status,
            type=updated_work_package.type,
            priority=updated_work_package.priority,
            assigned_to=updated_work_package.assigned_to,
            progress=updated_work_package.progress,
            start_date=updated_work_package.start_date,
            due_date=updated_work_package.due_date,
            created_at=updated_work_package.created_at,
            updated_at=updated_work_package.updated_at,
            project_id=getattr(updated_work_package, 'project_id', None)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except NotFoundError as e:
        logger.warning(f"Work package not found for update: {e}")
        raise HTTPException(status_code=404, detail=f"Work package with ID {work_package_id} not found")
    except ValidationError as e:
        logger.warning(f"Validation error updating work package: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to update work package: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update work package: {str(e)}")


# Convenience endpoints for project-specific work packages

@router.get(
    "/projects/{project_id}",
    response_model=WorkPackageListResponse,
    summary="Get work packages by project",
    description="Retrieve work packages for a specific project"
)
def get_project_work_packages(
    project_id: str = Path(..., description="The ID of the project"),
    offset: int = Query(0, ge=0, description="Number of work packages to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of work packages to return"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> WorkPackageListResponse:
    """
    Get work packages for a specific project (convenience endpoint)
    
    This is equivalent to calling GET /api/work-packages?project_id={project_id}
    but provides a more RESTful URL structure.
    """
    return get_work_packages(project_id=project_id, offset=offset, limit=limit, adapter=adapter)


# Health check endpoint for work packages service
@router.get(
    "/health",
    summary="Work packages service health check",
    description="Check the health of the work packages service"
)
def work_packages_health_check(
    adapter: SyncAsyncAdapter = Depends(get_basic_adapter)
) -> Dict[str, Any]:
    """
    Check the health of the work packages service
    
    Returns:
        Dict: Health status information
    """
    try:
        # Test basic connectivity by fetching a limited set of work packages
        work_packages = adapter.get_work_packages()
        work_package_count = len(work_packages)
        
        return {
            "status": "healthy",
            "service": "work_packages",
            "work_package_count": work_package_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Work packages service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "work_packages",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }