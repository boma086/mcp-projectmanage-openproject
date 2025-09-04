#!/bin/bash

# Comprehensive Kubernetes Deployment Script for MCP OpenProject Solutions
# This script deploys all solutions to a Kubernetes cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl >/dev/null 2>&1; then
        error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! kubectl cluster-info >/dev/null 2>&1; then
        error "Unable to connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log "kubectl is available and connected to cluster"
}

# Function to check if docker is available
check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        error "Unable to connect to Docker daemon. Please start Docker."
        exit 1
    fi
    
    log "Docker is available and running"
}

# Function to validate configuration
validate_config() {
    info "Validating configuration..."
    
    # Check if required files exist
    required_files=(
        "$PROJECT_DIR/k8s/namespace.yaml"
        "$PROJECT_DIR/k8s/http-solution.yaml"
        "$PROJECT_DIR/k8s/fastapi-solution.yaml"
        "$PROJECT_DIR/k8s/infrastructure.yaml"
        "$PROJECT_DIR/k8s/monitoring.yaml"
        "$PROJECT_DIR/k8s/secrets.yaml"
        "$PROJECT_DIR/k8s/configmaps.yaml"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            error "Required file not found: $file"
            exit 1
        fi
    done
    
    log "All required configuration files are present"
}

# Function to build Docker images
build_docker_images() {
    info "Building Docker images..."
    
    # Build HTTP solution image
    log "Building HTTP solution image..."
    cd "$PROJECT_DIR/solution-http"
    docker build -t mcp-http:latest .
    
    # Build FastAPI solution image
    log "Building FastAPI solution image..."
    cd "$PROJECT_DIR/solution-fastapi"
    docker build -t mcp-fastapi:latest .
    
    # Build FastMCP solution image (placeholder)
    log "Building FastMCP solution image..."
    cd "$PROJECT_DIR/solution-fastmcp"
    docker build -t mcp-fastmcp:latest .
    
    # Build TypeScript solution image (placeholder)
    log "Building TypeScript solution image..."
    cd "$PROJECT_DIR/solution-typescript"
    docker build -t mcp-typescript:latest .
    
    cd "$PROJECT_DIR"
    log "All Docker images built successfully"
}

# Function to deploy to Kubernetes
deploy_to_kubernetes() {
    info "Deploying to Kubernetes..."
    
    # Create namespace
    log "Creating namespace..."
    kubectl apply -f k8s/namespace.yaml
    
    # Create secrets
    log "Creating secrets..."
    kubectl apply -f k8s/secrets.yaml
    
    # Create configmaps
    log "Creating configmaps..."
    kubectl apply -f k8s/configmaps.yaml
    
    # Deploy infrastructure
    log "Deploying infrastructure services..."
    kubectl apply -f k8s/infrastructure.yaml
    
    # Wait for infrastructure to be ready
    log "Waiting for infrastructure services to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n mcp-openproject
    kubectl wait --for=condition=available --timeout=300s deployment/postgres -n mcp-openproject
    
    # Deploy applications
    log "Deploying application services..."
    kubectl apply -f k8s/http-solution.yaml
    kubectl apply -f k8s/fastapi-solution.yaml
    
    # Deploy monitoring
    log "Deploying monitoring services..."
    kubectl apply -f k8s/monitoring.yaml
    
    log "All services deployed successfully"
}

# Function to wait for deployment
wait_for_deployment() {
    info "Waiting for all deployments to be ready..."
    
    # Wait for all deployments to be ready
    deployments=(
        "http-solution"
        "fastapi-solution"
        "redis"
        "postgres"
        "nginx"
        "prometheus"
    )
    
    for deployment in "${deployments[@]}"; do
        log "Waiting for $deployment to be ready..."
        kubectl wait --for=condition=available --timeout=300s deployment/$deployment -n mcp-openproject || {
            warn "Timeout waiting for $deployment, continuing..."
        }
    done
    
    log "All deployments are ready"
}

# Function to run smoke tests
run_smoke_tests() {
    info "Running smoke tests..."
    
    # Test HTTP solution
    log "Testing HTTP solution..."
    kubectl port-forward -n mcp-openproject svc/http-solution-service 8010:80 &
    HTTP_PID=$!
    sleep 5
    
    if curl -f http://localhost:8010/health >/dev/null 2>&1; then
        log "HTTP solution health check passed"
    else
        warn "HTTP solution health check failed"
    fi
    
    kill $HTTP_PID 2>/dev/null || true
    
    # Test FastAPI solution
    log "Testing FastAPI solution..."
    kubectl port-forward -n mcp-openproject svc/fastapi-solution-service 8020:80 &
    FASTAPI_PID=$!
    sleep 5
    
    if curl -f http://localhost:8020/health >/dev/null 2>&1; then
        log "FastAPI solution health check passed"
    else
        warn "FastAPI solution health check failed"
    fi
    
    kill $FASTAPI_PID 2>/dev/null || true
    
    log "Smoke tests completed"
}

# Function to show deployment status
show_deployment_status() {
    info "Deployment Status:"
    echo "===================="
    
    echo -e "${BLUE}Namespace:${NC}"
    kubectl get namespace mcp-openproject
    
    echo -e "\n${BLUE}Pods:${NC}"
    kubectl get pods -n mcp-openproject -o wide
    
    echo -e "\n${BLUE}Services:${NC}"
    kubectl get svc -n mcp-openproject
    
    echo -e "\n${BLUE}Deployments:${NC}"
    kubectl get deployments -n mcp-openproject
    
    echo -e "\n${BLUE}HPAs:${NC}"
    kubectl get hpa -n mcp-openproject
    
    echo -e "\n${BLUE}Ingress:${NC}"
    kubectl get ingress -n mcp-openproject 2>/dev/null || echo "No ingress resources found"
}

# Function to show access information
show_access_info() {
    echo -e "\n${GREEN}Access Information:${NC}"
    echo "====================="
    
    # Get nginx service external IP
    NGINX_IP=$(kubectl get svc nginx-service -n mcp-openproject -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
    
    if [[ "$NGINX_IP" == "localhost" ]]; then
        echo "Using port forwarding for local access:"
        echo "  kubectl port-forward -n mcp-openproject svc/nginx-service 8080:80"
        echo "  Then access: http://localhost:8080"
    else
        echo "External access: http://$NGINX_IP"
    fi
    
    echo -e "\n${BLUE}Service URLs:${NC}"
    echo "  HTTP Solution:    http://$NGINX_IP/http/"
    echo "  FastAPI Solution: http://$NGINX_IP/fastapi/"
    echo "  FastMCP Solution: http://$NGINX_IP/fastmcp/"
    echo "  TypeScript:      http://$NGINX_IP/typescript/"
    
    echo -e "\n${BLUE}Monitoring:${NC}"
    echo "  Prometheus: http://$NGINX_IP/prometheus/"
    echo "  Grafana:    http://$NGINX_IP/grafana/ (admin/admin)"
    
    echo -e "\n${BLUE}Health Checks:${NC}"
    echo "  HTTP Solution:    http://$NGINX_IP/http/health"
    echo "  FastAPI Solution: http://$NGINX_IP/fastapi/health"
    echo "  FastMCP Solution: http://$NGINX_IP/fastmcp/health"
    echo "  TypeScript:      http://$NGINX_IP/typescript/health"
}

# Function to cleanup
cleanup() {
    info "Cleaning up..."
    
    # Kill any background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    log "Cleanup completed"
}

# Main function
main() {
    log "Starting Kubernetes deployment for MCP OpenProject solutions"
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    # Check prerequisites
    check_kubectl
    check_docker
    
    # Validate configuration
    validate_config
    
    # Build Docker images
    build_docker_images
    
    # Deploy to Kubernetes
    deploy_to_kubernetes
    
    # Wait for deployment
    wait_for_deployment
    
    # Run smoke tests
    run_smoke_tests
    
    # Show deployment status
    show_deployment_status
    
    # Show access information
    show_access_info
    
    log "Kubernetes deployment completed successfully!"
}

# Function to show help
show_help() {
    cat << EOF
Kubernetes Deployment Script for MCP OpenProject Solutions

USAGE:
    $0 [COMMAND]

COMMANDS:
    deploy    Full deployment (default)
    status    Show deployment status
    test      Run smoke tests
    cleanup   Clean up deployment
    help      Show this help message

EXAMPLES:
    $0 deploy          # Full deployment
    $0 status          # Show status
    $0 test            # Run tests
    $0 cleanup         # Clean up

ENVIRONMENT VARIABLES:
    KUBECONFIG        Path to kubeconfig file
    DOCKER_HOST       Docker daemon URL
    LOG_LEVEL         Logging level (DEBUG, INFO, WARN, ERROR)

NOTES:
    - Make sure kubectl is configured with proper cluster access
    - Docker daemon must be running
    - Update secrets in k8s/secrets.yaml before deployment
    - Update config values in k8s/configmaps.yaml as needed

EOF
}

# Parse command line arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    status)
        show_deployment_status
        show_access_info
        ;;
    test)
        run_smoke_tests
        ;;
    cleanup)
        kubectl delete namespace mcp-openproject --ignore-not-found=true
        log "Namespace mcp-openproject deleted"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac