# CI/CD Setup and Procedures

This document provides comprehensive documentation for the CI/CD automation implemented for the OpenProject MCP integration project.

## 📋 Overview

The CI/CD pipeline supports four solution architectures with unified automation, quality gates, security scanning, and deployment orchestration.

### 🎯 Key Features

- **Multi-Solution Support**: HTTP, FastAPI, FastMCP, and TypeScript solutions
- **Unified Workflows**: Reusable GitHub Actions workflows for consistency
- **Quality Gates**: Automated quality assessment with configurable thresholds
- **Security Scanning**: Comprehensive security checks across all solutions
- **Performance Testing**: Automated benchmarking and load testing
- **Deployment Automation**: Kubernetes-based deployment with rollback capabilities
- **Approval Processes**: Manual approval workflows for production deployments

## 🏗️ Architecture

### Pipeline Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Build & Test │───▶│ Quality Gates   │───▶│  Security Scan  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Performance Test│    │   Approval      │    │  Deployment     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   Monitoring    │
                                               └─────────────────┘
```

### Environment Strategy

- **Development**: Automated deployments on every commit
- **Staging**: Automated deployments with quality gates
- **Production**: Manual approval required with enhanced quality gates

## 🔧 Workflows

### Core Workflows

#### 1. Solution-Specific CI/CD
- **`ci-http.yml`**: HTTP solution pipeline
- **`ci-fastapi.yml`**: FastAPI solution pipeline  
- **`ci-typescript.yml`**: TypeScript solution pipeline
- **`ci-fastmcp.yml`**: FastMCP solution pipeline

Each includes:
- Build and test execution
- Security scanning
- Quality gate assessment
- Container image building
- Deployment to environment

#### 2. Unified CI/CD (`ci-unified.yml`)
Orchestrates all solutions with:
- Cross-solution integration tests
- Parallel execution
- Aggregated reporting
- Dependency management

#### 3. Environment Deployment (`deploy-environment.yml`)
Handles deployment to specific environments:
- Environment-specific configuration
- Kubernetes manifest generation
- Health checks and validation
- Rollback automation
- Monitoring setup

#### 4. Quality Gate (`quality-gate.yml`)
Enforces quality standards:
- Test coverage thresholds
- Security issue limits
- Performance benchmarks
- Automated scoring (0-100)

#### 5. Security & Performance (`security-performance.yml`)
Comprehensive testing:
- Multiple security scanners (Bandit, Safety, Semgrep, Trivy)
- Performance benchmarking
- Load testing with Locust and k6
- Cross-solution comparison

#### 6. Deployment Approval (`deployment-approval.yml`)
Manual approval process:
- GitHub Issues-based approval workflow
- Multi-level approvals required
- Automated expiration and cleanup
- Integration with deployment workflows

#### 7. Pipeline Validation (`validate-cicd.yml`)
Ensures pipeline health:
- Syntax validation
- Configuration verification
- Cross-solution consistency checks
- Automated health reporting

### Reusable Workflows

#### Build Workflow (`.github/workflows/reusable/build.yml`)
- Multi-language support (Python/TypeScript)
- Dependency caching
- Artifact management
- Build output standardization

#### Test Workflow (`.github/workflows/reusable/test.yml`)
- Unit, integration, and performance testing
- Matrix testing across Python versions
- Test result aggregation
- Coverage reporting

#### Security Scan Workflow (`.github/workflows/reusable/security-scan.yml`)
- Multiple scanner integration
- SARIF output generation
- Vulnerability assessment
- Security scoring

#### Docker Build Workflow (`.github/workflows/reusable/docker-build.yml`)
- Multi-architecture builds
- SBOM generation
- Container vulnerability scanning
- Registry publishing

#### Quality Gate Workflow (`.github/workflows/reusable/quality-gate.yml`)
- Configurable thresholds
- Multi-metric assessment
- Automated decision making
- Reporting and notifications

## 🚀 Deployment Process

### 1. Development Deployment
```bash
# Automatic on every commit to develop branch
# No approval required
# Full test suite execution
# Deployment to development environment
```

### 2. Staging Deployment
```bash
# Automatic on every commit to main branch
# Quality gates must pass
# Security scanning required
# Performance benchmarks evaluated
```

### 3. Production Deployment
```bash
# Manual approval required
# Enhanced quality gates
- Minimum 85% quality score
- 85% test coverage
- Zero critical security issues
- Stakeholder notification
- Rollback plan verification
```

### Deployment Commands

#### Manual Deployment
```bash
# Deploy all solutions to staging
./scripts/deploy-env.sh staging deploy

# Deploy specific solution to production
./scripts/deploy-env.sh production deploy solution-fastapi

# Rollback deployment
./scripts/deploy-env.sh production rollback solution-fastapi

