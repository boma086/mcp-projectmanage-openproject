# Deployment Tests

Comprehensive deployment testing suite for all OpenProject MCP solutions. This framework tests Docker builds, service deployment, API compatibility, performance, and cross-solution integration.

## 🏗️ Architecture

### Test Components

1. **Comprehensive Deployment Tests** (`test_deployment_comprehensive.py`)
   - Individual solution deployment testing
   - Docker build validation
   - Health check verification
   - API endpoint testing
   - Resource usage monitoring
   - Concurrent request handling
   - Cross-solution compatibility

2. **Docker Compose Tests** (`test_docker_compose.py`)
   - Multi-service deployment testing
   - Service networking validation
   - Volume persistence testing
   - Environment variable validation
   - Service scaling capabilities
   - Load balancing verification

3. **Test Runner** (`run_deployment_tests.py`)
   - Orchestrates all test suites
   - Generates comprehensive reports
   - Provides CLI interface
   - Supports selective test execution

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Required Python packages (see `requirements.txt`)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start Docker daemon
sudo systemctl start docker
```

### Running Tests

#### Run All Tests
```bash
python run_deployment_tests.py
```

#### Run Specific Test Types
```bash
# Comprehensive deployment tests
python run_deployment_tests.py --test-type comprehensive

# Docker Compose tests
python run_deployment_tests.py --test-type docker_compose

# Performance tests
python run_deployment_tests.py --test-type performance

# Compatibility tests
python run_deployment_tests.py --test-type compatibility
```

#### Test Specific Solutions
```bash
# Test specific solutions
python run_deployment_tests.py --solutions solution-http solution-fastapi

# Test with custom compose file
python run_deployment_tests.py --compose-file custom-compose.yml
```

### Using pytest Directly

```bash
# Run comprehensive tests
pytest test_deployment_comprehensive.py -v

# Run Docker Compose tests
pytest test_docker_compose.py -v

# Run with HTML report
pytest test_deployment_comprehensive.py -v --html=report.html

# Run performance tests
pytest test_deployment_comprehensive.py::TestDeploymentPerformance -v
```

## 📊 Test Coverage

### Comprehensive Tests

- ✅ **Docker Build Validation**: All solutions can be built successfully
- ✅ **Service Deployment**: Solutions start and run correctly
- ✅ **Health Checks**: Services respond to health endpoints
- ✅ **API Endpoints**: All API endpoints are accessible and functional
- ✅ **Resource Usage**: Memory and CPU usage within acceptable limits
- ✅ **Concurrent Requests**: Services handle concurrent traffic appropriately
- ✅ **Cross-Compatibility**: Solutions provide compatible API responses

### Docker Compose Tests

- ✅ **Compose File Validation**: YAML structure is valid
- ✅ **Service Building**: All services build successfully
- ✅ **Service Startup**: Services start without errors
- ✅ **Networking**: Services can communicate with each other
- ✅ **Volume Management**: Data persistence works correctly
- ✅ **Environment Variables**: Configuration is properly applied
- ✅ **Service Scaling**: Services can be scaled up and down

### Performance Tests

- ✅ **Startup Time**: Services start within acceptable timeframes
- ✅ **Memory Efficiency**: Memory usage remains stable under load
- ✅ **Response Time**: API responses are fast enough
- ✅ **Throughput**: Services handle expected request volumes
- ✅ **Resource Utilization**: CPU and memory usage is efficient

## 🔧 Configuration

### Test Configuration

Tests can be configured through:

1. **Command Line Arguments**: Modify test behavior at runtime
2. **Environment Variables**: Set test parameters
3. **Configuration Files**: Use custom compose files

### Environment Variables

```bash
# Test configuration
export TEST_TIMEOUT=120
export TEST_CONCURRENT_REQUESTS=50
export TEST_MEMORY_LIMIT_MB=500
export TEST_CPU_LIMIT_PERCENT=50

