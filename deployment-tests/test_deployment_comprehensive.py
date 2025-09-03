#!/usr/bin/env python3
"""
Comprehensive deployment testing suite for all OpenProject MCP solutions.
Tests Docker builds, health checks, API endpoints, and cross-solution compatibility.
"""

import pytest
import requests
import time
import subprocess
import docker
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentTester:
    """Comprehensive deployment testing for all solutions."""
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.containers = {}
        self.base_ports = {
            'solution-http': 8010,
            'solution-fastapi': 8020,
            'solution-fastmcp': 8030,
            'solution-typescript': 8040
        }
        
    def setup_method(self):
        """Setup before each test method."""
        self.cleanup_containers()
        
    def teardown_method(self):
        """Cleanup after each test method."""
        self.cleanup_containers()
        
    def cleanup_containers(self):
        """Clean up all running containers."""
        for name, container in self.containers.items():
            try:
                container.stop()
                container.remove()
                logger.info(f"Cleaned up container: {name}")
            except Exception as e:
                logger.warning(f"Failed to cleanup container {name}: {e}")
        self.containers.clear()
        
    def build_solution(self, solution_name: str) -> docker.models.images.Image:
        """Build Docker image for a solution."""
        logger.info(f"Building Docker image for {solution_name}")
        
        try:
            image, build_logs = self.docker_client.images.build(
                path=solution_name,
                tag=f"openproject-{solution_name}-test",
                rm=True
            )
            
            # Log build progress
            for chunk in build_logs:
                if 'stream' in chunk:
                    logger.info(f"Build: {chunk['stream'].strip()}")
                    
            logger.info(f"Successfully built image for {solution_name}")
            return image
            
        except Exception as e:
            logger.error(f"Failed to build {solution_name}: {e}")
            raise
            
    def run_container(self, solution_name: str, image: docker.models.images.Image) -> docker.models.containers.Container:
        """Run a container for the given solution."""
        port = self.base_ports[solution_name]
        container_name = f"{solution_name}-test"
        
        logger.info(f"Starting container {container_name} on port {port}")
        
        try:
            container = self.docker_client.containers.run(
                image.id,
                name=container_name,
                ports={f'{port}/tcp': port},
                detach=True,
                environment={
                    'OPENPROJECT_URL': 'https://test.openproject.com',
                    'OPENPROJECT_API_KEY': 'test-key',
                    'LOG_LEVEL': 'INFO'
                }
            )
            
            self.containers[solution_name] = container
            logger.info(f"Container {container_name} started successfully")
            return container
            
        except Exception as e:
            logger.error(f"Failed to start container {container_name}: {e}")
            raise
            
    def wait_for_health(self, solution_name: str, timeout: int = 60) -> bool:
        """Wait for service to become healthy."""
        port = self.base_ports[solution_name]
        url = f"http://localhost:{port}/health"
        
        logger.info(f"Waiting for {solution_name} to be healthy at {url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"{solution_name} is healthy")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            
        logger.error(f"{solution_name} did not become healthy within {timeout} seconds")
        return False
        
    def test_api_endpoints(self, solution_name: str) -> Dict[str, bool]:
        """Test basic API endpoints for a solution."""
        port = self.base_ports[solution_name]
        base_url = f"http://localhost:{port}"
        
        test_results = {}
        
        # Test endpoints based on solution type
        endpoints = []
        
        if solution_name == 'solution-http':
            endpoints = [
                ('/health', 'GET'),
                ('/api/projects', 'GET'),
                ('/api/users', 'GET'),
                ('/api/work-packages', 'GET')
            ]
        elif solution_name == 'solution-fastapi':
            endpoints = [
                ('/health', 'GET'),
                ('/docs', 'GET'),
                ('/api/projects', 'GET'),
                ('/api/mcp', 'POST')
            ]
        elif solution_name == 'solution-typescript':
            endpoints = [
                ('/health', 'GET'),
                ('/api/projects', 'GET'),
                ('/api/users', 'GET'),
                ('/api/mcp/tools', 'GET')
            ]
            
        for endpoint, method in endpoints:
            url = base_url + endpoint
            try:
                if method == 'GET':
                    response = requests.get(url, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, json={'test': 'data'}, timeout=10)
                    
                test_results[endpoint] = response.status_code < 500
                logger.info(f"{solution_name} {method} {endpoint}: {response.status_code}")
                
            except Exception as e:
                test_results[endpoint] = False
                logger.error(f"{solution_name} {method} {endpoint} failed: {e}")
                
        return test_results
        
    def test_resource_usage(self, solution_name: str) -> Dict[str, float]:
        """Test resource usage for a solution."""
        container = self.containers.get(solution_name)
        if not container:
            return {}
            
        try:
            stats = container.stats(stream=False)
            
            # Calculate CPU usage
            cpu_usage = 0.0
            try:
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            except (KeyError, ZeroDivisionError):
                pass
                
            # Get memory usage
            memory_usage = stats['memory_stats'].get('usage', 0) / (1024 * 1024)  # MB
            
            # Get network I/O
            network_stats = stats.get('networks', {}).get('eth0', {})
            rx_bytes = network_stats.get('rx_bytes', 0)
            tx_bytes = network_stats.get('tx_bytes', 0)
            
            return {
                'cpu_percent': cpu_usage,
                'memory_mb': memory_usage,
                'network_rx_bytes': rx_bytes,
                'network_tx_bytes': tx_bytes
            }
            
        except Exception as e:
            logger.error(f"Failed to get resource usage for {solution_name}: {e}")
            return {}
            
    def test_concurrent_requests(self, solution_name: str, num_requests: int = 10) -> Dict[str, float]:
        """Test concurrent request handling."""
        port = self.base_ports[solution_name]
        url = f"http://localhost:{port}/health"
        
        async def make_request(session):
            try:
                async with session.get(url, timeout=10) as response:
                    return response.status, time.time()
            except Exception as e:
                return 500, time.time()
                
        async def run_concurrent_tests():
            async with aiohttp.ClientSession() as session:
                tasks = [make_request(session) for _ in range(num_requests)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return results
                
        start_time = time.time()
        results = asyncio.run(run_concurrent_tests())
        end_time = time.time()
        
        # Analyze results
        successful_requests = sum(1 for r in results if isinstance(r, tuple) and r[0] == 200)
        response_times = [r[1] - start_time for r in results if isinstance(r, tuple)]
        
        return {
            'total_requests': num_requests,
            'successful_requests': successful_requests,
            'success_rate': successful_requests / num_requests,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'total_time': end_time - start_time
        }
        
    def test_cross_solution_compatibility(self) -> Dict[str, bool]:
        """Test compatibility between different solutions."""
        compatibility_results = {}
        
        # Test if all solutions can handle the same requests
        common_endpoints = ['/health', '/api/projects']
        
        for endpoint in common_endpoints:
            responses = {}
            for solution_name in self.containers:
                port = self.base_ports[solution_name]
                url = f"http://localhost:{port}{endpoint}"
                
                try:
                    response = requests.get(url, timeout=10)
                    responses[solution_name] = response.status_code
                except Exception as e:
                    responses[solution_name] = f"Error: {e}"
                    
            # Check if all responses are successful
            all_success = all(
                isinstance(status, int) and 200 <= status < 300 
                for status in responses.values()
            )
            
            compatibility_results[endpoint] = all_success
            
            if not all_success:
                logger.warning(f"Compatibility issue for {endpoint}: {responses}")
                
        return compatibility_results

@pytest.mark.deployment
class TestSolutionDeployment:
    """Test deployment for all solutions."""
    
    @pytest.fixture(scope="class")
    def tester(self):
        """Create deployment tester instance."""
        return DeploymentTester()
        
    @pytest.fixture(scope="class")
    def deployed_solutions(self, tester):
        """Deploy all solutions for testing."""
        deployed = {}
        
        solutions = ['solution-http', 'solution-fastapi', 'solution-typescript']
        
        for solution in solutions:
            try:
                # Build image
                image = tester.build_solution(solution)
                
                # Run container
                container = tester.run_container(solution, image)
                
                # Wait for health
                if tester.wait_for_health(solution):
                    deployed[solution] = container
                else:
                    pytest.fail(f"{solution} failed to become healthy")
                    
            except Exception as e:
                pytest.fail(f"Failed to deploy {solution}: {e}")
                
        yield deployed
        
        # Cleanup
        tester.cleanup_containers()
        
    def test_all_solutions_deployable(self, deployed_solutions):
        """Test that all solutions can be deployed."""
        assert len(deployed_solutions) >= 2, "At least 2 solutions should be deployable"
        
    @pytest.mark.parametrize("solution_name", ['solution-http', 'solution-fastapi', 'solution-typescript'])
    def test_individual_solution_deployment(self, tester, solution_name):
        """Test individual solution deployment."""
        try:
            # Build image
            image = tester.build_solution(solution_name)
            
            # Run container
            container = tester.run_container(solution_name, image)
            
            # Wait for health
            assert tester.wait_for_health(solution_name), f"{solution_name} should become healthy"
            
            # Test API endpoints
            api_results = tester.test_api_endpoints(solution_name)
            assert any(api_results.values()), f"{solution_name} should have at least one working endpoint"
            
            # Test resource usage
            resource_stats = tester.test_resource_usage(solution_name)
            assert resource_stats.get('memory_mb', 0) > 0, f"{solution_name} should use some memory"
            
        finally:
            tester.cleanup_containers()
            
    def test_api_compatibility(self, deployed_solutions):
        """Test API compatibility across solutions."""
        compatibility = tester.test_cross_solution_compatibility()
        
        # At least health endpoint should be compatible
        assert compatibility.get('/health', False), "Health endpoint should be compatible across solutions"
        
    def test_concurrent_request_handling(self, deployed_solutions):
        """Test concurrent request handling."""
        for solution_name in deployed_solutions:
            results = tester.test_concurrent_requests(solution_name, num_requests=5)
            
            # Should handle at least 80% of concurrent requests successfully
            assert results['success_rate'] >= 0.8, \
                f"{solution_name} should handle at least 80% of concurrent requests successfully"
                
    def test_resource_usage_limits(self, deployed_solutions):
        """Test that resource usage is within reasonable limits."""
        for solution_name in deployed_solutions:
            stats = tester.test_resource_usage(solution_name)
            
            # Memory usage should be reasonable (< 500MB for basic services)
            assert stats.get('memory_mb', 0) < 500, \
                f"{solution_name} memory usage should be < 500MB"
                
            # CPU usage should be reasonable (< 50% idle)
            assert stats.get('cpu_percent', 0) < 50, \
                f"{solution_name} CPU usage should be < 50%"

@pytest.mark.performance
class TestDeploymentPerformance:
    """Performance tests for deployed solutions."""
    
    @pytest.fixture
    def performance_tester(self):
        tester = DeploymentTester()
        yield tester
        tester.cleanup_containers()
        
    def test_startup_time(self, performance_tester):
        """Test solution startup time."""
        solution_name = 'solution-http'  # Test with HTTP solution
        
        start_time = time.time()
        
        # Build and run
        image = performance_tester.build_solution(solution_name)
        container = performance_tester.run_container(solution_name, image)
        
        # Wait for health
        healthy = performance_tester.wait_for_health(solution_name, timeout=120)
        
        startup_time = time.time() - start_time
        
        assert healthy, f"{solution_name} should become healthy"
        assert startup_time < 60, f"{solution_name} should start within 60 seconds"
        
        logger.info(f"{solution_name} startup time: {startup_time:.2f} seconds")
        
    def test_memory_efficiency(self, performance_tester):
        """Test memory efficiency across multiple requests."""
        solution_name = 'solution-fastapi'
        
        # Deploy solution
        image = performance_tester.build_solution(solution_name)
        container = performance_tester.run_container(solution_name, image)
        
        assert performance_tester.wait_for_health(solution_name)
        
        # Make multiple requests
        port = performance_tester.base_ports[solution_name]
        url = f"http://localhost:{port}/health"
        
        for _ in range(50):
            response = requests.get(url, timeout=10)
            assert response.status_code == 200
            
        # Check memory after load
        stats = performance_tester.test_resource_usage(solution_name)
        
        # Memory should not grow excessively
        assert stats.get('memory_mb', 0) < 300, \
            f"{solution_name} memory usage should remain reasonable after load"

if __name__ == "__main__":
    # Run deployment tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--deployment-tests",
        "--html=deployment-test-report.html"
    ])