# Verify deployment
./scripts/deploy-env.sh staging verify
```

#### Container Management
```bash
# Build all containers for staging
./scripts/build-containers.sh all staging

# Build specific solution for production
./scripts/build-containers.sh solution-fastapi production

# Build with custom registry
./scripts/build-containers.sh all staging docker.io
```

## 🔐 Security Integration

### Security Scanners

| Scanner | Target | Severity Levels | Output Format |
|---------|--------|-----------------|---------------|
| Bandit | Python code | Critical, High, Medium | SARIF, JSON |
| Safety | Python dependencies | Critical, High | JSON |
| Semgrep | All code | Critical, High, Medium | SARIF |
| Trivy | Container images | Critical, High, Medium | SARIF, JSON |
| Gitleaks | Secrets | Critical | JSON |
| npm audit | Node.js dependencies | Critical, High, Medium | JSON |

### Security Quality Gates

- **Critical Issues**: 0 allowed in production
- **High Issues**: Maximum 2 in staging, 0 in production
- **Medium Issues**: Maximum 5 in staging, 2 in production
- **Secrets**: 0 allowed in any environment

## 📊 Performance Testing

### Test Types

#### 1. Benchmark Testing
- Response time measurement
- Throughput assessment
- Resource utilization monitoring
- Cross-solution comparison

#### 2. Load Testing
- Concurrent user simulation
- Sustained load testing
- Memory leak detection
- Scalability assessment

#### 3. Stress Testing
- Maximum capacity determination
- Failure point identification
- Recovery capability testing
- Performance degradation analysis

### Performance Thresholds

| Metric | Development | Staging | Production |
|--------|-------------|---------|------------|
| Avg Response Time | < 500ms | < 300ms | < 200ms |
| Max Response Time | < 2000ms | < 1000ms | < 500ms |
| Throughput | > 100 req/s | > 500 req/s | > 1000 req/s |
| Error Rate | < 5% | < 2% | < 1% |
| P95 Response Time | < 1000ms | < 500ms | < 300ms |

## 🎛️ Quality Gates

### Quality Score Calculation

The quality score (0-100) is calculated as follows:

```
Quality Score = (Test Coverage × 0.4) + (Security Score × 0.3) + (Performance Score × 0.2) + (Test Success Rate × 0.1)
```

### Environment-Specific Thresholds

| Environment | Minimum Quality Score | Test Coverage | Security Issues | Performance Score |
|-------------|---------------------|---------------|-----------------|-------------------|
| Development | 70% | 70% | 5 high | 60% |
| Staging | 80% | 80% | 2 high | 70% |
| Production | 85% | 85% | 0 critical | 80% |

### Quality Gate Outcomes

- **✅ PASS**: All thresholds met → Deployment approved
- **⚠️ WARNING**: Some thresholds not met → Manual review required
- **❌ FAIL**: Critical thresholds not met → Deployment blocked

## 🔄 Approval Process

### Production Approval Workflow

1. **Request Creation**
   - Submit deployment request via GitHub Actions
   - Specify environment, solutions, and description
   - Required approvers automatically assigned

2. **Approval Issue**
   - GitHub Issue automatically created
   - Includes deployment checklist and risk assessment
   - Notifications sent to required approvers

3. **Approval Process**
   - Approvers review request
   - Comment `/approve` to authorize
   - Comment `/reject` to block
   - Comment `/request-changes` to request modifications

4. **Decision Execution**
   - Automatic deployment on approval
   - Blocked on rejection
   - Expired after 7 days without decision

### Approval Roles

| Role | Development | Staging | Production |
|------|-------------|---------|------------|
| Required Approvers | None | Tech Lead | Admin + Tech Lead + Ops Lead |
| Approval Duration | Immediate | 24 hours | 72 hours |
| Expiration | None | 3 days | 7 days |

## 📈 Monitoring and Observability

### Monitoring Components

#### 1. Application Metrics
- Request rate and response times
- Error rates and status codes
- Resource utilization (CPU, memory)
- Custom business metrics

#### 2. Infrastructure Metrics
- Pod health and restarts
- Resource quotas and limits
- Network traffic and latency
- Storage usage

#### 3. Security Metrics
- Vulnerability scan results
- Security score trends
- Compliance status
- Incident response times

### Dashboard Integration

Metrics are automatically integrated with:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and alerting
- **Kibana**: Log aggregation and analysis
- **AlertManager**: Alert routing and notification

## 🛠️ Maintenance and Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Check build logs
gh run view --log <run-id>

# Validate workflow syntax
python scripts/validate-cicd.py --output validation.json

# Check dependency issues
cd solution-fastapi && pip check
```

#### 2. Test Failures
```bash
# Run specific test suite
python -m pytest tests/unit/ -v

# Check test coverage
python -m pytest --cov=src tests/

# Debug integration tests
python test-utils/python/cross_solution_tester.py --environment development --test-type integration
```

