# CI/CD Quick Reference

This guide provides quick access to common CI/CD operations and commands.

## 🚀 Quick Start

### Basic Commands
```bash
# Validate entire CI/CD setup
python scripts/validate-cicd.py

# Deploy all solutions to staging
./scripts/deploy-env.sh staging deploy

# Build all containers for staging
./scripts/build-containers.sh all staging

# Run cross-solution tests
python test-utils/python/cross_solution_tester.py --environment staging --test-type integration
```

## 📋 Solution-Specific Operations

### HTTP Solution
```bash
# Build and test
cd solution-http
python -m pytest tests/
python -m src.main &

# Deploy to staging
./scripts/deploy-env.sh staging deploy solution-http

# Build container
./scripts/build-containers.sh solution-http staging
```

### FastAPI Solution
```bash
# Build and test
cd solution-fastapi
python -m pytest tests/
python app/main.py &

# Deploy to staging
./scripts/deploy-env.sh staging deploy solution-fastapi

# Build container
./scripts/build-containers.sh solution-fastapi staging
```

### TypeScript Solution
```bash
# Build and test
cd solution-typescript
npm test
npm start &

# Deploy to staging
./scripts/deploy-env.sh staging deploy solution-typescript

# Build container
./scripts/build-containers.sh solution-typescript staging
```

## 🔧 Environment Management

### Development
```bash
# Deploy to development
./scripts/deploy-env.sh development deploy

# Run development tests
python test-utils/python/cross_solution_tester.py --environment development --test-type unit

# Check development status
./scripts/deploy-env.sh development status
```

### Staging
```bash
# Deploy to staging
./scripts/deploy-env.sh staging deploy

# Run staging integration tests
python test-utils/python/cross_solution_tester.py --environment staging --test-type integration

# Verify staging deployment
./scripts/deploy-env.sh staging verify
```

### Production
```bash
# Request production deployment
gh workflow run deployment-approval.yml \
  --ref main \
  -f environment=production \
  -f deployment-request-id=prod-$(date +%Y%m%d-%H%M%S) \
  -f description="Production deployment"

# Check production status
./scripts/deploy-env.sh production status

# Rollback production deployment
./scripts/deploy-env.sh production rollback
```

## 🐛 Troubleshooting

### Common Issues
```bash
# Check workflow status
gh run list --limit 10

# View specific workflow run
gh run view <run-id>

# Download workflow artifacts
gh run download <run-id>

# Check failed workflow logs
gh run view --log <run-id>
```

### Build Issues
```bash
# Validate workflow syntax
python scripts/validate-cicd.py --output validation.json

# Check dependencies
cd solution-fastapi && pip check

# Clean build cache
gh cache list
gh cache delete --all
```

### Test Issues
```bash
# Run specific tests
python -m pytest tests/unit/test_main.py -v

# Check test coverage
python -m pytest --cov=src tests/ --cov-report=html

# Debug test failures
python -m pytest tests/ -v --tb=short
```

### Deployment Issues
```bash
# Check deployment status
kubectl get deployments -n openproject-staging

# View pod logs
kubectl logs -n openproject-staging deployment/solution-fastapi

# Check service status
kubectl get services -n openproject-staging

# Port forward for local testing
kubectl port-forward -n openproject-staging service/solution-fastapi-service 8020:80
```

## 🔒 Security Operations

### Security Scanning
```bash
# Run Bandit (Python)
bandit -r solution-fastapi/src/ -f json -o bandit-report.json

# Run Safety (dependencies)
safety check --file solution-fastapi/requirements.txt --json --output safety-report.json

# Run Trivy (containers)
trivy image --format json --output trivy-report.json ghcr.io/your-repo/solution-fastapi:staging

# Run Semgrep
semgrep --config=auto --json --output semgrep-report.json solution-fastapi/src/
```

### Security Validation
```bash
# Check for secrets
gitleaks detect --source . --report-format json --report-path gitleaks-report.json

# Validate container security
trivy image --severity CRITICAL,HIGH ghcr.io/your-repo/solution-fastapi:staging

# Check npm audit (TypeScript)
cd solution-typescript && npm audit --json > npm-audit-report.json
```

## 📊 Performance Testing

### Benchmark Testing
```bash
# Run performance benchmarks
python performance-tests/run_benchmarks.py \
  --solution solution-fastapi \
  --duration 60 \
  --compare \
  --report

# Run specific solution benchmark
python performance-tests/run_benchmarks.py \
  --solution solution-fastapi \
  --duration 30 \
  --output benchmark-fastapi.json
```

