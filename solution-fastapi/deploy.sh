#!/bin/bash
# Production deployment script for FastAPI MCP server with async optimizations

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="fastapi-mcp"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Determine Docker Compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    log "Prerequisites check passed"
}

# Validate environment configuration
validate_environment() {
    log "Validating environment configuration..."
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file $ENV_FILE not found"
        exit 1
    fi
    
    # Check required environment variables
    local required_vars=(
        "OPENPROJECT_URL"
        "OPENPROJECT_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            error "Required environment variable $var not found in $ENV_FILE"
            exit 1
        fi
    done
    
    log "Environment validation passed"
}

# Create backup of current deployment
create_backup() {
    log "Creating backup of current deployment..."
    
    mkdir -p "$BACKUP_DIR"
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Backup configuration files
    cp -r .env* "$backup_path/" 2>/dev/null || true
    cp -r nginx/ "$backup_path/" 2>/dev/null || true
    cp -r monitoring/ "$backup_path/" 2>/dev/null || true
    
    # Backup Redis data if running
    if $COMPOSE_CMD ps redis | grep -q "Up"; then
        info "Creating Redis backup..."
        $COMPOSE_CMD exec -T redis redis-cli BGSAVE
        sleep 2
        docker cp "${PROJECT_NAME}_redis_1:/data/dump.rdb" "$backup_path/redis_dump.rdb" 2>/dev/null || true
    fi
    
    log "Backup created at $backup_path"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    # Set build arguments
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export APP_VERSION=${APP_VERSION:-$(git describe --tags --always 2>/dev/null || echo "1.0.0")}
    
    # Build with no cache for production
    $COMPOSE_CMD build --no-cache --parallel
    
    log "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Deploy based on environment
    local environment=${ENVIRONMENT:-production}
    
    case $environment in
        "production")
            info "Deploying production configuration..."
            $COMPOSE_CMD --profile production up -d --remove-orphans
            ;;
        "development")
            info "Deploying development configuration..."
            $COMPOSE_CMD --profile development up -d --remove-orphans
            ;;
        *)
            info "Deploying default configuration..."
            $COMPOSE_CMD up -d --remove-orphans
            ;;
    esac
    
    log "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if $COMPOSE_CMD ps | grep -E "(healthy|running)" | grep -q fastapi-mcp; then
            log "FastAPI MCP server is healthy"
            break
        fi
        
        info "Waiting for services... (attempt $((attempt + 1))/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "Services failed to become healthy within timeout"
        return 1
    fi
    
    # Test the health endpoint
    local health_url="http://localhost:${PORT:-8020}/health"
    if curl -sf "$health_url" > /dev/null; then
        log "Health check passed"
    else
        warn "Health check endpoint not responding"
    fi
}

# Run post-deployment tests
run_tests() {
    log "Running post-deployment tests..."
    
    # Basic connectivity test
    local base_url="http://localhost:${PORT:-8020}"
    
    # Test root endpoint
    if curl -sf "$base_url/" > /dev/null; then
        info "Root endpoint test passed"
    else
        error "Root endpoint test failed"
        return 1
    fi
    
    # Test health endpoint
    if curl -sf "$base_url/health" > /dev/null; then
        info "Health endpoint test passed"
    else
        error "Health endpoint test failed"
        return 1
    fi
    
    # Test metrics endpoint (if enabled)
    if curl -sf "$base_url/metrics" > /dev/null; then
        info "Metrics endpoint test passed"
    else
        warn "Metrics endpoint not accessible (may be restricted)"
    fi
    
    log "Post-deployment tests completed"
}

# Show deployment status
show_status() {
    log "Deployment Status:"
    echo ""
    
    # Show running services
    info "Running services:"
    $COMPOSE_CMD ps
    echo ""
    
    # Show service logs (last 10 lines)
    info "Recent logs:"
    $COMPOSE_CMD logs --tail=10 fastapi-mcp
    echo ""
    
    # Show access information
    local port=${PORT:-8020}
    info "Service endpoints:"
    echo "  - Application: http://localhost:$port/"
    echo "  - Health check: http://localhost:$port/health"
    echo "  - API docs: http://localhost:$port/docs"
    echo "  - Metrics: http://localhost:$port/metrics"
    echo "  - WebSocket: ws://localhost:$port/ws/{client_id}"
    echo ""
    
    # Show monitoring endpoints if available
    if $COMPOSE_CMD ps prometheus | grep -q "Up"; then
        echo "  - Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}/"
    fi
    
    if $COMPOSE_CMD ps grafana | grep -q "Up"; then
        echo "  - Grafana: http://localhost:${GRAFANA_PORT:-3000}/"
    fi
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old images and containers..."
    
    # Remove old containers
    docker container prune -f
    
    # Remove old images
    docker image prune -f
    
    # Remove unused volumes (careful!)
    # docker volume prune -f
    
    log "Cleanup completed"
}

# Main deployment function
main() {
    log "Starting FastAPI MCP server deployment..."
    
    cd "$SCRIPT_DIR"
    
    # Parse command line arguments
    local action=${1:-deploy}
    
    case $action in
        "deploy")
            check_prerequisites
            validate_environment
            create_backup
            build_images
            deploy_services
            wait_for_services
            run_tests
            show_status
            log "Deployment completed successfully!"
            ;;
        "update")
            log "Updating existing deployment..."
            check_prerequisites
            validate_environment
            build_images
            $COMPOSE_CMD up -d --no-deps fastapi-mcp
            wait_for_services
            run_tests
            log "Update completed successfully!"
            ;;
        "stop")
            log "Stopping services..."
            $COMPOSE_CMD down
            log "Services stopped"
            ;;
        "restart")
            log "Restarting services..."
            $COMPOSE_CMD restart
            wait_for_services
            log "Services restarted"
            ;;
        "logs")
            $COMPOSE_CMD logs -f "${2:-fastapi-mcp}"
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            create_backup
            ;;
        *)
            echo "Usage: $0 {deploy|update|stop|restart|logs|status|cleanup|backup}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Full deployment with backup and testing"
            echo "  update  - Update FastAPI MCP service only"
            echo "  stop    - Stop all services"
            echo "  restart - Restart all services"
            echo "  logs    - Show service logs (optionally specify service name)"
            echo "  status  - Show deployment status"
            echo "  cleanup - Clean up old containers and images"
            echo "  backup  - Create backup of current deployment"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"