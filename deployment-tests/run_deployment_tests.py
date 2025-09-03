#!/usr/bin/env python3
"""
Main deployment test runner script.
Orchestrates all deployment testing scenarios and generates comprehensive reports.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pytest
import docker
import requests
from test_deployment_comprehensive import DeploymentTester
from test_docker_compose import DockerComposeTester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment-tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentTestRunner:
    """Main deployment test runner."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_runs': [],
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'success_rate': 0.0
            },
            'solutions': {},
            'performance_metrics': {},
            'issues': []
        }
        self.report_dir = Path('deployment-test-reports')
        self.report_dir.mkdir(exist_ok=True)
        
    def run_test_suite(self, test_type: str, *args, **kwargs) -> Dict[str, Any]:
        """Run a specific test suite and return results."""
        logger.info(f"Running {test_type} test suite")
        
        start_time = time.time()
        
        try:
            if test_type == 'comprehensive':
                result = self.run_comprehensive_tests(*args, **kwargs)
            elif test_type == 'docker_compose':
                result = self.run_docker_compose_tests(*args, **kwargs)
            elif test_type == 'performance':
                result = self.run_performance_tests(*args, **kwargs)
            elif test_type == 'compatibility':
                result = self.run_compatibility_tests(*args, **kwargs)
            else:
                raise ValueError(f"Unknown test type: {test_type}")
                
            result['duration'] = time.time() - start_time
            result['success'] = True
            
        except Exception as e:
            logger.error(f"Test suite {test_type} failed: {e}")
            result = {
                'test_type': test_type,
                'success': False,
                'error': str(e),
                'duration': time.time() - start_time
            }
            
        return result
        
    def run_comprehensive_tests(self, solutions: List[str] = None) -> Dict[str, Any]:
        """Run comprehensive deployment tests."""
        logger.info("Running comprehensive deployment tests")
        
        if solutions is None:
            solutions = ['solution-http', 'solution-fastapi', 'solution-typescript']
            
        results = {
            'test_type': 'comprehensive',
            'solutions_tested': solutions,
            'solution_results': {},
            'summary': {
                'deployable': 0,
                'healthy': 0,
                'api_accessible': 0
            }
        }
        
        tester = DeploymentTester()
        
        try:
            for solution in solutions:
                logger.info(f"Testing {solution}")
                
                solution_result = {
                    'solution': solution,
                    'build_success': False,
                    'deployment_success': False,
                    'health_check': False,
                    'api_endpoints': {},
                    'resource_usage': {},
                    'concurrent_requests': {},
                    'error': None
                }
                
                try:
                    # Test build
                    image = tester.build_solution(solution)
                    solution_result['build_success'] = True
                    
                    # Test deployment
                    container = tester.run_container(solution, image)
                    solution_result['deployment_success'] = True
                    
                    # Test health
                    healthy = tester.wait_for_health(solution)
                    solution_result['health_check'] = healthy
                    
                    if healthy:
                        results['summary']['healthy'] += 1
                        
                        # Test API endpoints
                        api_results = tester.test_api_endpoints(solution)
                        solution_result['api_endpoints'] = api_results
                        
                        if any(api_results.values()):
                            results['summary']['api_accessible'] += 1
                            
                        # Test resource usage
                        resource_stats = tester.test_resource_usage(solution)
                        solution_result['resource_usage'] = resource_stats
                        
                        # Test concurrent requests
                        concurrent_results = tester.test_concurrent_requests(solution)
                        solution_result['concurrent_requests'] = concurrent_results
                        
                    results['summary']['deployable'] += 1
                    
                except Exception as e:
                    solution_result['error'] = str(e)
                    logger.error(f"Failed to test {solution}: {e}")
                    
                finally:
                    tester.cleanup_containers()
                    
                results['solution_results'][solution] = solution_result
                
        except Exception as e:
            logger.error(f"Comprehensive test failed: {e}")
            results['error'] = str(e)
            
        return results
        
    def run_docker_compose_tests(self, compose_file: str = 'docker-compose.yml') -> Dict[str, Any]:
        """Run Docker Compose tests."""
        logger.info("Running Docker Compose tests")
        
        results = {
            'test_type': 'docker_compose',
            'compose_file': compose_file,
            'services': {},
            'networking': {},
            'volumes': {},
            'success': False
        }
        
        try:
            compose_tester = DockerComposeTester(compose_file)
            
            # Test compose file validity
            with open(compose_file, 'r') as f:
                import yaml
                compose_config = yaml.safe_load(f)
                
            results['services'] = list(compose_config.get('services', {}).keys())
            
            # Test service build
            build_result = compose_tester.run_compose_command(['build'])
            results['build_success'] = build_result.returncode == 0
            
            # Test service startup
            compose_tester.start_services()
            time.sleep(30)
            
            # Test service health
            health_checks = {
                'solution-http': 'http://localhost:8010/health',
                'solution-fastapi': 'http://localhost:8020/health',
                'solution-typescript': 'http://localhost:8040/health'
            }
            
            health_results = {}
            for service, url in health_checks.items():
                if service in results['services']:
                    healthy = compose_tester.wait_for_service_health(service, url, timeout=60)
                    health_results[service] = healthy
                    
            results['health_checks'] = health_results
            
            # Test networking
            connectivity = compose_tester.test_service_connectivity(health_checks)
            results['networking'] = connectivity
            
            results['success'] = True
            
        except Exception as e:
            logger.error(f"Docker Compose test failed: {e}")
            results['error'] = str(e)
            
        finally:
            try:
                compose_tester.stop_services()
            except:
                pass
                
        return results
        
    def run_performance_tests(self, solutions: List[str] = None) -> Dict[str, Any]:
        """Run performance tests for deployed solutions."""
        logger.info("Running performance tests")
        
        if solutions is None:
            solutions = ['solution-http', 'solution-fastapi']
            
        results = {
            'test_type': 'performance',
            'solutions': {},
            'benchmarks': {
                'startup_time': {},
                'memory_usage': {},
                'response_time': {},
                'throughput': {}
            }
        }
        
        tester = DeploymentTester()
        
        try:
            for solution in solutions:
                logger.info(f"Performance testing {solution}")
                
                solution_result = {
                    'solution': solution,
                    'startup_time': 0,
                    'memory_usage': {},
                    'response_times': [],
                    'throughput': 0
                }
                
                try:
                    # Test startup time
                    start_time = time.time()
                    image = tester.build_solution(solution)
                    container = tester.run_container(solution, image)
                    healthy = tester.wait_for_health(solution)
                    startup_time = time.time() - start_time
                    
                    solution_result['startup_time'] = startup_time
                    results['benchmarks']['startup_time'][solution] = startup_time
                    
                    if healthy:
                        # Test memory usage
                        resource_stats = tester.test_resource_usage(solution)
                        solution_result['memory_usage'] = resource_stats
                        results['benchmarks']['memory_usage'][solution] = resource_stats
                        
                        # Test response times
                        port = tester.base_ports[solution]
                        url = f"http://localhost:{port}/health"
                        
                        response_times = []
                        for _ in range(20):
                            start = time.time()
                            response = requests.get(url, timeout=10)
                            end = time.time()
                            if response.status_code == 200:
                                response_times.append((end - start) * 1000)  # Convert to ms
                                
                        solution_result['response_times'] = response_times
                        results['benchmarks']['response_time'][solution] = response_times
                        
                        # Test throughput
                        concurrent_results = tester.test_concurrent_requests(solution, num_requests=50)
                        solution_result['throughput'] = concurrent_results['total_requests'] / concurrent_results['total_time']
                        results['benchmarks']['throughput'][solution] = solution_result['throughput']
                        
                    results['solutions'][solution] = solution_result
                    
                except Exception as e:
                    logger.error(f"Performance test failed for {solution}: {e}")
                    solution_result['error'] = str(e)
                    results['solutions'][solution] = solution_result
                    
                finally:
                    tester.cleanup_containers()
                    
        except Exception as e:
            logger.error(f"Performance test suite failed: {e}")
            results['error'] = str(e)
            
        return results
        
    def run_compatibility_tests(self) -> Dict[str, Any]:
        """Run cross-solution compatibility tests."""
        logger.info("Running compatibility tests")
        
        results = {
            'test_type': 'compatibility',
            'api_compatibility': {},
            'data_compatibility': {},
            'protocol_compatibility': {},
            'success': False
        }
        
        tester = DeploymentTester()
        solutions = ['solution-http', 'solution-fastapi', 'solution-typescript']
        
        try:
            # Deploy all solutions
            deployed = {}
            for solution in solutions:
                try:
                    image = tester.build_solution(solution)
                    container = tester.run_container(solution, image)
                    if tester.wait_for_health(solution):
                        deployed[solution] = container
                except Exception as e:
                    logger.error(f"Failed to deploy {solution} for compatibility testing: {e}")
                    
            if len(deployed) < 2:
                raise Exception("Need at least 2 deployed solutions for compatibility testing")
                
            # Test API compatibility
            compatibility = tester.test_cross_solution_compatibility()
            results['api_compatibility'] = compatibility
            
            # Test data format compatibility
            data_compatibility = {}
            common_endpoints = ['/health', '/api/projects']
            
            for endpoint in common_endpoints:
                responses = {}
                for solution in deployed:
                    port = tester.base_ports[solution]
                    url = f"http://localhost:{port}{endpoint}"
                    
                    try:
                        response = requests.get(url, timeout=10)
                        if response.status_code == 200:
                            responses[solution] = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    except Exception as e:
                        responses[solution] = f"Error: {e}"
                        
                # Check if responses are compatible (same structure)
                if len(responses) >= 2:
                    sample_responses = list(responses.values())
                    compatible = isinstance(sample_responses[0], type(sample_responses[1]))
                    data_compatibility[endpoint] = compatible
                    
            results['data_compatibility'] = data_compatibility
            results['success'] = True
            
        except Exception as e:
            logger.error(f"Compatibility test failed: {e}")
            results['error'] = str(e)
            
        finally:
            tester.cleanup_containers()
            
        return results
        
    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        logger.info("Generating deployment test report")
        
        # Calculate summary statistics
        total_tests = len(self.results['test_runs'])
        passed_tests = sum(1 for test in self.results['test_runs'] if test.get('success', False))
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.results['summary'].update({
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate
        })
        
        # Generate HTML report
        report_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Deployment Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ background-color: #e8f5e8; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .test-section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .success {{ background-color: #d4edda; }}
                .failure {{ background-color: #f8d7da; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f8f9fa; border-radius: 3px; }}
                pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Deployment Test Report</h1>
                <p>Generated: {self.results['timestamp']}</p>
            </div>
            
            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">
                    <strong>Total Tests:</strong> {total_tests}
                </div>
                <div class="metric">
                    <strong>Passed:</strong> {passed_tests}
                </div>
                <div class="metric">
                    <strong>Failed:</strong> {failed_tests}
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {success_rate:.1f}%
                </div>
            </div>
        """
        
        # Add test results
        for test_run in self.results['test_runs']:
            status_class = 'success' if test_run.get('success', False) else 'failure'
            report_html += f"""
            <div class="test-section {status_class}">
                <h3>{test_run.get('test_type', 'Unknown Test')}</h3>
                <p><strong>Duration:</strong> {test_run.get('duration', 0):.2f}s</p>
                <p><strong>Status:</strong> {'✅ Passed' if test_run.get('success', False) else '❌ Failed'}</p>
            """
            
            if 'error' in test_run:
                report_html += f'<p><strong>Error:</strong> {test_run["error"]}</p>'
                
            if 'solution_results' in test_run:
                report_html += '<h4>Solution Results:</h4><ul>'
                for solution, result in test_run['solution_results'].items():
                    status = '✅' if result.get('health_check', False) else '❌'
                    report_html += f'<li>{status} {solution}</li>'
                report_html += '</ul>'
                
            report_html += '</div>'
            
        report_html += """
        </body>
        </html>
        """
        
        # Save report
        report_file = self.report_dir / f'deployment_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
        with open(report_file, 'w') as f:
            f.write(report_html)
            
        # Save JSON data
        json_file = self.report_dir / f'deployment_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Report generated: {report_file}")
        return str(report_file)
        
    def run_all_tests(self) -> str:
        """Run all deployment test suites."""
        logger.info("Starting comprehensive deployment test suite")
        
        # Run all test suites
        test_suites = [
            ('comprehensive', {}),
            ('docker_compose', {}),
            ('performance', {}),
            ('compatibility', {})
        ]
        
        for test_type, kwargs in test_suites:
            try:
                result = self.run_test_suite(test_type, **kwargs)
                self.results['test_runs'].append(result)
                
                if result.get('success', False):
                    logger.info(f"✅ {test_type} tests passed")
                else:
                    logger.error(f"❌ {test_type} tests failed")
                    
            except Exception as e:
                logger.error(f"❌ {test_type} tests crashed: {e}")
                self.results['test_runs'].append({
                    'test_type': test_type,
                    'success': False,
                    'error': str(e)
                })
                
        # Generate report
        report_file = self.generate_report()
        
        # Print summary
        summary = self.results['summary']
        logger.info(f"""
        🎯 Deployment Test Summary:
        - Total Tests: {summary['total_tests']}
        - Passed: {summary['passed_tests']}
        - Failed: {summary['failed_tests']}
        - Success Rate: {summary['success_rate']:.1f}%
        - Report: {report_file}
        """)
        
        return report_file

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run deployment tests')
    parser.add_argument('--test-type', choices=['all', 'comprehensive', 'docker_compose', 'performance', 'compatibility'],
                       default='all', help='Type of tests to run')
    parser.add_argument('--solutions', nargs='+', help='Specific solutions to test')
    parser.add_argument('--compose-file', default='docker-compose.yml', help='Docker Compose file to test')
    parser.add_argument('--output-dir', default='deployment-test-reports', help='Output directory for reports')
    
    args = parser.parse_args()
    
    runner = DeploymentTestRunner()
    runner.report_dir = Path(args.output_dir)
    runner.report_dir.mkdir(exist_ok=True)
    
    if args.test_type == 'all':
        report_file = runner.run_all_tests()
    else:
        kwargs = {}
        if args.solutions:
            kwargs['solutions'] = args.solutions
        if args.compose_file:
            kwargs['compose_file'] = args.compose_file
            
        result = runner.run_test_suite(args.test_type, **kwargs)
        runner.results['test_runs'].append(result)
        report_file = runner.generate_report()
        
    print(f"Report generated: {report_file}")
    
    # Exit with appropriate code
    success = all(test.get('success', False) for test in runner.results['test_runs'])
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()