#!/bin/bash
set -euo pipefail

# Production Automation Script for MCP OpenProject Solutions
# This script provides comprehensive automation for production deployments

# Configuration
NAMESPACE="mcp-openproject"
CLUSTER_NAME="mcp-openproject-prod"
REGION="us-west-2"
BACKUP_BUCKET="mcp-openproject-backups"
MONITORING_ENABLED=true
BACKUP_ENABLED=true
ROLLBACK_ENABLED=true
SECURITY_ENABLED=true
HA_ENABLED=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Environment validation
validate_environment() {
    log "Validating production environment..."
    
    # Check required tools
    local required_tools=("kubectl" "aws" "helm" "istioctl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            error "Required tool '$tool' not found"
        fi
    done
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &>/dev/null; then
        error "AWS credentials not configured"
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &>/dev/null; then
        error "Kubernetes cluster not accessible"
    fi
    
    log "Environment validation completed"
}

# Security hardening
apply_security_hardening() {
    if [ "$SECURITY_ENABLED" != true ]; then
        log "Security hardening disabled, skipping..."
        return
    fi
    
    log "Applying security hardening configurations..."
    
    # Apply security policies
    kubectl apply -f k8s/security-hardening.yaml
    
    # Apply network policies
    kubectl apply -f k8s/production-ingress.yaml
    
    # Wait for security policies to be applied
    sleep 10
    
    # Verify security policies
    local security_policies=("restricted-psp" "production-network-policy")
    for policy in "${security_policies[@]}"; do
        if ! kubectl get networkpolicy "$policy" -n "$NAMESPACE" &>/dev/null; then
            warn "Security policy $policy not found"
        fi
    done
    
    log "Security hardening completed"
}

# High availability setup
setup_high_availability() {
    if [ "$HA_ENABLED" != true ]; then
        log "High availability setup disabled, skipping..."
        return
    fi
    
    log "Setting up high availability configurations..."
    
    # Apply HA configurations
    kubectl apply -f k8s/high-availability.yaml
    
    # Wait for HA components to be ready
    kubectl wait --for=condition=ready pod -l app=postgres-ha -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis-cluster -n "$NAMESPACE" --timeout=300s
    
    # Initialize Redis cluster
    log "Initializing Redis cluster..."
    kubectl exec -it redis-cluster-0 -n "$NAMESPACE" -- redis-cli --cluster create \
        $(kubectl get pods -l app=redis-cluster -n "$NAMESPACE" -o jsonpath='{range.items[*]}{.podIP}:6379 {end}')
    
    log "High availability setup completed"
}

# Monitoring setup
setup_monitoring() {
    if [ "$MONITORING_ENABLED" != true ]; then
        log "Monitoring setup disabled, skipping..."
        return
    fi
    
    log "Setting up production monitoring..."
    
    # Apply monitoring configurations
    kubectl apply -f k8s/production-monitoring.yaml
    
    # Wait for monitoring components to be ready
    kubectl wait --for=condition=ready pod -l app=prometheus -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=alertmanager -n "$NAMESPACE" --timeout=300s
    
    # Setup Grafana dashboards
    log "Setting up Grafana dashboards..."
    kubectl apply -f monitoring/grafana/dashboards/
    
    log "Monitoring setup completed"
}

# Backup setup
setup_backup() {
    if [ "$BACKUP_ENABLED" != true ]; then
        log "Backup setup disabled, skipping..."
        return
    fi
    
    log "Setting up backup and disaster recovery..."
    
    # Apply backup configurations
    kubectl apply -f k8s/backup-disaster-recovery.yaml
    
    # Create S3 bucket for backups
    if ! aws s3 ls "s3://$BACKUP_BUCKET" &>/dev/null; then
        aws s3 mb "s3://$BACKUP_BUCKET" --region "$REGION"
    fi
    
    # Setup backup retention policies
    aws s3api put-bucket-lifecycle-configuration \
        --bucket "$BACKUP_BUCKET" \
        --lifecycle-configuration '{
            "Rules": [
                {
                    "ID": "DeleteOldBackups",
                    "Status": "Enabled",
                    "Filter": {},
                    "Expiration": { "Days": 90 }
                }
            ]
        }'
    
    log "Backup setup completed"
}

