#!/bin/bash

# FastMCP Solution Deployment Script
# This script helps deploy the FastMCP solution in different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="fastmcp-solution"
IMAGE_NAME="mcp-fastmcp"
VERSION=${VERSION:-latest}
ENVIRONMENT=${ENVIRONMENT:-development}
NAMESPACE=${NAMESPACE:-mcp-openproject}

# Help function
show_help() {
    echo -e "${BLUE}FastMCP Solution Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  docker-build     Build Docker image"
    echo "  docker-push      Push Docker image to registry"
    echo "  docker-run       Run Docker container locally"
    echo "  compose-up       Start services with Docker Compose"
    echo "  compose-down     Stop services with Docker Compose"
    echo "  k8s-deploy       Deploy to Kubernetes"
    echo "  k8s-delete       Delete from Kubernetes"
    echo "  monitoring       Start monitoring stack"
    echo "  all-deploy       Complete deployment pipeline"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV      Environment (development, production, testing)"
    echo "  -v, --version VER  Version tag for Docker image"
    echo "  -n, --namespace NS Kubernetes namespace"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker-build -e production"
    echo "  $0 compose-up -e development"
    echo "  $0 k8s-deploy -e production -v 1.0.0"
}

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check required tools
check_requirements() {
    local missing_tools=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_tools+=("docker-compose")
    fi
    
    # Check kubectl for Kubernetes operations
    if [[ "$1" == "k8s"* ]]; then
        if ! command -v kubectl &> /dev/null; then
            missing_tools+=("kubectl")
        fi
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi
}

# Build Docker image
docker_build() {
    log_info "Building Docker image..."
    
    local build_args=(
        "--build-arg" "APP_VERSION=${VERSION}"
        "--build-arg" "BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        "--build-arg" "VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    )
    
    docker build "${build_args[@]}" -t "${IMAGE_NAME}:${VERSION}" -t "${IMAGE_NAME}:latest" .
    
    log_info "Docker image built successfully: ${IMAGE_NAME}:${VERSION}"
}

# Push Docker image
docker_push() {
    log_info "Pushing Docker image..."
    
    if [[ "$VERSION" != "latest" ]]; then
        docker push "${IMAGE_NAME}:${VERSION}"
    fi
    docker push "${IMAGE_NAME}:latest"
    
    log_info "Docker image pushed successfully"
}

# Run Docker container locally
docker_run() {
    log_info "Running Docker container locally..."
    
    docker run -d \
        --name "${PROJECT_NAME}-local" \
        -p "${FASTMCP_PORT:-8030}:8030" \
        -p "${FASTMCP_SSE_PORT:-8031}:8031" \
        -e "ENVIRONMENT=${ENVIRONMENT}" \
        -e "LOG_LEVEL=${LOG_LEVEL:-INFO}" \
        -e "OPENPROJECT_URL=${OPENPROJECT_URL}" \
        -e "OPENPROJECT_API_KEY=${OPENPROJECT_API_KEY}" \
        --restart unless-stopped \
        "${IMAGE_NAME}:${VERSION}"
    
    log_info "Container started successfully"
    log_info "Access logs: docker logs -f ${PROJECT_NAME}-local"
}

# Start services with Docker Compose
compose_up() {
    log_info "Starting services with Docker Compose..."
    
    local compose_args=(
        "--env-file" ".env"
        "-p" "${PROJECT_NAME}"
        "--profile" "${ENVIRONMENT}"
    )
    
    # Add monitoring profile if enabled
    if [[ "$MONITORING" == "true" ]]; then
        compose_args+=("--profile" "monitoring")
    fi
    
    docker compose "${compose_args[@]}" up -d
    
    log_info "Services started successfully"
    log_info "View status: docker compose -p ${PROJECT_NAME} ps"
    log_info "View logs: docker compose -p ${PROJECT_NAME} logs -f"
}

# Stop services with Docker Compose
compose_down() {
    log_info "Stopping services with Docker Compose..."
    
    docker compose -p "${PROJECT_NAME}" down
    
    log_info "Services stopped successfully"
}

# Deploy to Kubernetes
k8s_deploy() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/ -n "${NAMESPACE}"
    
    # Wait for deployment to be ready
    kubectl rollout status deployment/fastmcp-solution -n "${NAMESPACE}" --timeout=300s
    
    log_info "Deployment completed successfully"
    log_info "View status: kubectl get pods -n ${NAMESPACE}"
    log_info "View logs: kubectl logs -f deployment/fastmcp-solution -n ${NAMESPACE}"
}

# Delete from Kubernetes
k8s_delete() {
    log_info "Deleting from Kubernetes..."
    
    kubectl delete -f k8s/ -n "${NAMESPACE}" --ignore-not-found=true
    
    log_info "Resources deleted successfully"
}

# Start monitoring stack
start_monitoring() {
    log_info "Starting monitoring stack..."
    
    docker compose -p "${PROJECT_NAME}" --profile monitoring up -d
    
    log_info "Monitoring stack started"
    log_info "Grafana: http://localhost:${GRAFANA_PORT:-3001}"
    log_info "Prometheus: http://localhost:${PROMETHEUS_PORT:-9091}"
}

# Complete deployment pipeline
all_deploy() {
    log_info "Starting complete deployment pipeline..."
    
    check_requirements
    docker_build
    
    if [[ "$PUSH_IMAGE" == "true" ]]; then
        docker_push
    fi
    
    if [[ "$DEPLOY_TARGET" == "kubernetes" ]]; then
        k8s_deploy
    else
        compose_up
    fi
    
    if [[ "$START_MONITORING" == "true" ]]; then
        start_monitoring
    fi
    
    log_info "Complete deployment pipeline finished successfully"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                COMMAND="$1"
                shift
                ;;
        esac
    done
}

# Main function
main() {
    # Parse arguments
    parse_args "$@"
    
    # Set default environment variables
    export ENVIRONMENT=${ENVIRONMENT:-development}
    export VERSION=${VERSION:-latest}
    export NAMESPACE=${NAMESPACE:-mcp-openproject}
    
    # Execute command
    case "${COMMAND:-help}" in
        docker-build)
            check_requirements
            docker_build
            ;;
        docker-push)
            check_requirements
            docker_push
            ;;
        docker-run)
            check_requirements
            docker_run
            ;;
        compose-up)
            check_requirements
            compose_up
            ;;
        compose-down)
            check_requirements
            compose_down
            ;;
        k8s-deploy)
            check_requirements k8s
            k8s_deploy
            ;;
        k8s-delete)
            check_requirements k8s
            k8s_delete
            ;;
        monitoring)
            check_requirements
            start_monitoring
            ;;
        all-deploy)
            check_requirements
            all_deploy
            ;;
        help)
            show_help
            ;;
        *)
            log_error "Unknown command: ${COMMAND:-none}"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"