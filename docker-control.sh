#!/bin/bash

# Docker Control Script for Ztrade
# Manages Docker Compose services for development and production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment (default: development)
ENV="${1:-dev}"
COMPOSE_FILE="docker-compose.${ENV}.yml"

# Check if compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}Error: $COMPOSE_FILE not found${NC}"
    echo "Usage: $0 [dev|prod] [command]"
    exit 1
fi

# Function to print colored messages
info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

success() {
    echo -e "${GREEN}✅${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

error() {
    echo -e "${RED}❌${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Docker Control Script for Ztrade

Usage:
    $0 [dev|prod] [command]

Commands:
    build       Build all images
    up          Start all services
    down        Stop all services
    restart     Restart all services
    ps          Show running services
    logs        Show logs for all services
    shell       Open shell in trading container
    clean       Remove all containers and volumes
    help        Show this help message

Examples:
    $0 dev up            # Start development environment
    $0 prod build        # Build production images
    $0 dev logs worker   # Show worker logs in dev
    $0 prod down         # Stop production services

EOF
}

# Parse command
COMMAND="${2:-help}"

case "$COMMAND" in
    build)
        info "Building Docker images for $ENV environment..."
        docker-compose -f "$COMPOSE_FILE" build
        success "Build complete!"
        ;;

    up)
        info "Starting services for $ENV environment..."
        docker-compose -f "$COMPOSE_FILE" up -d
        success "Services started!"
        echo ""
        info "Access points:"
        echo "  Dashboard: http://localhost:8501"
        echo "  Flower:    http://localhost:5555"
        echo ""
        info "View logs: $0 $ENV logs"
        ;;

    down)
        info "Stopping services for $ENV environment..."
        docker-compose -f "$COMPOSE_FILE" down
        success "Services stopped!"
        ;;

    restart)
        info "Restarting services for $ENV environment..."
        docker-compose -f "$COMPOSE_FILE" restart
        success "Services restarted!"
        ;;

    ps)
        info "Running services for $ENV environment:"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;

    logs)
        SERVICE="${3:-}"
        if [ -z "$SERVICE" ]; then
            info "Showing logs for all services (Ctrl+C to exit)..."
            docker-compose -f "$COMPOSE_FILE" logs -f
        else
            info "Showing logs for $SERVICE (Ctrl+C to exit)..."
            docker-compose -f "$COMPOSE_FILE" logs -f "$SERVICE"
        fi
        ;;

    shell)
        CONTAINER="${3:-trading}"
        info "Opening shell in $CONTAINER container..."
        docker-compose -f "$COMPOSE_FILE" exec "$CONTAINER" /bin/bash
        ;;

    clean)
        warning "This will remove all containers, volumes, and networks for $ENV"
        read -p "Are you sure? (yes/no) " -r
        echo
        if [[ $REPLY =~ ^[Yy]es$ ]]; then
            info "Cleaning up $ENV environment..."
            docker-compose -f "$COMPOSE_FILE" down -v
            success "Cleanup complete!"
        else
            info "Cleanup cancelled"
        fi
        ;;

    help|--help|-h)
        usage
        ;;

    *)
        error "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac
