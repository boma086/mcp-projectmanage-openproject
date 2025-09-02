#!/usr/bin/env python3
"""
Local Performance Test Script for FastAPI MCP Server

This script tests the performance of local server endpoints including connection pooling,
rate limiting, and middleware functionality.
"""
import asyncio
import httpx
import time
import json
from typing import Dict, List, Any


async def test_local_endpoints():
    """Test local server endpoints performance"""
    print("Testing local server endpoints...")
    
    async with httpx.AsyncClient() as client:
        # Test root endpoint
        start_time = time.time()
        response = await client.get("http://localhost:8000/")
        root_time = time.time() - start_time
        print(f"Root endpoint: {response.status_code} ({root_time:.3f}s)")
        
        # Test health endpoint
        start_time = time.time()
        response = await client.get("http://localhost:8000/health")
        health_time = time.time() - start_time
        print(f"Health endpoint: {response.status_code} ({health_time:.3f}s)")
        
        # Test performance endpoint
        start_time = time.time()
        response = await client.get("http://localhost:8000/performance")
        perf_time = time.time() - start_time
        print(f"Performance endpoint: {response.status_code} ({perf_time:.3f}s)")
        
        if response.status_code == 200:
            data = response.json()
            print("Performance stats retrieved successfully")
            print(f"Connection pools: {list(data.get('connection_pools', {}).keys())}")
            print(f"WebSocket enabled: {data.get('websocket', {}).get('enabled', False)}")


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
                print(f"Request failed: {response}")
                continue
            if response.status_code == 429:
                rate_limited += 1
            elif response.status_code == 200:
                successful += 1
        
        print(f"Successful: {successful}, Rate limited: {rate_limited}")


async def test_connection_pool_stats():
    """Test connection pool statistics"""
    print("Testing connection pool statistics...")
    
    try:
        from app.core.connection_pool import get_connection_pool_manager
        
        manager = get_connection_pool_manager()
        stats = manager.get_all_stats()
        
        print("Connection pool statistics:")
        for pool_type, pool_stats in stats.items():
            print(f"  {pool_type.value}:")
            print(f"    Total connections: {pool_stats.total_connections}")
            print(f"    Active connections: {pool_stats.active_connections}")
            print(f"    Total requests: {pool_stats.total_requests}")
            print(f"    Avg response time: {pool_stats.avg_response_time_ms:.2f}ms")
        
    except Exception as e:
        print(f"Connection pool stats test failed: {e}")


async def main():
    """Run all performance tests"""
    print("Starting local performance tests...")
    
    try:
        await test_local_endpoints()
        await asyncio.sleep(1)  # Wait between tests
        
        await test_rate_limiting()
        await asyncio.sleep(1)  # Wait between tests
        
        await test_connection_pool_stats()
        
        print("All local performance tests completed successfully!")
        
    except Exception as e:
        print(f"Performance tests failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())