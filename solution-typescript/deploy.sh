#!/bin/bash

# Deployment script for TypeScript MCP Solution
# Usage: ./deploy.sh [dev|prod]

set -e

# Configuration
ENVIRONMENT=${1:-dev}
PROJECT_NAME="mcp-typescript"
REGISTRY=${REGISTRY:-docker.io}
IMAGE_TAG=${IMAGE_TAG:-latest}

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
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if required commands exist
check_prerequisites() {
    log "Checking prerequisites..."
    
    command -v docker >/dev/null 2>&1 || { error "Docker is required but not installed."; exit 1; }
    command -v docker-compose >/dev/null 2>&1 || { error "Docker Compose is required but not installed."; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { warn "kubectl is not installed. Kubernetes deployment will be skipped."; }
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        warn ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            info "Created .env file from .env.example. Please update it with your configuration."
        else
            error "Neither .env nor .env.example found. Please create environment configuration."
            exit 1
        fi
    fi
    
    log "Prerequisites check completed."
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    # Build image
    docker build -t ${REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG} .
    
    # Tag as latest if not already
    if [ "$IMAGE_TAG" != "latest" ]; then
        docker tag ${REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG} ${REGISTRY}/${PROJECT_NAME}:latest
    fi
    
    log "Docker image built successfully: ${REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}"
}

# Run tests
run_tests() {
    log "Running tests..."
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    
    # Run tests
    npm test
    
    log "Tests completed successfully."
}

# Deploy with Docker Compose
deploy_compose() {
    log "Deploying with Docker Compose..."
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Build and start services
    if [ "$ENVIRONMENT" = "prod" ]; then
        docker-compose -f docker-compose.yml --profile production up -d
    else
        docker-compose up -d
    fi
    
    # Wait for health check
    log "Waiting for service to be healthy..."
    sleep 10
    
    # Check service health
    if curl -f http://localhost:8040/health/live > /dev/null 2>&1; then
        log "Service is healthy and running."
    else
        error "Service health check failed."
        docker-compose logs
        exit 1
    fi
    
    log "Docker Compose deployment completed successfully."
}

# Deploy to Kubernetes
deploy_kubernetes() {
    if ! command -v kubectl >/dev/null 2>&1; then
        warn "kubectl not found. Skipping Kubernetes deployment."
        return
    fi
    
    log "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace mcp-openproject --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s/typescript-solution.yaml
    
    # Wait for deployment to be ready
    log "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/typescript-solution -n mcp-openproject
    
    # Check deployment status
    kubectl get pods -n mcp-openproject -l app=typescript-solution
    
    log "Kubernetes deployment completed successfully."
}

# Push to registry
push_to_registry() {
    if [ -z "$REGISTRY" ] || [ "$REGISTRY" = "docker.io" ]; then
        warn "Skipping registry push (local development)."
        return
    fi
    
    log "Pushing image to registry..."
    
    docker push ${REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}
    docker push ${REGISTRY}/${PROJECT_NAME}:latest
    
    log "Image pushed to registry successfully."
}

# Cleanup
cleanup() {
    log "Cleaning up..."
    
    # Remove unused Docker objects
    docker system prune -f
    
    # Remove old images (keep last 3)
    docker images ${REGISTRY}/${PROJECT_NAME} --format "{{.Tag}}" | tail -n +4 | xargs -r docker rmi
    
    log "Cleanup completed."
}

# Main deployment function
main() {
    log "Starting TypeScript MCP Solution deployment..."
    log "Environment: $ENVIRONMENT"
    log "Image: ${REGISTRY}/${PROJECT_NAME}:${IMAGE_TAG}"
    
    # Execute deployment steps
    check_prerequisites
    run_tests
    build_image
    
    if [ "$ENVIRONMENT" = "prod" ]; then
        push_to_registry
        deploy_kubernetes
    else
        deploy_compose
    fi
    
    cleanup
    
    log "Deployment completed successfully!"
    
    # Show service information
    if [ "$ENVIRONMENT" = "dev" ]; then
        echo ""
        info "Service URLs:"
        echo "  - MCP Endpoint: http://localhost:8040/mcp"
        echo "  - Health Check: http://localhost:8040/health"
        echo "  - Metrics: http://localhost:8040/metrics"
        echo "  - Grafana: http://localhost:3000 (if monitoring enabled)"
        echo "  - Prometheus: http://localhost:9090 (if monitoring enabled)"
    fi
}

# Handle script arguments
case "$1" in
    "dev")
        ENVIRONMENT="dev"
        ;;
    "prod")
        ENVIRONMENT="prod"
        ;;
    "test")
        run_tests
        exit 0
        ;;
    "build")
        build_image
        exit 0
        ;;
    "help"|"--help"|"-h")
        echo "Usage: $0 [dev|prod|test|build|help]"
        echo "  dev     - Deploy for development (default)"
        echo "  prod    - Deploy for production"
        echo "  test    - Run tests only"
        echo "  build   - Build Docker image only"
        echo "  help    - Show this help message"
        exit 0
        ;;
    "")
        ;;
    *)
        error "Unknown argument: $1"
        echo "Use '$0 help' for usage information."
        exit 1
        ;;
esac

# Run main function
main "$@"