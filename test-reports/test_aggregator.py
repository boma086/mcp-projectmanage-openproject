#!/usr/bin/env python3
"""
Cross-solution test aggregator for CI/CD pipeline.
Aggregates test results from multiple solutions and generates comprehensive reports.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse


class TestAggregator:
    """Aggregates test results from multiple solutions."""
    
    def __init__(self):
        self.results_dir = Path('test-results')
        self.coverage_dir = Path('coverage-reports')
        self.output_dir = Path('test-reports')
        
    def aggregate_test_results(self) -> Dict[str, Any]:
        """Aggregate test results from all solutions."""
        
        aggregated = {
            'timestamp': datetime.now().isoformat(),
            'solutions': {},
            'summary': {
                'total_solutions': 0,
                'solutions_with_tests': 0,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'skipped_tests': 0,
                'average_coverage': 0.0,
                'overall_success_rate': 0.0
            }
        }
        
        # Find all test result files
        test_result_files = list(self.results_dir.glob('**/test-summary.json'))
        
        if not test_result_files:
            return aggregated
            
        coverage_sum = 0.0
        coverage_count = 0
        
        for result_file in test_result_files:
            try:
                with open(result_file, 'r') as f:
                    solution_results = json.load(f)
                    
                solution_name = solution_results.get('solution', 'unknown')
                aggregated['solutions'][solution_name] = solution_results
                aggregated['summary']['total_solutions'] += 1
                
                if solution_results.get('solution') != 'unknown':
                    aggregated['summary']['solutions_with_tests'] += 1
                
                # Aggregate test counts
                aggregated['summary']['total_tests'] += solution_results.get('total_tests', 0)
                aggregated['summary']['passed_tests'] += solution_results.get('passed_tests', 0)
                aggregated['summary']['failed_tests'] += solution_results.get('failed_tests', 0)
                aggregated['summary']['skipped_tests'] += solution_results.get('skipped_tests', 0)
                
                # Aggregate coverage
                coverage = solution_results.get('coverage', 0)
                if coverage > 0:
                    coverage_sum += coverage
                    coverage_count += 1
                    
            except Exception as e:
                print(f"Error processing {result_file}: {e}")
                
        # Calculate summary metrics
        if coverage_count > 0:
            aggregated['summary']['average_coverage'] = round(coverage_sum / coverage_count, 1)
            
        if aggregated['summary']['total_tests'] > 0:
            aggregated['summary']['overall_success_rate'] = round(
                (aggregated['summary']['passed_tests'] / aggregated['summary']['total_tests']) * 100, 1
            )
            
        return aggregated
        
    def aggregate_coverage_reports(self) -> Dict[str, Any]:
        """Aggregate coverage reports from all solutions."""
        
        coverage_data = {
            'timestamp': datetime.now().isoformat(),
            'solutions': {},
            'summary': {
                'total_solutions': 0,
                'solutions_with_coverage': 0,
                'average_line_coverage': 0.0,
                'average_branch_coverage': 0.0,
                'total_lines_covered': 0,
                'total_lines': 0
            }
        }
        
        # Find all coverage files
        coverage_files = list(self.coverage_dir.glob('**/coverage.xml'))
        
        line_coverage_sum = 0.0
        branch_coverage_sum = 0.0
        total_lines_covered = 0
        total_lines = 0
        coverage_count = 0
        
        for coverage_file in coverage_files:
            try:
                solution_name = coverage_file.parent.parent.name
                
                with open(coverage_file, 'r') as f:
                    coverage_xml = f.read()
                    
                # Parse XML coverage data
                coverage_info = self._parse_coverage_xml(coverage_xml)
                coverage_data['solutions'][solution_name] = coverage_info
                coverage_data['summary']['total_solutions'] += 1
                
                if coverage_info.get('line_coverage', 0) > 0:
                    coverage_data['summary']['solutions_with_coverage'] += 1
                    line_coverage_sum += coverage_info.get('line_coverage', 0)
                    branch_coverage_sum += coverage_info.get('branch_coverage', 0)
                    total_lines_covered += coverage_info.get('lines_covered', 0)
                    total_lines += coverage_info.get('total_lines', 0)
                    coverage_count += 1
                    
            except Exception as e:
                print(f"Error processing {coverage_file}: {e}")
                
        # Calculate summary metrics
        if coverage_count > 0:
            coverage_data['summary']['average_line_coverage'] = round(line_coverage_sum / coverage_count, 1)
            coverage_data['summary']['average_branch_coverage'] = round(branch_coverage_sum / coverage_count, 1)
            
        coverage_data['summary']['total_lines_covered'] = total_lines_covered
        coverage_data['summary']['total_lines'] = total_lines
        
        return coverage_data
        
    def _parse_coverage_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse coverage XML data."""
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_content)
            
            # Extract coverage metrics
            line_coverage = float(root.get('line-rate', '0')) * 100
            branch_coverage = float(root.get('branch-rate', '0')) * 100
            
            # Calculate line counts
            lines_covered = 0
            total_lines = 0
            
            for package in root.findall('.//package'):
                for klass in package.findall('.//class'):
                    for line in klass.findall('.//line'):
                        total_lines += 1
                        if int(line.get('hits', '0')) > 0:
                            lines_covered += 1
                            
            return {
                'line_coverage': round(line_coverage, 1),
                'branch_coverage': round(branch_coverage, 1),
                'lines_covered': lines_covered,
                'total_lines': total_lines,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'line_coverage': 0.0,
                'branch_coverage': 0.0,
                'lines_covered': 0,
                'total_lines': 0,
                'error': str(e)
            }
            
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        
        # Aggregate all data
        test_results = self.aggregate_test_results()
        coverage_results = self.aggregate_coverage_reports()
        
        # Create comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': test_results,
            'coverage_results': coverage_results,
            'overall_health': self._calculate_overall_health(test_results, coverage_results)
        }
        
        return report
        
    def _calculate_overall_health(self, test_results: Dict, coverage_results: Dict) -> Dict[str, Any]:
        """Calculate overall project health metrics."""
        
        health = {
            'overall_score': 0,
            'test_health': 'unknown',
            'coverage_health': 'unknown',
            'recommendations': []
        }
        
        # Calculate test health
        test_summary = test_results.get('summary', {})
        if test_summary.get('total_tests', 0) > 0:
            success_rate = test_summary.get('overall_success_rate', 0)
            if success_rate >= 95:
                health['test_health'] = 'excellent'
            elif success_rate >= 85:
                health['test_health'] = 'good'
            elif success_rate >= 70:
                health['test_health'] = 'fair'
            else:
                health['test_health'] = 'poor'
                health['recommendations'].append('High test failure rate detected')
                
        # Calculate coverage health
        coverage_summary = coverage_results.get('summary', {})
        avg_coverage = coverage_summary.get('average_line_coverage', 0)
        if avg_coverage >= 80:
            health['coverage_health'] = 'excellent'
        elif avg_coverage >= 70:
            health['coverage_health'] = 'good'
        elif avg_coverage >= 60:
            health['coverage_health'] = 'fair'
        else:
            health['coverage_health'] = 'poor'
            health['recommendations'].append('Low test coverage detected')
            
        # Calculate overall score (0-100)
        test_score = min(test_summary.get('overall_success_rate', 0), 100)
        coverage_score = min(avg_coverage, 100)
        health['overall_score'] = round((test_score + coverage_score) / 2, 1)
        
        return health
        
    def save_report(self, report: Dict[str, Any], output_file: Optional[str] = None):
        """Save report to file."""
        
        if output_file is None:
            output_file = self.output_dir / 'comprehensive_test_report.json'
            
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"Report saved to {output_file}")
        
    def generate_html_report(self, report: Dict[str, Any], output_file: Optional[str] = None):
        """Generate HTML report."""
        
        if output_file is None:
            output_file = self.output_dir / 'comprehensive_test_report.html'
            
        # Ensure output directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        html_content = self._generate_html_content(report)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
            
        print(f"HTML report saved to {output_file}")
        
    def _generate_html_content(self, report: Dict[str, Any]) -> str:
        """Generate HTML content for report."""
        
        overall_health = report.get('overall_health', {})
        test_results = report.get('test_results', {})
        coverage_results = report.get('coverage_results', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Cross-Solution Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .health-score {{ font-size: 24px; font-weight: bold; }}
                .excellent {{ color: #28a745; }}
                .good {{ color: #17a2b8; }}
                .fair {{ color: #ffc107; }}
                .poor {{ color: #dc3545; }}
                .metric {{ margin: 10px 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Cross-Solution Test Report</h1>
                <p>Generated: {report.get('timestamp', 'Unknown')}</p>
            </div>
            
            <div class="section">
                <h2>Overall Health</h2>
                <div class="health-score {overall_health.get('test_health', 'unknown')}">
                    Score: {overall_health.get('overall_score', 0)}/100
                </div>
                <div class="metric">
                    <strong>Test Health:</strong> {overall_health.get('test_health', 'unknown')}
                </div>
                <div class="metric">
                    <strong>Coverage Health:</strong> {overall_health.get('coverage_health', 'unknown')}
                </div>
            </div>
            
            <div class="section">
                <h2>Test Results Summary</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Total Solutions</td>
                        <td>{test_results.get('summary', {}).get('total_solutions', 0)}</td>
                    </tr>
                    <tr>
                        <td>Solutions with Tests</td>
                        <td>{test_results.get('summary', {}).get('solutions_with_tests', 0)}</td>
                    </tr>
                    <tr>
                        <td>Total Tests</td>
                        <td>{test_results.get('summary', {}).get('total_tests', 0)}</td>
                    </tr>
                    <tr>
                        <td>Passed Tests</td>
                        <td>{test_results.get('summary', {}).get('passed_tests', 0)}</td>
                    </tr>
                    <tr>
                        <td>Failed Tests</td>
                        <td>{test_results.get('summary', {}).get('failed_tests', 0)}</td>
                    </tr>
                    <tr>
                        <td>Success Rate</td>
                        <td>{test_results.get('summary', {}).get('overall_success_rate', 0)}%</td>
                    </tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Coverage Summary</h2>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>Average Line Coverage</td>
                        <td>{coverage_results.get('summary', {}).get('average_line_coverage', 0)}%</td>
                    </tr>
                    <tr>
                        <td>Average Branch Coverage</td>
                        <td>{coverage_results.get('summary', {}).get('average_branch_coverage', 0)}%</td>
                    </tr>
                    <tr>
                        <td>Total Lines Covered</td>
                        <td>{coverage_results.get('summary', {}).get('total_lines_covered', 0)}</td>
                    </tr>
                    <tr>
                        <td>Total Lines</td>
                        <td>{coverage_results.get('summary', {}).get('total_lines', 0)}</td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        
        return html


def main():
    """Main entry point for test aggregator."""
    
    parser = argparse.ArgumentParser(description='Cross-solution test aggregator')
    parser.add_argument('--output', help='Output file for JSON report')
    parser.add_argument('--html', help='Output file for HTML report')
    parser.add_argument('--results-dir', default='test-results', help='Directory containing test results')
    parser.add_argument('--coverage-dir', default='coverage-reports', help='Directory containing coverage reports')
    
    args = parser.parse_args()
    
    aggregator = TestAggregator()
    aggregator.results_dir = Path(args.results_dir)
    aggregator.coverage_dir = Path(args.coverage_dir)
    
    # Generate comprehensive report
    report = aggregator.generate_comprehensive_report()
    
    # Save JSON report
    aggregator.save_report(report, args.output)
    
    # Generate HTML report if requested
    if args.html:
        aggregator.generate_html_report(report, args.html)
        
    # Print summary
    overall_health = report.get('overall_health', {})
    print(f"Overall Health Score: {overall_health.get('overall_score', 0)}/100")
    print(f"Test Health: {overall_health.get('test_health', 'unknown')}")
    print(f"Coverage Health: {overall_health.get('coverage_health', 'unknown')}")
    
    if overall_health.get('recommendations'):
        print("Recommendations:")
        for rec in overall_health.get('recommendations', []):
            print(f"  - {rec}")


if __name__ == '__main__':
    main()