# Docker configuration
export DOCKER_HOST=tcp://localhost:2376
export COMPOSE_PROJECT_NAME=openproject-test
```

### Custom Test Scenarios

Create custom test scenarios by modifying the test runner:

```python
# Example: Custom test scenario
runner = DeploymentTestRunner()
result = runner.run_test_suite(
    'comprehensive',
    solutions=['solution-http', 'solution-fastapi'],
    timeout=180
)
```

## 📈 Reporting

### Report Types

1. **HTML Reports**: Visual, interactive test reports
2. **JSON Reports**: Machine-readable test data
3. **Console Output**: Real-time test progress
4. **Log Files**: Detailed test execution logs

### Report Location

Reports are generated in the `deployment-test-reports/` directory:

```
deployment-test-reports/
├── deployment_test_report_20250903_123456.html
├── deployment_test_results_20250903_123456.json
└── deployment-tests.log
```

### Report Contents

- **Summary Statistics**: Total tests, pass/fail rates
- **Solution Results**: Individual solution performance
- **Performance Metrics**: Response times, resource usage
- **Compatibility Matrix**: Cross-solution compatibility
- **Error Analysis**: Detailed error information
- **Recommendations**: Improvement suggestions

## 🐛 Debugging

### Common Issues

1. **Docker Daemon Not Running**
   ```bash
   sudo systemctl start docker
   sudo systemctl status docker
   ```

2. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :8010
   lsof -i :8020
   
   # Kill conflicting processes
   sudo kill -9 <PID>
   ```

3. **Permission Issues**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Debug Mode

Run tests with debug output:

```bash
# Enable debug logging
export PYTHONPATH=.:$PYTHONPATH
export LOG_LEVEL=DEBUG

# Run with verbose output
python run_deployment_tests.py --test-type comprehensive --verbose

# Use pytest for detailed debugging
pytest test_deployment_comprehensive.py -v -s --tb=long
```

### Container Debugging

```bash
# View container logs
docker logs openproject-http-test
docker logs openproject-fastapi-test

# Access running container
docker exec -it openproject-fastapi-test bash

# Inspect container
docker inspect openproject-fastapi-test
```

## 🔄 CI/CD Integration

### GitHub Actions

The testing framework integrates with GitHub Actions through:

1. **Automated Testing**: Tests run on every PR and push
2. **Quality Gates**: Tests must pass for merges
3. **Report Generation**: Automated test reports
4. **Notifications**: Slack/email notifications on failures

### Example Workflow

```yaml
name: Deployment Tests

on: [push, pull_request]

jobs:
  deployment-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r deployment-tests/requirements.txt
          
      - name: Run deployment tests
        run: |
          python deployment-tests/run_deployment_tests.py
          
      - name: Upload test reports
        uses: actions/upload-artifact@v3
        with:
          name: deployment-test-reports
          path: deployment-test-reports/
```

## 📊 Performance Thresholds

### Acceptable Limits

- **Startup Time**: < 60 seconds
- **Memory Usage**: < 500MB per service
- **CPU Usage**: < 50% per service
- **Response Time**: < 1000ms for health endpoints
- **Error Rate**: < 5% under load
- **Concurrent Requests**: Handle 50+ concurrent requests

### Performance Regression Detection

The framework automatically detects performance regressions:

```python
# Example regression detection
if current_response_time > baseline_response_time * 1.5:
    raise PerformanceRegressionError("Response time increased by 50%")
```

## 🔒 Security Considerations

### Test Security

- **Isolated Test Environment**: Tests run in isolated containers
- **Clean Credentials**: Test credentials are separate from production
- **Network Isolation**: Test containers use isolated networks
- **Resource Limits**: Containers have resource constraints

### Best Practices

1. **Never use production credentials in tests**
2. **Clean up test containers after each run**
3. **Use separate test databases**
4. **Monitor resource usage during tests**
5. **Validate test data before use**

## 🤝 Contributing

### Adding New Tests

1. **Create test file**: Add new test files to `deployment-tests/`
2. **Follow naming convention**: Use `test_*.py` naming
3. **Add documentation**: Document test purpose and coverage
4. **Update requirements**: Add new dependencies to `requirements.txt`
5. **Test locally**: Verify tests work before committing

### Test Structure

```python
import pytest
import logging

logger = logging.getLogger(__name__)

@pytest.mark.deployment
class TestNewFeature:
    """Test new deployment feature."""
    
    def test_new_feature_deployment(self):
        """Test that new feature deploys correctly."""
        # Test implementation
        pass
```

## 📞 Support

### Getting Help

1. **Check logs**: Review `deployment-tests.log`
2. **Review documentation**: Check this README and inline comments
3. **Run with debug**: Use `--verbose` flag for detailed output
4. **Check environment**: Verify Docker and Python installations

### Common Commands

```bash
# View test help
python run_deployment_tests.py --help

# Check Docker status
docker ps
docker info

# Clean up test containers
docker system prune -f

# View resource usage
docker stats
```

## 📄 License

This deployment testing framework is part of the OpenProject MCP project and follows the same license terms.