#### 3. Deployment Issues
```bash
# Check deployment status
./scripts/deploy-env.sh staging status

# View pod logs
kubectl logs -n openproject-staging deployment/solution-fastapi

# Check health endpoints
curl http://staging.openproject-mcp.local/fastapi/health
```

#### 4. Security Scan Failures
```bash
# Run security scan locally
bandit -r solution-fastapi/src/
safety check --file solution-fastapi/requirements.txt

# Check container security
trivy image ghcr.io/your-repo/solution-fastapi:staging
```

### Maintenance Tasks

#### 1. Weekly Maintenance
- Review pipeline performance metrics
- Update security scanner definitions
- Clean up old artifacts and logs
- Validate backup procedures

#### 2. Monthly Maintenance
- Update CI/CD dependencies
- Review and optimize workflows
- Update quality gate thresholds
- Test disaster recovery procedures

#### 3. Quarterly Maintenance
- Major version upgrades
- Architecture review and optimization
- Security audit and compliance check
- Performance benchmark review

## 📚 Best Practices

### 1. Workflow Development
- Use reusable workflows for consistency
- Implement proper error handling and timeouts
- Include comprehensive logging and debugging
- Follow GitHub Actions security best practices

### 2. Security Practices
- Never hardcode secrets in workflows
- Use GitHub Secrets for sensitive data
- Implement least privilege permissions
- Regular security scanning and updates

### 3. Performance Optimization
- Use caching for dependencies and builds
- Parallelize independent tasks
- Optimize container image sizes
- Monitor and optimize resource usage

### 4. Monitoring and Alerting
- Set up comprehensive monitoring
- Configure appropriate alert thresholds
- Establish incident response procedures
- Regular review of metrics and logs

## 🔗 Integration Points

### 1. External Systems
- **GitHub**: Repository management and Actions
- **Docker Hub/GHCR**: Container registry
- **Kubernetes**: Container orchestration
- **Prometheus/Grafana**: Monitoring and alerting
- **Slack/Email**: Notifications and approvals

### 2. Internal Tools
- **Cross-solution tester**: Integration testing
- **Test aggregator**: Results aggregation
- **Performance benchmarks**: Load testing
- **Security scanners**: Vulnerability assessment

### 3. API Endpoints
- **GitHub API**: Workflow management
- **Kubernetes API**: Deployment control
- **Monitoring APIs**: Metrics collection
- **Notification APIs**: Alert delivery

## 🚀 Getting Started

### 1. Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd mcp-projectmanage-openproject

# Set up GitHub Secrets
gh secret set KUBECONFIG
gh secret set OPENPROJECT_URL
gh secret set OPENPROJECT_API_KEY

# Configure repository variables
gh variable set PRODUCTION_APPROVERS "admin,tech-lead,ops-lead"
gh variable set STAGING_APPROVERS "tech-lead"
```

### 2. First Deployment
```bash
# Validate CI/CD setup
python scripts/validate-cicd.py

# Deploy to development
./scripts/deploy-env.sh development deploy

# Run validation tests
python test-utils/python/cross_solution_tester.py --environment development --test-type integration
```

### 3. Production Deployment
```bash
# Request production approval
gh workflow run deployment-approval.yml \
  --ref main \
  -f environment=production \
  -f deployment-request-id=prod-001 \
  -f description="Production deployment v1.0.0"

# Monitor approval process
gh issue list --label "deployment,approval-request,production"

# After approval, verify deployment
./scripts/deploy-env.sh production verify
```

## 📞 Support and Resources

### Documentation
- [CI/CD Architecture](CICD_ARCHITECTURE.md)
- [Solution Documentation](docs/)
- [API Documentation](docs/api/)
- [Troubleshooting Guide](docs/troubleshooting.md)

### Tools and Utilities
- **Validation Script**: `scripts/validate-cicd.py`
- **Deployment Scripts**: `scripts/deploy*.sh`
- **Test Utilities**: `test-utils/python/`
- **Performance Testing**: `performance-tests/`

### Monitoring and Alerting
- **Pipeline Status**: GitHub Actions tab
- **Application Health**: Grafana dashboard
- **Security Status**: Security scan reports
- **Performance Metrics**: Performance benchmark reports

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|----------|
| 1.0.0 | 2024-01-XX | Initial CI/CD automation implementation |
| 1.1.0 | 2024-01-XX | Added security scanning integration |
| 1.2.0 | 2024-01-XX | Enhanced performance testing |
| 1.3.0 | 2024-01-XX | Implemented approval workflows |
| 1.4.0 | 2024-01-XX | Added comprehensive validation |

---

*This documentation is automatically generated as part of the CI/CD pipeline implementation. Last updated: $(date)*