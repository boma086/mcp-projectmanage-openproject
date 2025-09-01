#!/usr/bin/env python3
"""
Test script to verify router functionality without loading full application
"""

import os
import sys
from pathlib import Path

# Add the src directory and parent directories to Python path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_router_imports():
    """Test that all routers can be imported successfully"""
    print("Testing router imports...")
    
    try:
        from routers import projects_router, work_packages_router, users_router
        print("✓ All routers imported successfully")
        
        # Test that routers have the expected attributes
        assert hasattr(projects_router, 'router'), "Projects router missing router attribute"
        assert hasattr(work_packages_router, 'router'), "Work packages router missing router attribute"
        assert hasattr(users_router, 'router'), "Users router missing router attribute"
        
        print("✓ All routers have router attribute")
        
        # Test that routers have endpoints
        projects_routes = [route.path for route in projects_router.router.routes]
        work_packages_routes = [route.path for route in work_packages_router.router.routes]
        users_routes = [route.path for route in users_router.router.routes]
        
        print(f"✓ Projects router has {len(projects_routes)} routes")
        print(f"✓ Work packages router has {len(work_packages_routes)} routes")
        print(f"✓ Users router has {len(users_routes)} routes")
        
        # Check for some key endpoints
        expected_projects_endpoints = [
            "/api/projects/",
            "/api/projects/{project_id}",
            "/api/projects/{project_id}/reports/weekly"
        ]
        
        for endpoint in expected_projects_endpoints:
            if endpoint in projects_routes:
                print(f"✓ Projects endpoint found: {endpoint}")
            else:
                print(f"⚠ Projects endpoint missing: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"✗ Router import test failed: {e}")
        return False

def test_dependencies():
    """Test that dependencies can be imported"""
    print("\nTesting dependencies...")
    
    try:
        from dependencies import SyncAsyncAdapter, get_openproject_adapter
        print("✓ Dependencies imported successfully")
        return True
        
    except Exception as e:
        print(f"✗ Dependencies import failed: {e}")
        return False

if __name__ == "__main__":
    print("Running HTTP Solution Router Tests")
    print("=" * 50)
    
    # Set minimal environment variables to avoid config validation errors
    os.environ["OPENPROJECT_URL"] = "http://localhost:8090"
    os.environ["OPENPROJECT_API_KEY"] = "valid-api-key-with-more-than-10-chars"
    
    success = True
    success &= test_router_imports()
    success &= test_dependencies()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ All tests passed!")
        sys.exit(0)
    else:
        print("✗ Some tests failed!")
        sys.exit(1)