# Ingress setup
setup_ingress() {
    log "Setting up production ingress..."
    
    # Apply ingress configurations
    kubectl apply -f k8s/production-ingress.yaml
    
    # Wait for ingress controller to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --timeout=300s
    
    # Get ingress endpoint
    local ingress_endpoint=$(kubectl get ingress production-ingress -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    if [ -n "$ingress_endpoint" ]; then
        log "Ingress endpoint: $ingress_endpoint"
    fi
    
    log "Ingress setup completed"
}

# Certificate management
setup_certificates() {
    log "Setting up SSL certificates..."
    
    # Install cert-manager
    helm repo add jetstack https://charts.jetstack.io
    helm repo update
    helm install cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s
    
    # Create cluster issuer
    kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@mcp-openproject.example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    
    log "Certificate setup completed"
}

# Infrastructure deployment
deploy_infrastructure() {
    log "Deploying production infrastructure..."
    
    # Apply namespace and basic configurations
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/secrets.yaml
    kubectl apply -f k8s/configmaps.yaml
    kubectl apply -f k8s/infrastructure.yaml
    
    # Wait for infrastructure to be ready
    kubectl wait --for=condition=ready pod -l app=postgres -n "$NAMESPACE" --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n "$NAMESPACE" --timeout=300s
    
    log "Infrastructure deployment completed"
}

# Application deployment
deploy_applications() {
    log "Deploying applications..."
    
    # Deploy all solutions
    local solutions=("http-solution" "fastapi-solution" "fastmcp-solution" "typescript-solution")
    for solution in "${solutions[@]}"; do
        log "Deploying $solution..."
        
        # Apply solution-specific configurations
        if [ -f "k8s/$solution.yaml" ]; then
            kubectl apply -f "k8s/$solution.yaml"
        fi
        
        # Wait for deployment to be ready
        kubectl wait --for=condition=ready pod -l app="$solution" -n "$NAMESPACE" --timeout=300s
    done
    
    log "Application deployment completed"
}

# Smoke tests
run_smoke_tests() {
    log "Running smoke tests..."
    
    # Test application endpoints
    local endpoints=(
        "http-solution-service:80/health"
        "fastapi-solution-service:80/health"
        "fastmcp-solution-service:80/health"
        "typescript-solution-service:80/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if ! kubectl run smoke-test --rm -i --restart=Never --image=busybox \
            -- wget -q -O - "http://$endpoint" &>/dev/null; then
            error "Smoke test failed for $endpoint"
        fi
    done
    
    log "Smoke tests completed"
}

# Performance tests
run_performance_tests() {
    log "Running performance tests..."
    
    # Install k6
    helm repo add k6 https://k6.io/charts
    helm repo update
    helm install k6 k6/k6 --namespace k6 --create-namespace
    
    # Run performance test
    kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: performance-test
  namespace: k6
spec:
  template:
    spec:
      containers:
      - name: k6
        image: loadimpact/k6:latest
        command: ["k6", "run", "--vus", "10", "--duration", "30s", "-"]
        stdin: true
      restartPolicy: Never
EOF
    
    # Wait for test to complete
    kubectl wait --for=condition=complete job/performance-test -n k6 --timeout=300s
    
    # Get test results
    kubectl logs job/performance-test -n k6
    
    log "Performance tests completed"
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary resources..."
    
    # Clean up test resources
    kubectl delete job performance-test -n k6 --ignore-not-found=true
    
    log "Cleanup completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Check all pods are running
    local non_running_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep -v "Running" | wc -l)
    if [ "$non_running_pods" -gt 0 ]; then
        error "Found $non_running_pods non-running pods"
    fi
    
    # Check all services are accessible
    local services=("http-solution-service" "fastapi-solution-service" "fastmcp-solution-service" "typescript-solution-service")
    for service in "${services[@]}"; do
        if ! kubectl get service "$service" -n "$NAMESPACE" &>/dev/null; then
            error "Service $service not found"
        fi
    done
    
    # Check ingress is working
    if ! kubectl get ingress production-ingress -n "$NAMESPACE" &>/dev/null; then
        error "Production ingress not found"
    fi
    
    log "Health check completed"
}

# Main deployment function
main() {
    log "Starting production deployment automation..."
    
    # Parse arguments
    local skip_security=false
    local skip_ha=false
    local skip_monitoring=false
    local skip_backup=false
    local skip_tests=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-security)
                skip_security=true
                SECURITY_ENABLED=false
                shift
                ;;
            --skip-ha)
                skip_ha=true
                HA_ENABLED=false
                shift
                ;;
            --skip-monitoring)
                skip_monitoring=true
                MONITORING_ENABLED=false
                shift
                ;;
            --skip-backup)
                skip_backup=true
                BACKUP_ENABLED=false
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-security    Skip security hardening"
                echo "  --skip-ha          Skip high availability setup"
                echo "  --skip-monitoring  Skip monitoring setup"
                echo "  --skip-backup      Skip backup setup"
                echo "  --skip-tests       Skip tests"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Validate environment
    validate_environment
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Setup high availability
    if [ "$skip_ha" != true ]; then
        setup_high_availability
    fi
    
    # Setup monitoring
    if [ "$skip_monitoring" != true ]; then
        setup_monitoring
    fi
    
    # Setup backup
    if [ "$skip_backup" != true ]; then
        setup_backup
    fi
    
    # Apply security hardening
    if [ "$skip_security" != true ]; then
        apply_security_hardening
    fi
    
    # Setup ingress
    setup_ingress
    
    # Setup certificates
    setup_certificates
    
    # Deploy applications
    deploy_applications
    
    # Run tests
    if [ "$skip_tests" != true ]; then
        run_smoke_tests
        run_performance_tests
    fi
    
    # Health check
    health_check
    
    # Cleanup
    cleanup
    
    log "Production deployment automation completed successfully!"
    
    # Display deployment summary
    echo -e "${BLUE}=== DEPLOYMENT SUMMARY ===${NC}"
    echo -e "${GREEN}Namespace: $NAMESPACE${NC}"
    echo -e "${GREEN}Cluster: $CLUSTER_NAME${NC}"
    echo -e "${GREEN}Region: $REGION${NC}"
    echo -e "${GREEN}Security: ${SECURITY_ENABLED:-enabled}${NC}"
    echo -e "${GREEN}High Availability: ${HA_ENABLED:-enabled}${NC}"
    echo -e "${GREEN}Monitoring: ${MONITORING_ENABLED:-enabled}${NC}"
    echo -e "${GREEN}Backup: ${BACKUP_ENABLED:-enabled}${NC}"
    echo -e "${BLUE}============================${NC}"
}

# Run main function
main "$@"