### Load Testing
```bash
# Run Locust load testing
locust --host=http://localhost:8020 \
       --users=50 \
       --spawn-rate=5 \
       --run-time=2m \
       --headless \
       --html locust-report.html

# Run k6 stress testing
k6 run k6-test.js --out json=k6-results.json
```

## 📈 Monitoring

### Application Metrics
```bash
# Check health endpoints
curl http://localhost:8010/health
curl http://localhost:8020/health
curl http://localhost:8030/health
curl http://localhost:8040/health

# Check metrics endpoints
curl http://localhost:8020/metrics

# Check readiness
curl http://localhost:8020/health/ready
```

### Infrastructure Metrics
```bash
# Check pod status
kubectl get pods -n openproject-staging

# Check resource usage
kubectl top pods -n openproject-staging

# Check events
kubectl get events -n openproject-staging --sort-by='.metadata.creationTimestamp'

# Check HPA status
kubectl get hpa -n openproject-staging
```

## 🔄 Approval Process

### Request Deployment
```bash
# Create deployment request
gh workflow run deployment-approval.yml \
  --ref main \
  -f environment=production \
  -f deployment-request-id=deploy-$(date +%Y%m%d-%H%M%S) \
  -f description="Production deployment v1.0.0" \
  -f approvers="admin,tech-lead"
```

### Approve Deployment
```bash
# Find approval issue
gh issue list --label "deployment,approval-request,production"

# Approve deployment (comment on issue)
gh issue comment <issue-number> --body "/approve"

# Reject deployment
gh issue comment <issue-number> --body "/reject Security concerns identified"

# Request changes
gh issue comment <issue-number> --body "/request-changes Please add rollback plan"
```

## 📊 Reporting

### Test Reports
```bash
# Generate test aggregation report
python test-reports/test_aggregator.py \
  --output test-report.json \
  --html test-report.html

# Generate performance report
python performance-tests/run_benchmarks.py \
  --solution all \
  --duration 60 \
  --report \
  --output performance-report.json
```

### Quality Reports
```bash
# Run quality gate assessment
gh workflow run quality-gate.yml \
  --ref main \
  -f environment=production \
  -f coverage-threshold=85 \
  -f security-threshold=0

# Generate validation report
python scripts/validate-cicd.py --output validation-report.json
```

## 🛠️ Maintenance

### Cleanup Operations
```bash
# Clean up old artifacts
gh cache list --expired
gh cache delete --all

# Clean up old deployment requests
find deployment-requests -name "*.json" -mtime +30 -delete

# Clean up old test results
find test-results -name "*.json" -mtime +7 -delete

# Clean up Docker images
docker system prune -f
```

### Updates and Upgrades
```bash
# Update GitHub Actions
git pull origin main
gh workflow list
gh workflow rerun <workflow-id>

# Update dependencies
cd solution-fastapi && pip install -r requirements.txt --upgrade
cd solution-typescript && npm update

# Update security scanners
pip install --upgrade bandit safety semgrep
npm update -g npm-audit-resolver snyk
```

## 🚨 Emergency Procedures

### Emergency Rollback
```bash
# Immediate rollback
./scripts/deploy-env.sh production rollback

# Rollback specific solution
./scripts/deploy-env.sh production rollback solution-fastapi

# Check rollback status
./scripts/deploy-env.sh production status

# Verify rollback
./scripts/deploy-env.sh production verify
```

### Emergency Shutdown
```bash
# Scale down deployments
kubectl scale deployment solution-fastapi --replicas=0 -n openproject-production

# Stop all solutions
for solution in solution-http solution-fastapi solution-fastmcp solution-typescript; do
  kubectl scale deployment $solution --replicas=0 -n openproject-production
done

# Emergency backup
kubectl get all -n openproject-production -o yaml > emergency-backup.yaml
```

## 📞 Support

### Get Help
```bash
# Check documentation
cat docs/CICD_SETUP.md
cat docs/troubleshooting.md

# Check workflow help
gh workflow view --help

# Check GitHub CLI help
gh --help
gh run --help
```

### Contact Information
- **CI/CD Issues**: Create GitHub issue with `ci-cd` label
- **Production Emergencies**: Contact on-call engineer
- **Security Issues**: Create confidential GitHub issue
- **Performance Issues**: Use performance monitoring dashboard

---

*This quick reference guide is part of the CI/CD automation implementation. For detailed information, see the full [CI/CD Setup documentation](CICD_SETUP.md).*