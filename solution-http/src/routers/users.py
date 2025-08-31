"""
Users Router - HTTP Solution
Synchronous REST API endpoints for OpenProject user operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import dependencies and core models
from ..dependencies import SyncAsyncAdapter, validate_openproject_connection, get_basic_adapter
from mcp_core.domain.models import User
from mcp_core.shared.exceptions import OpenProjectError, NotFoundError, AuthenticationError
from mcp_core.shared.logger import get_logger

logger = get_logger("http.routers.users")

# Create router instance
router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={
        404: {"description": "User not found"},
        401: {"description": "Authentication failed"},
        503: {"description": "OpenProject service unavailable"}
    }
)

# Response models
class UserResponse(BaseModel):
    """User response model"""
    id: str
    name: str
    email: Optional[str] = None
    login: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: str
    language: Optional[str] = None
    admin: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserListResponse(BaseModel):
    """User list response model"""
    users: List[UserResponse]
    total: int

class UserSummaryResponse(BaseModel):
    """User summary response model for lightweight operations"""
    id: str
    name: str
    email: Optional[str] = None
    status: str

# User Read Endpoints

@router.get(
    "/",
    response_model=UserListResponse,
    summary="Get all users",
    description="Retrieve a list of all users from OpenProject"
)
def get_users(
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    status_filter: Optional[str] = Query(None, description="Filter by user status (active, locked, etc.)"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> UserListResponse:
    """
    Get all users with pagination and optional status filtering
    
    Args:
        offset: Number of users to skip for pagination
        limit: Maximum number of users to return
        status_filter: Optional status filter
        
    Returns:
        UserListResponse: List of users with total count
    """
    try:
        logger.info(f"Fetching users with offset={offset}, limit={limit}, status_filter={status_filter}")
        
        # Get all users using the adapter
        users = adapter.get_users()
        
        # Apply status filter if provided
        if status_filter:
            users = [user for user in users if user.status.lower() == status_filter.lower()]
        
        # Apply pagination
        total = len(users)
        paginated_users = users[offset:offset + limit]
        
        # Convert to response models
        user_responses = [
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                login=getattr(user, 'login', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None),
                status=user.status,
                language=getattr(user, 'language', None),
                admin=getattr(user, 'admin', False),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in paginated_users
        ]
        
        logger.info(f"Successfully retrieved {len(user_responses)} users out of {total}")
        
        return UserListResponse(
            users=user_responses,
            total=total
        )
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID"
)
def get_user(
    user_id: str = Path(..., description="The ID of the user to retrieve"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> UserResponse:
    """
    Get a specific user by ID
    
    Args:
        user_id: The user ID to retrieve
        
    Returns:
        UserResponse: The requested user
    """
    try:
        logger.info(f"Fetching user with ID: {user_id}")
        
        # Get user using the adapter
        user = adapter.get_user(user_id)
        
        if user is None:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
        
        logger.info(f"Successfully retrieved user: {user.name}")
        
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            login=getattr(user, 'login', None),
            first_name=getattr(user, 'first_name', None),
            last_name=getattr(user, 'last_name', None),
            status=user.status,
            language=getattr(user, 'language', None),
            admin=getattr(user, 'admin', False),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except NotFoundError as e:
        logger.warning(f"User not found: {e}")
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")


# User Summary Endpoints (Lightweight operations)

@router.get(
    "/summary",
    response_model=List[UserSummaryResponse],
    summary="Get users summary",
    description="Retrieve a lightweight summary of all users (for dropdowns, selectors, etc.)"
)
def get_users_summary(
    active_only: bool = Query(True, description="Return only active users"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> List[UserSummaryResponse]:
    """
    Get a lightweight summary of users
    
    This endpoint is optimized for use in dropdowns, user selectors, and other
    contexts where only basic user information is needed.
    
    Args:
        active_only: If True, return only active users
        
    Returns:
        List[UserSummaryResponse]: List of user summaries
    """
    try:
        logger.info(f"Fetching user summaries with active_only={active_only}")
        
        # Get all users using the adapter
        users = adapter.get_users()
        
        # Filter active users if requested
        if active_only:
            users = [user for user in users if user.status.lower() == 'active']
        
        # Convert to summary response models
        user_summaries = [
            UserSummaryResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                status=user.status
            )
            for user in users
        ]
        
        logger.info(f"Successfully retrieved {len(user_summaries)} user summaries")
        
        return user_summaries
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error fetching user summaries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch user summaries: {str(e)}")


# User Search Endpoints

@router.get(
    "/search",
    response_model=List[UserResponse],
    summary="Search users",
    description="Search users by name, email, or login"
)
def search_users(
    query: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results to return"),
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> List[UserResponse]:
    """
    Search users by name, email, or login
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List[UserResponse]: List of matching users
    """
    try:
        logger.info(f"Searching users with query: {query}")
        
        # Get all users using the adapter
        users = adapter.get_users()
        
        # Perform case-insensitive search across multiple fields
        query_lower = query.lower()
        matching_users = []
        
        for user in users:
            # Search in name, email, and login fields
            searchable_fields = [
                user.name.lower() if user.name else "",
                user.email.lower() if user.email else "",
                getattr(user, 'login', '').lower()
            ]
            
            if any(query_lower in field for field in searchable_fields):
                matching_users.append(user)
                
                # Limit results
                if len(matching_users) >= limit:
                    break
        
        # Convert to response models
        user_responses = [
            UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                login=getattr(user, 'login', None),
                first_name=getattr(user, 'first_name', None),
                last_name=getattr(user, 'last_name', None),
                status=user.status,
                language=getattr(user, 'language', None),
                admin=getattr(user, 'admin', False),
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in matching_users
        ]
        
        logger.info(f"Found {len(user_responses)} users matching query: {query}")
        
        return user_responses
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error searching users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")


# User Statistics Endpoints

@router.get(
    "/stats",
    summary="Get user statistics",
    description="Get statistical information about users in the system"
)
def get_user_statistics(
    adapter: SyncAsyncAdapter = Depends(validate_openproject_connection)
) -> Dict[str, Any]:
    """
    Get statistical information about users
    
    Returns:
        Dict: User statistics including counts by status, admin users, etc.
    """
    try:
        logger.info("Fetching user statistics")
        
        # Get all users using the adapter
        users = adapter.get_users()
        
        # Calculate statistics
        total_users = len(users)
        status_counts = {}
        admin_count = 0
        
        for user in users:
            # Count by status
            status = user.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count admins
            if getattr(user, 'admin', False):
                admin_count += 1
        
        statistics = {
            "total_users": total_users,
            "status_breakdown": status_counts,
            "admin_users": admin_count,
            "regular_users": total_users - admin_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Successfully calculated user statistics: {total_users} total users")
        
        return statistics
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="OpenProject authentication failed")
    except OpenProjectError as e:
        logger.error(f"OpenProject error: {e}")
        raise HTTPException(status_code=503, detail=f"OpenProject service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error calculating user statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate user statistics: {str(e)}")


# Health check endpoint for users service
@router.get(
    "/health",
    summary="Users service health check",
    description="Check the health of the users service"
)
def users_health_check(
    adapter: SyncAsyncAdapter = Depends(get_basic_adapter)
) -> Dict[str, Any]:
    """
    Check the health of the users service
    
    Returns:
        Dict: Health status information
    """
    try:
        # Test basic connectivity
        users = adapter.get_users()
        user_count = len(users)
        
        return {
            "status": "healthy",
            "service": "users",
            "user_count": user_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Users service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "users",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }