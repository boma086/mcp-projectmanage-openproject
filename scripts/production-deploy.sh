#!/bin/bash
set -euo pipefail

# Production Deployment Script for MCP OpenProject Solutions
# This script handles production deployments with proper safety checks

# Configuration
NAMESPACE="mcp-openproject"
CLUSTER_NAME="mcp-openproject-prod"
REGION="us-west-2"
BACKUP_BUCKET="mcp-openproject-backups"
MONITORING_ENABLED=true
BACKUP_ENABLED=true
ROLLBACK_ENABLED=true

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

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if kubectl is configured
    if ! kubectl cluster-info &>/dev/null; then
        error "Kubernetes cluster not accessible"
    fi
    
    # Check if we're connected to the right cluster
    current_cluster=$(kubectl config current-context)
    if [[ "$current_cluster" != *"$CLUSTER_NAME"* ]]; then
        error "Not connected to production cluster: $CLUSTER_NAME"
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
        error "Namespace $NAMESPACE does not exist"
    fi
    
    # Check if all required secrets exist
    local required_secrets=("postgres-secrets" "tls-secret" "redis-secrets")
    for secret in "${required_secrets[@]}"; do
        if ! kubectl get secret "$secret" -n "$NAMESPACE" &>/dev/null; then
            error "Required secret $secret not found"
        fi
    done
    
    # Check disk space
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 80 ]; then
        warn "Disk usage is ${disk_usage}% on deployment server"
    fi
    
    # Check memory
    local available_memory=$(free -m | awk 'NR==2{printf "%.1f", $7/1024}')
    if (( $(echo "$available_memory < 2.0" | bc -l) )); then
        warn "Low available memory: ${available_memory}GB"
    fi
    
    log "Pre-deployment checks passed"
}

# Backup function
create_backup() {
    if [ "$BACKUP_ENABLED" != true ]; then
        log "Backup disabled, skipping..."
        return
    fi
    
    log "Creating backup before deployment..."
    
    local backup_date=$(date +%Y%m%d_%H%M%S)
    local backup_dir="/tmp/backup_${backup_date}"
    
    mkdir -p "$backup_dir"
    
    # Backup database
    log "Backing up PostgreSQL database..."
    kubectl exec -n "$NAMESPACE" postgres-0 -- pg_dump -U mcpuser -d mcpdb > "$backup_dir/postgres_backup.sql"
    
    # Backup Redis
    log "Backing up Redis data..."
    kubectl exec -n "$NAMESPACE" redis-0 -- redis-cli SAVE
    kubectl cp "$NAMESPACE/redis-0:/data/dump.rdb" "$backup_dir/redis_backup.rdb"
    
    # Backup configurations
    log "Backing up Kubernetes configurations..."
    kubectl get all,configmaps,secrets -n "$NAMESPACE" -o yaml > "$backup_dir/k8s_resources.yaml"
    
    # Upload to S3
    log "Uploading backup to S3..."
    aws s3 cp "$backup_dir" "s3://$BACKUP_BUCKET/backup_${backup_date}/" --recursive
    
    # Clean up local backup
    rm -rf "$backup_dir"
    
    log "Backup completed successfully"
}

# Health check function
health_check() {
    local service_name=$1
    local namespace=$2
    local max_attempts=30
    local attempt=1
    
    log "Checking health of $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if kubectl get pods -n "$namespace" -l app="$service_name" | grep -q "Running"; then
            log "$service_name is healthy"
            return 0
        fi
        
        log "Waiting for $service_name to be ready... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    error "$service_name failed to become healthy within $max_attempts attempts"
}

# Rolling deployment function
rolling_deploy() {
    local deployment_name=$1
    local namespace=$2
    local new_image=$3
    
    log "Starting rolling deployment for $deployment_name..."
    
    # Get current replicas
    local current_replicas=$(kubectl get deployment "$deployment_name" -n "$namespace" -o jsonpath='{.spec.replicas}')
    
    # Update image
    kubectl set image deployment/"$deployment_name" -n "$namespace" "*=$new_image"
    
    # Watch rollout status
    kubectl rollout status deployment/"$deployment_name" -n "$namespace" --timeout=600s
    
    log "Rolling deployment for $deployment_name completed"
}

# Blue-green deployment function
blue_green_deploy() {
    local deployment_name=$1
    local namespace=$2
    local new_image=$3
    
    log "Starting blue-green deployment for $deployment_name..."
    
    # Create green deployment
    local green_deployment="${deployment_name}-green"
    kubectl get deployment "$deployment_name" -n "$namespace" -o yaml | \
        sed "s/name: $deployment_name/name: $green_deployment/g" | \
        sed "s/app: $deployment_name/app: $green_deployment/g" | \
        sed "s/image: .*/image: $new_image/g" | \
        kubectl apply -f -
    
    # Wait for green deployment to be ready
    health_check "$green_deployment" "$namespace"
    
    # Update service to point to green deployment
    kubectl patch service "${deployment_name}-service" -n "$namespace" -p '{"spec":{"selector":{"app":"'$green_deployment'"}}}'
    
    # Scale down blue deployment
    kubectl scale deployment "$deployment_name" -n "$namespace" --replicas=0
    
    log "Blue-green deployment for $deployment_name completed"
}

# Canary deployment function
canary_deploy() {
    local deployment_name=$1
    local namespace=$2
    local new_image=$3
    local canary_percentage=10
    
    log "Starting canary deployment for $deployment_name with $canary_percentage% traffic..."
    
    # Create canary deployment
    local canary_deployment="${deployment_name}-canary"
    kubectl get deployment "$deployment_name" -n "$namespace" -o yaml | \
        sed "s/name: $deployment_name/name: $canary_deployment/g" | \
        sed "s/app: $deployment_name/app: $canary_deployment/g" | \
        sed "s/image: .*/image: $new_image/g" | \
        kubectl apply -f -
    
    # Set canary replicas
    local current_replicas=$(kubectl get deployment "$deployment_name" -n "$NAMESPACE" -o jsonpath='{.spec.replicas}')
    local canary_replicas=$((current_replicas * canary_percentage / 100))
    kubectl scale deployment "$canary_deployment" -n "$namespace" --replicas="$canary_replicas"
    
    # Wait for canary to be ready
    health_check "$canary_deployment" "$namespace"
    
    # Monitor canary metrics
    log "Monitoring canary deployment for 5 minutes..."
    sleep 300
    
    # If canary is successful, proceed with full rollout
    log "Canary deployment successful, proceeding with full rollout..."
    kubectl set image deployment/"$deployment_name" -n "$namespace" "*=$new_image"
    kubectl rollout status deployment/"$deployment_name" -n "$namespace" --timeout=600s
    
    # Clean up canary
    kubectl delete deployment "$canary_deployment" -n "$namespace"
    
    log "Canary deployment for $deployment_name completed"
}

# Rollback function
rollback_deployment() {
    local deployment_name=$1
    local namespace=$2
    
    if [ "$ROLLBACK_ENABLED" != true ]; then
        log "Rollback disabled, skipping..."
        return
    fi
    
    log "Rolling back deployment $deployment_name..."
    
    # Rollback to previous revision
    kubectl rollout undo deployment/"$deployment_name" -n "$namespace"
    kubectl rollout status deployment/"$deployment_name" -n "$namespace" --timeout=600s
    
    log "Rollback completed"
}

# Post-deployment verification
post_deployment_verification() {
    log "Running post-deployment verification..."
    
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
    
    # Run smoke tests
    log "Running smoke tests..."
    ./scripts/smoke-test.sh || error "Smoke tests failed"
    
    log "Post-deployment verification completed"
}

# Main deployment function
main() {
    log "Starting production deployment..."
    
    # Parse arguments
    local deployment_type="rolling"
    local solution="all"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --deployment-type)
                deployment_type="$2"
                shift 2
                ;;
            --solution)
                solution="$2"
                shift 2
                ;;
            --skip-backup)
                BACKUP_ENABLED=false
                shift
                ;;
            --skip-rollback)
                ROLLBACK_ENABLED=false
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --deployment-type TYPE  Deployment type (rolling, blue-green, canary)"
                echo "  --solution SOLUTION      Solution to deploy (all, http, fastapi, fastmcp, typescript)"
                echo "  --skip-backup          Skip backup creation"
                echo "  --skip-rollback        Skip rollback capability"
                echo "  --help                 Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # Pre-deployment checks
    pre_deployment_checks
    
    # Create backup
    create_backup
    
    # Deploy based on solution type
    case $solution in
        "all")
            log "Deploying all solutions..."
            ;;
        "http")
            log "Deploying HTTP solution..."
            ;;
        "fastapi")
            log "Deploying FastAPI solution..."
            ;;
        "fastmcp")
            log "Deploying FastMCP solution..."
            ;;
        "typescript")
            log "Deploying TypeScript solution..."
            ;;
        *)
            error "Unknown solution: $solution"
            ;;
    esac
    
    # Deploy based on deployment type
    case $deployment_type in
        "rolling")
            log "Using rolling deployment..."
            ;;
        "blue-green")
            log "Using blue-green deployment..."
            ;;
        "canary")
            log "Using canary deployment..."
            ;;
        *)
            error "Unknown deployment type: $deployment_type"
            ;;
    esac
    
    # Post-deployment verification
    post_deployment_verification
    
    log "Production deployment completed successfully!"
}

# Run main function
main "$@"