#!/usr/bin/env python3
"""
CI/CD Pipeline Validation Script
Validates all CI/CD pipelines across all solutions to ensure they work correctly.
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import yaml


class CICDValidator:
    """Validates CI/CD pipelines across all solutions."""
    
    def __init__(self):
        self.solutions = [
            'solution-http',
            'solution-fastapi', 
            'solution-fastmcp',
            'solution-typescript'
        ]
        
        self.environments = ['development', 'staging', 'production']
        
        self.workflows = [
            'ci-http.yml',
            'ci-fastapi.yml',
            'ci-typescript.yml',
            'ci-fastmcp.yml',
            'ci-unified.yml',
            'deploy-environment.yml',
            'quality-gate.yml',
            'deployment-approval.yml',
            'security-performance.yml',
            'container-registry.yml'
        ]
        
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': 0,
            'solution_results': {},
            'workflow_results': {},
            'environment_results': {},
            'recommendations': []
        }
    
    async def validate_solution_structure(self, solution: str) -> Dict[str, Any]:
        """Validate solution directory structure."""
        
        result = {
            'solution': solution,
            'checks': [],
            'passed': 0,
            'failed': 0,
            'total': 0,
            'valid': True
        }
        
        solution_path = Path(solution)
        
        # Check if solution directory exists
        if not solution_path.exists():
            result['checks'].append({
                'check': 'directory_exists',
                'status': 'FAILED',
                'message': f'Solution directory {solution} does not exist'
            })
            result['failed'] += 1
            result['valid'] = False
        else:
            result['checks'].append({
                'check': 'directory_exists',
                'status': 'PASSED',
                'message': f'Solution directory {solution} exists'
            })
            result['passed'] += 1
        
        # Check for required files
        required_files = {
            'solution-http': ['src/main.py', 'requirements.txt'],
            'solution-fastapi': ['app/main.py', 'requirements.txt'],
            'solution-fastmcp': ['src/main.py', 'requirements.txt'],
            'solution-typescript': ['package.json', 'tsconfig.json']
        }
        
        if solution in required_files:
            for file_path in required_files[solution]:
                full_path = solution_path / file_path
                if full_path.exists():
                    result['checks'].append({
                        'check': f'file_exists_{file_path.replace("/", "_")}',
                        'status': 'PASSED',
                        'message': f'Required file {file_path} exists'
                    })
                    result['passed'] += 1
                else:
                    result['checks'].append({
                        'check': f'file_exists_{file_path.replace("/", "_")}',
                        'status': 'FAILED',
                        'message': f'Required file {file_path} missing'
                    })
                    result['failed'] += 1
                    result['valid'] = False
        
        # Check for Dockerfile
        dockerfile_path = solution_path / 'Dockerfile'
        if dockerfile_path.exists():
            result['checks'].append({
                'check': 'dockerfile_exists',
                'status': 'PASSED',
                'message': 'Dockerfile exists'
            })
            result['passed'] += 1
        else:
            result['checks'].append({
                'check': 'dockerfile_exists',
                'status': 'FAILED',
                'message': 'Dockerfile missing'
            })
            result['failed'] += 1
            result['valid'] = False
        
        # Check for test files
        test_files = list(solution_path.rglob('test_*.py')) + list(solution_path.rglob('*_test.py'))
        if test_files:
            result['checks'].append({
                'check': 'test_files_exist',
                'status': 'PASSED',
                'message': f'Found {len(test_files)} test files'
            })
            result['passed'] += 1
        else:
            result['checks'].append({
                'check': 'test_files_exist',
                'status': 'WARNING',
                'message': 'No test files found'
            })
            result['failed'] += 1
        
        result['total'] = result['passed'] + result['failed']
        
        return result
    
    async def validate_workflow_syntax(self, workflow_file: str) -> Dict[str, Any]:
        """Validate GitHub Actions workflow syntax."""
        
        result = {
            'workflow': workflow_file,
            'checks': [],
            'passed': 0,
            'failed': 0,
            'total': 0,
            'valid': True
        }
        
        workflow_path = Path('.github/workflows') / workflow_file
        
        # Check if workflow file exists
        if not workflow_path.exists():
            result['checks'].append({
                'check': 'workflow_exists',
                'status': 'FAILED',
                'message': f'Workflow file {workflow_file} does not exist'
            })
            result['failed'] += 1
            result['valid'] = False
        else:
            result['checks'].append({
                'check': 'workflow_exists',
                'status': 'PASSED',
                'message': f'Workflow file {workflow_file} exists'
            })
            result['passed'] += 1
        
        # Validate YAML syntax
        if workflow_path.exists():
            try:
                with open(workflow_path, 'r') as f:
                    workflow_data = yaml.safe_load(f)
                
                result['checks'].append({
                    'check': 'yaml_syntax',
                    'status': 'PASSED',
                    'message': 'YAML syntax is valid'
                })
                result['passed'] += 1
                
                # Check required workflow fields
                required_fields = ['name', 'on', 'jobs']
                for field in required_fields:
                    if field in workflow_data:
                        result['checks'].append({
                            'check': f'has_{field}',
                            'status': 'PASSED',
                            'message': f'Workflow has {field} field'
                        })
                        result['passed'] += 1
                    else:
                        result['checks'].append({
                            'check': f'has_{field}',
                            'status': 'FAILED',
                            'message': f'Workflow missing {field} field'
                        })
                        result['failed'] += 1
                        result['valid'] = False
                
                # Check for common security issues
                if 'jobs' in workflow_data:
                    for job_name, job_config in workflow_data['jobs'].items():
                        # Check for hardcoded secrets
                        if 'env' in job_config:
                            env_vars = job_config['env']
                            secret_keys = [k for k in env_vars.keys() if 'secret' in k.lower() or 'key' in k.lower() or 'password' in k.lower()]
                            if secret_keys:
                                result['checks'].append({
                                    'check': 'no_hardcoded_secrets',
                                    'status': 'WARNING',
                                    'message': f'Potential hardcoded secrets in job {job_name}: {secret_keys}'
                                })
                                result['failed'] += 1
                
            except yaml.YAMLError as e:
                result['checks'].append({
                    'check': 'yaml_syntax',
                    'status': 'FAILED',
                    'message': f'YAML syntax error: {str(e)}'
                })
                result['failed'] += 1
                result['valid'] = False
            except Exception as e:
                result['checks'].append({
                    'check': 'workflow_parsing',
                    'status': 'FAILED',
                    'message': f'Error parsing workflow: {str(e)}'
                })
                result['failed'] += 1
                result['valid'] = False
        
        result['total'] = result['passed'] + result['failed']
        
        return result
    
    async def validate_deployment_scripts(self) -> Dict[str, Any]:
        """Validate deployment scripts."""
        
        result = {
            'component': 'deployment_scripts',
            'checks': [],
            'passed': 0,
            'failed': 0,
            'total': 0,
            'valid': True
        }
        
        scripts = [
            'scripts/deploy.sh',
            'scripts/deploy-env.sh',
            'scripts/build-containers.sh'
        ]
        
        for script in scripts:
            script_path = Path(script)
            
            if script_path.exists():
                result['checks'].append({
                    'check': f'script_exists_{Path(script).stem}',
                    'status': 'PASSED',
                    'message': f'Script {script} exists'
                })
                result['passed'] += 1
                
                # Check if script is executable
                if os.access(script_path, os.X_OK):
                    result['checks'].append({
                        'check': f'script_executable_{Path(script).stem}',
                        'status': 'PASSED',
                        'message': f'Script {script} is executable'
                    })
                    result['passed'] += 1
                else:
                    result['checks'].append({
                        'check': f'script_executable_{Path(script).stem}',
                        'status': 'FAILED',
                        'message': f'Script {script} is not executable'
                    })
                    result['failed'] += 1
                    result['valid'] = False
            else:
                result['checks'].append({
                    'check': f'script_exists_{Path(script).stem}',
                    'status': 'FAILED',
                    'message': f'Script {script} does not exist'
                })
                result['failed'] += 1
                result['valid'] = False
        
        result['total'] = result['passed'] + result['failed']
        
        return result
    
    async def validate_test_utilities(self) -> Dict[str, Any]:
        """Validate test utilities and frameworks."""
        
        result = {
            'component': 'test_utilities',
            'checks': [],
            'passed': 0,
            'failed': 0,
            'total': 0,
            'valid': True
        }
        
        test_utils = [
            'test-utils/python/cross_solution_tester.py',
            'test-reports/test_aggregator.py',
            'performance-tests/run_benchmarks.py'
        ]
        
        for util in test_utils:
            util_path = Path(util)
            
            if util_path.exists():
                result['checks'].append({
                    'check': f'util_exists_{Path(util).stem}',
                    'status': 'PASSED',
                    'message': f'Test utility {util} exists'
                })
                result['passed'] += 1
                
                # Check if Python file is syntactically correct
                if util_path.suffix == '.py':
                    try:
                        with open(util_path, 'r') as f:
                            compile(f.read(), str(util_path), 'exec')
                        result['checks'].append({
                            'check': f'util_syntax_{Path(util).stem}',
                            'status': 'PASSED',
                            'message': f'Test utility {util} has valid Python syntax'
                        })
                        result['passed'] += 1
                    except SyntaxError as e:
                        result['checks'].append({
                            'check': f'util_syntax_{Path(util).stem}',
                            'status': 'FAILED',
                            'message': f'Syntax error in {util}: {str(e)}'
                        })
                        result['failed'] += 1
                        result['valid'] = False
            else:
                result['checks'].append({
                    'check': f'util_exists_{Path(util).stem}',
                    'status': 'FAILED',
                    'message': f'Test utility {util} does not exist'
                })
                result['failed'] += 1
                result['valid'] = False
        
        result['total'] = result['passed'] + result['failed']
        
        return result
    
    async def validate_dependencies(self, solution: str) -> Dict[str, Any]:
        """Validate solution dependencies."""
        
        result = {
            'solution': solution,
            'checks': [],
            'passed': 0,
            'failed': 0,
            'total': 0,
            'valid': True
        }
        
        solution_path = Path(solution)
        
        if not solution_path.exists():
            return result
        
        # Check Python dependencies
        requirements_files = list(solution_path.rglob('requirements*.txt'))
        if requirements_files:
            for req_file in requirements_files:
                result['checks'].append({
                    'check': f'requirements_exists_{req_file.name}',
                    'status': 'PASSED',
                    'message': f'Requirements file {req_file.name} exists'
                })
                result['passed'] += 1
                
                # Check for security issues in dependencies
                try:
                    result_check = subprocess.run(
                        ['safety', 'check', '--file', str(req_file), '--json'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result_check.returncode == 0:
                        result['checks'].append({
                            'check': f'dependency_security_{req_file.name}',
                            'status': 'PASSED',
                            'message': f'No security issues found in {req_file.name}'
                        })
                        result['passed'] += 1
                    else:
                        result['checks'].append({
                            'check': f'dependency_security_{req_file.name}',
                            'status': 'WARNING',
                            'message': f'Security issues found in {req_file.name}'
                        })
                        result['failed'] += 1
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    result['checks'].append({
                        'check': f'dependency_security_{req_file.name}',
                        'status': 'SKIPPED',
                        'message': f'Safety check skipped for {req_file.name}'
                    })
        else:
            result['checks'].append({
                'check': 'requirements_exists',
                'status': 'FAILED',
                'message': 'No requirements files found'
            })
            result['failed'] += 1
            result['valid'] = False
        
        # Check Node.js dependencies for TypeScript solution
        if solution == 'solution-typescript':
            package_json = solution_path / 'package.json'
            if package_json.exists():
                result['checks'].append({
                    'check': 'package_json_exists',
                    'status': 'PASSED',
                    'message': 'package.json exists'
                })
                result['passed'] += 1
                
                # Check for npm audit
                try:
                    os.chdir(solution_path)
                    result_check = subprocess.run(
                        ['npm', 'audit', '--json'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result_check.returncode == 0:
                        result['checks'].append({
                            'check': 'npm_audit',
                            'status': 'PASSED',
                            'message': 'No npm security issues found'
                        })
                        result['passed'] += 1
                    else:
                        result['checks'].append({
                            'check': 'npm_audit',
                            'status': 'WARNING',
                            'message': 'NPM security issues found'
                        })
                        result['failed'] += 1
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    result['checks'].append({
                        'check': 'npm_audit',
                        'status': 'SKIPPED',
                        'message': 'NPM audit skipped'
                    })
                
                os.chdir('..')
            else:
                result['checks'].append({
                    'check': 'package_json_exists',
                    'status': 'FAILED',
                    'message': 'package.json missing'
                })
                result['failed'] += 1
                result['valid'] = False
        
        result['total'] = result['passed'] + result['failed']
        
        return result
    
    async def validate_ci_cd_integration(self) -> Dict[str, Any]:
        """Validate CI/CD integration across solutions."""
        
        result = {
            'component': 'ci_cd_integration',
            'checks': [],
            'passed': 0,
            'failed': 0,
            'total': 0,
            'valid': True
        }
        
        # Check if CI/CD architecture document exists
        if Path('CICD_ARCHITECTURE.md').exists():
            result['checks'].append({
                'check': 'architecture_document',
                'status': 'PASSED',
                'message': 'CI/CD architecture document exists'
            })
            result['passed'] += 1
        else:
            result['checks'].append({
                'check': 'architecture_document',
                'status': 'FAILED',
                'message': 'CI/CD architecture document missing'
            })
            result['failed'] += 1
            result['valid'] = False
        
        # Check workflow consistency
        workflow_dir = Path('.github/workflows')
        if workflow_dir.exists():
            workflow_files = list(workflow_dir.glob('*.yml'))
            
            # Check for reusable workflows
            reusable_workflows = [f for f in workflow_files if 'reusable' in f.name]
            if reusable_workflows:
                result['checks'].append({
                    'check': 'reusable_workflows',
                    'status': 'PASSED',
                    'message': f'Found {len(reusable_workflows)} reusable workflows'
                })
                result['passed'] += 1
            else:
                result['checks'].append({
                    'check': 'reusable_workflows',
                    'status': 'WARNING',
                    'message': 'No reusable workflows found'
                })
                result['failed'] += 1
            
            # Check for solution-specific workflows
            solution_workflows = [f for f in workflow_files if f.name.startswith('ci-') and 'unified' not in f.name]
            if solution_workflows:
                result['checks'].append({
                    'check': 'solution_workflows',
                    'status': 'PASSED',
                    'message': f'Found {len(solution_workflows)} solution-specific workflows'
                })
                result['passed'] += 1
            else:
                result['checks'].append({
                    'check': 'solution_workflows',
                    'status': 'FAILED',
                    'message': 'No solution-specific workflows found'
                })
                result['failed'] += 1
                result['valid'] = False
        
        result['total'] = result['passed'] + result['failed']
        
        return result
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete CI/CD validation."""
        
        print("🚀 Starting CI/CD pipeline validation...")
        
        # Validate solution structures
        print("📁 Validating solution structures...")
        for solution in self.solutions:
            print(f"  Validating {solution}...")
            solution_result = await self.validate_solution_structure(solution)
            self.validation_results['solution_results'][solution] = solution_result
            self.validation_results['total_checks'] += solution_result['total']
            self.validation_results['passed_checks'] += solution_result['passed']
            self.validation_results['failed_checks'] += solution_result['failed']
        
        # Validate workflows
        print("🔧 Validating workflows...")
        for workflow in self.workflows:
            print(f"  Validating {workflow}...")
            workflow_result = await self.validate_workflow_syntax(workflow)
            self.validation_results['workflow_results'][workflow] = workflow_result
            self.validation_results['total_checks'] += workflow_result['total']
            self.validation_results['passed_checks'] += workflow_result['passed']
            self.validation_results['failed_checks'] += workflow_result['failed']
        
        # Validate deployment scripts
        print("🚀 Validating deployment scripts...")
        deployment_result = await self.validate_deployment_scripts()
        self.validation_results['deployment_scripts'] = deployment_result
        self.validation_results['total_checks'] += deployment_result['total']
        self.validation_results['passed_checks'] += deployment_result['passed']
        self.validation_results['failed_checks'] += deployment_result['failed']
        
        # Validate test utilities
        print("🧪 Validating test utilities...")
        test_result = await self.validate_test_utilities()
        self.validation_results['test_utilities'] = test_result
        self.validation_results['total_checks'] += test_result['total']
        self.validation_results['passed_checks'] += test_result['passed']
        self.validation_results['failed_checks'] += test_result['failed']
        
        # Validate dependencies
        print("📦 Validating dependencies...")
        for solution in self.solutions:
            print(f"  Validating {solution} dependencies...")
            dep_result = await self.validate_dependencies(solution)
            self.validation_results['environment_results'][f"{solution}_deps"] = dep_result
            self.validation_results['total_checks'] += dep_result['total']
            self.validation_results['passed_checks'] += dep_result['passed']
            self.validation_results['failed_checks'] += dep_result['failed']
        
        # Validate CI/CD integration
        print("🔗 Validating CI/CD integration...")
        integration_result = await self.validate_ci_cd_integration()
        self.validation_results['ci_cd_integration'] = integration_result
        self.validation_results['total_checks'] += integration_result['total']
        self.validation_results['passed_checks'] += integration_result['passed']
        self.validation_results['failed_checks'] += integration_result['failed']
        
        # Generate recommendations
        await self.generate_recommendations()
        
        return self.validation_results
    
    async def generate_recommendations(self):
        """Generate improvement recommendations."""
        
        recommendations = []
        
        # Check for failed solution validations
        for solution, result in self.validation_results['solution_results'].items():
            if not result['valid']:
                recommendations.append(f"Fix validation issues in {solution}")
        
        # Check for failed workflow validations
        for workflow, result in self.validation_results['workflow_results'].items():
            if not result['valid']:
                recommendations.append(f"Fix workflow syntax issues in {workflow}")
        
        # Check for missing test coverage
        for solution, result in self.validation_results['solution_results'].items():
            has_tests = any('test_files_exist' in check['check'] and check['status'] == 'PASSED' 
                           for check in result['checks'])
            if not has_tests:
                recommendations.append(f"Add test files to {solution}")
        
        # Check for security issues
        total_security_issues = 0
        for category, results in self.validation_results.items():
            if isinstance(results, dict) and 'checks' in results:
                for check in results['checks']:
                    if 'security' in check['check'] and check['status'] in ['FAILED', 'WARNING']:
                        total_security_issues += 1
        
        if total_security_issues > 0:
            recommendations.append(f"Address {total_security_issues} security issues")
        
        # Check overall success rate
        if self.validation_results['total_checks'] > 0:
            success_rate = (self.validation_results['passed_checks'] / self.validation_results['total_checks']) * 100
            
            if success_rate < 80:
                recommendations.append("Improve overall CI/CD pipeline health")
            elif success_rate < 95:
                recommendations.append("Address minor CI/CD pipeline issues")
        
        self.validation_results['recommendations'] = recommendations
    
    def save_validation_report(self, output_file: str):
        """Save validation report to file."""
        
        with open(output_file, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"Validation report saved to {output_file}")
    
    def print_summary(self):
        """Print validation summary."""
        
        total = self.validation_results['total_checks']
        passed = self.validation_results['passed_checks']
        failed = self.validation_results['failed_checks']
        
        print("\n" + "="*60)
        print("🎯 CI/CD Pipeline Validation Summary")
        print("="*60)
        print(f"Total Checks: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print("\n📊 Solution Results:")
        for solution, result in self.validation_results['solution_results'].items():
            status = "✅" if result['valid'] else "❌"
            print(f"  {status} {solution}: {result['passed']}/{result['total']} checks passed")
        
        print("\n🔧 Workflow Results:")
        for workflow, result in self.validation_results['workflow_results'].items():
            status = "✅" if result['valid'] else "❌"
            print(f"  {status} {workflow}: {result['passed']}/{result['total']} checks passed")
        
        if self.validation_results['recommendations']:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(self.validation_results['recommendations'], 1):
                print(f"  {i}. {rec}")
        
        print("="*60)


async def main():
    """Main entry point for CI/CD validation."""
    
    parser = argparse.ArgumentParser(description='CI/CD Pipeline Validation')
    parser.add_argument('--output', '-o', default='cicd-validation-report.json',
                       help='Output file for validation report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    validator = CICDValidator()
    
    # Run validation
    results = await validator.run_validation()
    
    # Save report
    validator.save_validation_report(args.output)
    
    # Print summary
    validator.print_summary()
    
    # Exit with appropriate code
    if results['failed_checks'] > 0:
        print(f"\n❌ Validation failed with {results['failed_checks']} errors")
        sys.exit(1)
    else:
        print(f"\n✅ All validations passed!")
        sys.exit(0)


if __name__ == '__main__':
    asyncio.run(main())