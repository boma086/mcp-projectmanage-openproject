"""
Async dependency injection for FastAPI application

This module provides async dependencies for the OpenProject client with proper
connection pooling and lifecycle management.
"""
from typing import Optional
import httpx
from fastapi import Depends, HTTPException
from app.adapters.async_openproject_adapter import AsyncOpenProjectClient
from app.core.config import Settings, get_settings


# Global instances for connection pooling
_httpx_client: Optional[httpx.AsyncClient] = None
_openproject_client: Optional[AsyncOpenProjectClient] = None


def get_http_client_pool() -> httpx.AsyncClient:
    """
    Get or create the shared async HTTP client with connection pooling.
    
    This client should be used for all external HTTP requests to benefit
    from connection reuse and pooling optimizations.
    
    Returns:
        httpx.AsyncClient: Shared async HTTP client instance
    
    Raises:
        HTTPException: If the HTTP client cannot be initialized
    """
    global _httpx_client
    
    if _httpx_client is None:
        # Create HTTP client with optimized connection pooling
        _httpx_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=100,  # Maximum persistent connections
                max_connections=200,           # Maximum total connections
                keepalive_expiry=60            # Connection keepalive timeout (seconds)
            ),
            timeout=httpx.Timeout(
                connect=10.0,     # Connection timeout
                read=30.0,        # Read timeout
                write=10.0,       # Write timeout
                pool=5.0          # Pool acquisition timeout
            ),
            # Enable HTTP/2 for better performance if supported
            # http2=True  # Disabled for testing, requires h2 package
        )
    
    if _httpx_client.is_closed:
        raise HTTPException(status_code=503, detail="HTTP client pool is closed")
    
    return _httpx_client


async def get_openproject_client(
    settings: Settings = Depends(get_settings),
    http_client: httpx.AsyncClient = Depends(get_http_client_pool)
) -> AsyncOpenProjectClient:
    """
    Dependency to get the async OpenProject client with connection pooling.
    
    This dependency provides a fully initialized AsyncOpenProjectClient
    that uses the shared HTTP client pool for optimal performance.
    
    Args:
        settings: Application settings
        http_client: Shared async HTTP client
    
    Returns:
        AsyncOpenProjectClient: Initialized async OpenProject client
    
    Raises:
        HTTPException: If the client cannot be initialized
    """
    global _openproject_client
    
    if _openproject_client is None:
        try:
            _openproject_client = AsyncOpenProjectClient(
                url=settings.openproject_url,
                api_key=settings.openproject_api_key,
                http_client=http_client
            )
            await _openproject_client.initialize()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to initialize OpenProject client: {str(e)}"
            )
    
    return _openproject_client


async def close_http_client_pool():
    """
    Close the HTTP client pool and cleanup resources.
    
    This should be called during application shutdown.
    """
    global _httpx_client, _openproject_client
    
    if _httpx_client and not _httpx_client.is_closed:
        await _httpx_client.aclose()
        _httpx_client = None
    
    if _openproject_client:
        await _openproject_client.cleanup()
        _openproject_client = None