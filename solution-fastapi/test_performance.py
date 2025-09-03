#!/usr/bin/env python3
"""
Performance Test Script for FastAPI MCP Server

This script tests the performance optimizations including connection pooling,
caching, rate limiting, and middleware functionality.
"""
import asyncio
import httpx
import time
import json
from typing import Dict, List, Any


async def test_connection_pool():
    """Test connection pool functionality"""
    print("Testing connection pool...")
    
    try:
        from app.core.connection_pool import get_connection_pool_manager, ConnectionType
        
        manager = get_connection_pool_manager()
        await manager.initialize()
        
        # Test HTTP connection pool
        async with manager.acquire_connection(ConnectionType.HTTP) as http_client:
            response = await http_client.get("https://httpbin.org/get")
            print(f"HTTP pool test: {response.status_code}")
        
        # Test health checks
        health_status = await manager.health_check_all()
        print(f"Health status: {health_status}")
        
        # Test statistics
        stats = manager.get_all_stats()
        print(f"Pool statistics: {stats}")
        
        await manager.close_all()
        print("Connection pool test passed!")
        
    except Exception as e:
        print(f"Connection pool test failed: {e}")
        raise


async def test_performance_endpoints():
    """Test performance monitoring endpoints"""
    print("Testing performance endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        response = await client.get("http://localhost:8000/")
        print(f"Root endpoint: {response.status_code}")
        
        # Test health endpoint
        response = await client.get("http://localhost:8000/health")
        print(f"Health endpoint: {response.status_code}")
        
        # Test performance endpoint
        response = await client.get("http://localhost:8000/performance")
        print(f"Performance endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Performance stats retrieved successfully")


async def test_rate_limiting():
    """Test rate limiting functionality"""
    print("Testing rate limiting...")
    
    async with httpx.AsyncClient() as client:
        requests = []
        
        # Make multiple rapid requests to trigger rate limiting
        for i in range(10):
            requests.append(client.get("http://localhost:8000/"))
        
        responses = await asyncio.gather(*requests, return_exceptions=True)
        
        rate_limited = 0
        successful = 0
        
        for response in responses:
            if isinstance(response, Exception):
                continue
            if response.status_code == 429:
                rate_limited += 1
            elif response.status_code == 200:
                successful += 1
        
        print(f"Successful: {successful}, Rate limited: {rate_limited}")


async def main():
    """Run all performance tests"""
    print("Starting performance tests...")
    
    try:
        await test_connection_pool()
        await asyncio.sleep(1)  # Wait for server to start
        
        await test_performance_endpoints()
        await test_rate_limiting()
        
        print("All performance tests completed successfully!")
        
    except Exception as e:
        print(f"Performance tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
