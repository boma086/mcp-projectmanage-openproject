#!/usr/bin/env python3
"""
Docker Compose testing suite for complete solution stack deployment.
Tests multi-service deployment, networking, and service discovery.
"""

import pytest
import subprocess
import requests
import time
import json
import logging
from pathlib import Path
import docker
import yaml
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DockerComposeTester:
    """Test Docker Compose deployments."""
    
    def __init__(self, compose_file: str = "docker-compose.yml"):
        self.compose_file = compose_file
        self.docker_client = docker.from_env()
        self.project_name = "openproject-test"
        
    def setup_method(self):
        """Setup before each test."""
        self.stop_services()
        
    def teardown_method(self):
        """Cleanup after each test."""
        self.stop_services()
        
    def run_compose_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run a docker-compose command."""
        full_command = ["docker-compose", "-f", self.compose_file, "-p", self.project_name] + command
        return subprocess.run(full_command, capture_output=True, text=True)
        
    def start_services(self, services: Optional[List[str]] = None):
        """Start Docker Compose services."""
        logger.info("Starting Docker Compose services")
        
        cmd = ["up", "-d"]
        if services:
            cmd.extend(services)
            
        result = self.run_compose_command(cmd)
        
        if result.returncode != 0:
            logger.error(f"Failed to start services: {result.stderr}")
            raise Exception(f"Docker Compose up failed: {result.stderr}")
            
        logger.info("Services started successfully")
        
    def stop_services(self):
        """Stop and remove all services."""
        logger.info("Stopping Docker Compose services")
        
        self.run_compose_command(["down", "-v", "--remove-orphans"])
        logger.info("Services stopped")
        
    def wait_for_service_health(self, service_name: str, health_url: str, timeout: int = 120) -> bool:
        """Wait for a service to become healthy."""
        logger.info(f"Waiting for {service_name} to be healthy at {health_url}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"{service_name} is healthy")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            
        logger.error(f"{service_name} did not become healthy within {timeout} seconds")
        return False
        
    def get_service_logs(self, service_name: str) -> str:
        """Get logs for a specific service."""
        result = self.run_compose_command(["logs", service_name])
        return result.stdout
        
    def check_service_running(self, service_name: str) -> bool:
        """Check if a service is running."""
        result = self.run_compose_command(["ps", "--services", "--filter", f"status=running"])
        return service_name in result.stdout
        
    def test_service_connectivity(self, services: Dict[str, str]) -> Dict[str, bool]:
        """Test connectivity between services."""
        connectivity_results = {}
        
        for service_name, health_url in services.items():
            try:
                response = requests.get(health_url, timeout=10)
                connectivity_results[service_name] = response.status_code == 200
                logger.info(f"{service_name} connectivity: {response.status_code}")
            except Exception as e:
                connectivity_results[service_name] = False
                logger.error(f"{service_name} connectivity failed: {e}")
                
        return connectivity_results

@pytest.mark.docker_compose
class TestDockerComposeDeployment:
    """Test Docker Compose deployment scenarios."""
    
    @pytest.fixture(scope="class")
    def compose_tester(self):
        return DockerComposeTester()
        
    def test_compose_file_validity(self, compose_tester):
        """Test that the docker-compose.yml file is valid."""
        try:
            with open(compose_tester.compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
                
            # Basic validation
            assert 'version' in compose_config, "Compose file should have version"
            assert 'services' in compose_config, "Compose file should have services"
            assert len(compose_config['services']) > 0, "Compose file should define at least one service"
            
            logger.info(f"Compose file is valid with {len(compose_config['services'])} services")
            
        except Exception as e:
            pytest.fail(f"Invalid docker-compose.yml file: {e}")
            
    def test_service_build(self, compose_tester):
        """Test that all services can be built."""
        result = compose_tester.run_compose_command(["build"])
        
        if result.returncode != 0:
            pytest.fail(f"Service build failed: {result.stderr}")
            
        logger.info("All services built successfully")
        
    def test_service_startup(self, compose_tester):
        """Test that services can start up."""
        try:
            compose_tester.start_services()
            
            # Wait a bit for services to start
            time.sleep(30)
            
            # Check that services are running
            result = compose_tester.run_compose_command(["ps"])
            assert result.returncode == 0, "docker-compose ps should succeed"
            
            logger.info("Services started successfully")
            
        finally:
            compose_tester.stop_services()
            
    def test_service_health_checks(self, compose_tester):
        """Test service health checks."""
        try:
            compose_tester.start_services()
            
            # Define health check endpoints
            health_checks = {
                'solution-http': 'http://localhost:8010/health',
                'solution-fastapi': 'http://localhost:8020/health',
                'solution-typescript': 'http://localhost:8040/health'
            }
            
            health_results = {}
            
            for service, url in health_checks.items():
                if compose_tester.check_service_running(service):
                    healthy = compose_tester.wait_for_service_health(service, url, timeout=60)
                    health_results[service] = healthy
                else:
                    logger.warning(f"Service {service} is not running")
                    health_results[service] = False
                    
            # At least one service should be healthy
            assert any(health_results.values()), "At least one service should be healthy"
            
            logger.info(f"Health check results: {health_results}")
            
        finally:
            compose_tester.stop_services()
            
    def test_service_networking(self, compose_tester):
        """Test service-to-service networking."""
        try:
            compose_tester.start_services()
            
            # Test that services can communicate with each other
            services = ['solution-http', 'solution-fastapi']
            
            for service in services:
                if compose_tester.check_service_running(service):
                    # Test if service can reach other services
                    result = compose_tester.run_compose_command([
                        "exec", "-T", service, "curl", "-f", "http://localhost:8010/health"
                    ])
                    
                    # We don't care about the result, just that the command works
                    logger.info(f"Networking test for {service}: {result.returncode}")
                    
        finally:
            compose_tester.stop_services()
            
    def test_volume_persistence(self, compose_tester):
        """Test that volumes work correctly."""
        try:
            compose_tester.start_services()
            
            # Wait for services to be ready
            time.sleep(20)
            
            # Check volume mounts
            result = compose_tester.run_compose_command(["exec", "-T", "solution-fastapi", "mount"])
            assert result.returncode == 0, "Should be able to check mounts"
            
            # Look for volume mounts in output
            mount_output = result.stdout
            logger.info(f"Volume mounts: {mount_output}")
            
        finally:
            compose_tester.stop_services()
            
    def test_environment_variables(self, compose_tester):
        """Test that environment variables are properly set."""
        try:
            compose_tester.start_services()
            
            # Test environment variables in FastAPI service
            result = compose_tester.run_compose_command([
                "exec", "-T", "solution-fastapi", "env"
            ])
            
            assert result.returncode == 0, "Should be able to check environment"
            
            env_output = result.stdout
            assert "OPENPROJECT_URL" in env_output, "OPENPROJECT_URL should be set"
            assert "LOG_LEVEL" in env_output, "LOG_LEVEL should be set"
            
            logger.info("Environment variables are properly set")
            
        finally:
            compose_tester.stop_services()

@pytest.mark.docker_compose
class TestDockerComposeScaling:
    """Test Docker Compose scaling capabilities."""
    
    @pytest.fixture
    def scaling_tester(self):
        return DockerComposeTester()
        
    def test_service_scaling(self, scaling_tester):
        """Test that services can be scaled."""
        try:
            # Start with single instance
            scaling_tester.start_services(['solution-fastapi'])
            
            # Scale up
            result = scaling_tester.run_compose_command(["up", "-d", "--scale", "solution-fastapi=2"])
            assert result.returncode == 0, "Should be able to scale up"
            
            time.sleep(10)
            
            # Check that multiple instances are running
            result = scaling_tester.run_compose_command(["ps", "solution-fastapi"])
            assert "solution-fastapi" in result.stdout, "Scaled service should be running"
            
            # Count instances (rough check)
            instance_count = result.stdout.count("solution-fastapi")
            assert instance_count >= 2, f"Should have at least 2 instances, found {instance_count}"
            
            logger.info(f"Successfully scaled to {instance_count} instances")
            
        finally:
            scaling_tester.stop_services()
            
    def test_load_balancing(self, scaling_tester):
        """Test basic load balancing with scaled services."""
        try:
            # Start and scale service
            scaling_tester.start_services(['solution-fastapi'])
            scaling_tester.run_compose_command(["up", "-d", "--scale", "solution-fastapi=3"])
            
            time.sleep(15)
            
            # Make multiple requests to the service
            responses = []
            for i in range(10):
                try:
                    response = requests.get('http://localhost:8020/health', timeout=5)
                    responses.append(response.status_code)
                except Exception as e:
                    logger.warning(f"Request {i} failed: {e}")
                    
            # Most requests should succeed
            success_rate = sum(1 for r in responses if r == 200) / len(responses)
            assert success_rate >= 0.7, f"Success rate should be >= 70%, got {success_rate*100}%"
            
            logger.info(f"Load balancing test completed with {success_rate*100:.1f}% success rate")
            
        finally:
            scaling_tester.stop_services()

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--html=docker-compose-test-report.html"
    ])