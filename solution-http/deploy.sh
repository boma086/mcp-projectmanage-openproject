#!/bin/bash
# Deployment script for HTTP MCP Solution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="backup"
LOG_FILE="deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "docker-compose.yml not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f ".env.example" ]; then
            warning ".env file not found, copying from .env.example"
            cp .env.example .env
            warning "Please edit .env file with your configuration"
        else
            error ".env file not found and no .env.example available"
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p logs data templates backup
    
    success "Environment setup completed"
}

# Build images
build_images() {
    log "Building Docker images..."
    
    docker-compose build --no-cache
    
    success "Docker images built successfully"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Start services in correct order
    docker-compose up -d postgres memcached
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    sleep 30
    
    # Start remaining services
    docker-compose up -d
    
    success "Services deployed successfully"
}

# Health check
health_check() {
    log "Performing health checks..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8010/health &> /dev/null; then
            success "Health check passed"
            return 0
        fi
        
        log "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 10
        ((attempt++))
    done
    
    error "Health check failed after $max_attempts attempts"
    return 1
}

# Show status
show_status() {
    log "Service status:"
    docker-compose ps
    
    echo ""
    log "Service URLs:"
    echo "  - HTTP MCP Server: http://localhost:8010"
    echo "  - API Documentation: http://localhost:8010/docs"
    echo "  - Health Check: http://localhost:8010/health"
    echo "  - OpenProject: http://localhost:8090"
    echo ""
    log "Log files:"
    echo "  - Deployment: $LOG_FILE"
    echo "  - Application: logs/error.log"
    echo "  - Access: logs/access.log"
}

# Backup
backup() {
    log "Creating backup..."
    
    local backup_file="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    mkdir -p "$BACKUP_DIR"
    
    tar -czf "$backup_file" \
        --exclude="$BACKUP_DIR" \
        --exclude=".git" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude="venv" \
        --exclude="node_modules" \
        .
    
    success "Backup created: $backup_file"
}

# Rollback
rollback() {
    log "Rolling back deployment..."
    
    docker-compose down
    
    # Find latest backup
    local latest_backup=$(find "$BACKUP_DIR" -name "backup-*.tar.gz" | sort -r | head -n 1)
    
    if [ -n "$latest_backup" ]; then
        log "Restoring from $latest_backup"
        tar -xzf "$latest_backup"
        deploy_services
    else
        error "No backup found for rollback"
        exit 1
    fi
}

# Stop services
stop() {
    log "Stopping services..."
    docker-compose down
    success "Services stopped"
}

# Clean up
cleanup() {
    log "Cleaning up..."
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    success "Cleanup completed"
}

# Main deployment function
deploy() {
    log "Starting deployment of HTTP MCP Solution..."
    
    check_prerequisites
    setup_environment
    backup
    build_images
    deploy_services
    
    if health_check; then
        show_status
        success "Deployment completed successfully!"
    else
        error "Deployment failed health check"
        exit 1
    fi
}

# Command line interface
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    build)
        check_prerequisites
        build_images
        ;;
    start)
        docker-compose up -d
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        deploy_services
        ;;
    status)
        show_status
        ;;
    logs)
        docker-compose logs -f ${2:-mcp-http}
        ;;
    health)
        health_check
        ;;
    backup)
        backup
        ;;
    rollback)
        rollback
        ;;
    cleanup)
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|build|start|stop|restart|status|logs|health|backup|rollback|cleanup}"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  build    - Build Docker images only"
        echo "  start    - Start services"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  status   - Show service status"
        echo "  logs     - Show logs (optionally specify service)"
        echo "  health   - Check service health"
        echo "  backup   - Create backup"
        echo "  rollback - Rollback to latest backup"
        echo "  cleanup  - Clean up containers and volumes"
        exit 1
        ;;
esac