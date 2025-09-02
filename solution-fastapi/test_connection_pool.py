#!/usr/bin/env python3
"""
Connection Pool Performance Test

This script tests the connection pool optimizations from the recent commit.
"""
import asyncio
import time
from app.core.connection_pool import get_connection_pool_manager, ConnectionType


async def test_connection_pool_performance():
    """Test connection pool performance optimizations"""
    print("Testing connection pool performance optimizations...")
    
    manager = get_connection_pool_manager()
    
    # Test initialization
    start_time = time.time()
    await manager.initialize()
    init_time = time.time() - start_time
    print(f"Pool initialization time: {init_time:.3f}s")
    
    # Test acquiring connections
    connection_times = []
    for i in range(5):
        start_time = time.time()
        async with manager.acquire_connection(ConnectionType.HTTP) as client:
            acquire_time = time.time() - start_time
            connection_times.append(acquire_time)
            print(f"Connection {i+1} acquired in {acquire_time:.3f}s")
    
    avg_acquire_time = sum(connection_times) / len(connection_times)
    print(f"Average connection acquire time: {avg_acquire_time:.3f}s")
    
    # Test health checks
    start_time = time.time()
    health_status = await manager.health_check_all()
    health_time = time.time() - start_time
    print(f"Health check time: {health_time:.3f}s")
    print(f"Health status: {health_status}")
    
    # Test statistics
    stats = manager.get_all_stats()
    print("\nConnection pool statistics:")
    for pool_type, pool_stats in stats.items():
        print(f"{pool_type.value}:")
        print(f"  Total connections: {pool_stats.total_connections}")
        print(f"  Active connections: {pool_stats.active_connections}")
        print(f"  Idle connections: {pool_stats.idle_connections}")
        print(f"  Total requests: {pool_stats.total_requests}")
        print(f"  Successful requests: {pool_stats.successful_requests}")
        print(f"  Failed requests: {pool_stats.failed_requests}")
        print(f"  Avg response time: {pool_stats.avg_response_time_ms:.2f}ms")
        print(f"  P95 response time: {pool_stats.p95_response_time_ms:.2f}ms")
        print(f"  P99 response time: {pool_stats.p99_response_time_ms:.2f}ms")
    
    # Test cleanup
    start_time = time.time()
    await manager.close_all()
    cleanup_time = time.time() - start_time
    print(f"Cleanup time: {cleanup_time:.3f}s")
    
    print("\nConnection pool performance test completed successfully!")
    
    # Performance metrics summary
    print("\n=== PERFORMANCE SUMMARY ===")
    print(f"Initialization time: {init_time:.3f}s")
    print(f"Average acquire time: {avg_acquire_time:.3f}s")
    print(f"Health check time: {health_time:.3f}s")
    print(f"Cleanup time: {cleanup_time:.3f}s")
    
    # Check if optimizations are working
    if avg_acquire_time < 0.1:  # Should be very fast with connection pooling
        print("✅ Connection pooling optimizations are working effectively!")
    else:
        print("⚠️  Connection pooling may need further optimization")


async def main():
    """Run connection pool performance test"""
    try:
        await test_connection_pool_performance()
    except Exception as e:
        print(f"Performance test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())