#!/bin/bash

# LinkedIn Recommendation Writer - One Command Setup Script
# This script sets up the entire development environment with a single command

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="LinkedIn Recommendation Writer"
DOCKER_COMPOSE_FILE="docker-compose.yml"
DOCKER_COMPOSE_PROD_FILE="docker-compose.prod.yml"
ENV_TEMPLATE="env.template"
ENV_FILE=".env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║              LinkedIn Recommendation Writer                   ║"
    echo "║                                                              ║"
    echo "║                  🚀 One Command Setup                        ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
}

check_requirements() {
    log_info "Checking system requirements..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        log_info "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        log_info "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi

    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "No .env file found. Creating from template..."
        if [ -f "$ENV_TEMPLATE" ]; then
            cp "$ENV_TEMPLATE" "$ENV_FILE"
            log_info "Created .env file from template. Please edit it with your configuration."
            log_warning "Required: GITHUB_TOKEN, GEMINI_API_KEY"
            echo ""
            read -p "Press Enter to continue after editing .env file..."
        else
            log_error "No .env template found. Please create a .env file manually."
            exit 1
        fi
    fi

    log_success "System requirements check passed!"
}

setup_environment() {
    local mode="$1"

    case $mode in
        "dev"|"development")
            log_info "Setting up development environment..."
            export COMPOSE_FILE="$DOCKER_COMPOSE_FILE"
            export NODE_ENV=development
            ;;
        "prod"|"production")
            log_info "Setting up production environment..."
            export COMPOSE_FILE="$DOCKER_COMPOSE_PROD_FILE"
            export NODE_ENV=production
            ;;

        *)
            log_error "Invalid mode: $mode"
            show_usage
            exit 1
            ;;
    esac
}

build_services() {
    log_info "Building Docker images..."
    if command -v docker-compose &> /dev/null; then
        docker-compose build --parallel
    else
        docker compose build --parallel
    fi
    log_success "Docker images built successfully!"
}

start_services() {
    log_info "Starting services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi
    log_success "Services started successfully!"
}

run_tests() {
    log_info "Running frontend tests..."
    if command -v docker-compose &> /dev/null; then
        docker-compose exec frontend npm run test
    else
        docker compose exec frontend npm run test
    fi
    log_success "Tests completed!"
}

show_status() {
    log_info "Service Status:"
    echo ""
    if command -v docker-compose &> /dev/null; then
        docker-compose ps
    else
        docker compose ps
    fi
    echo ""
}

show_urls() {
    local mode="$1"

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                          🌐 URLs                             ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    case $mode in
        "dev"|"development")
            echo "Development URLs:"
            echo "  Frontend (Vite):    http://localhost:5173"
            echo "  Backend (FastAPI):  http://localhost:8000"
            echo "  API Docs:          http://localhost:8000/docs"
            echo "  Database:          localhost:5432"
            echo "  Redis:             localhost:6379"
            ;;
        "prod"|"production")
            echo "Production URLs:"
            echo "  Application:       http://localhost"
            echo "  API:              http://localhost/api"
            echo ""
            echo "Note: Services run internally, accessed through Nginx"
            ;;

    esac
    echo ""
}

show_logs() {
    log_info "Showing service logs (Ctrl+C to stop)..."
    echo ""
    if command -v docker-compose &> /dev/null; then
        docker-compose logs -f
    else
        docker compose logs -f
    fi
}

stop_services() {
    log_info "Stopping services..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down
    else
        docker compose down
    fi
    log_success "Services stopped!"
}

cleanup() {
    log_warning "Cleaning up Docker resources..."
    if command -v docker-compose &> /dev/null; then
        docker-compose down -v --rmi all
        docker-compose -f "$DOCKER_COMPOSE_PROD_FILE" down -v --rmi all
    else
        docker compose down -v --rmi all
        docker compose -f "$DOCKER_COMPOSE_PROD_FILE" down -v --rmi all
    fi
    log_success "Cleanup completed!"
}

show_usage() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                     📖 Usage Guide                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Usage: $0 [MODE] [COMMAND]"
    echo ""
    echo "MODES:"
    echo "  dev     Development environment (default)"
    echo "  prod    Production environment"

    echo ""
    echo "COMMANDS:"
    echo "  setup   Full setup (build + start) - DEFAULT"
    echo "  build   Build Docker images only"
    echo "  start   Start services only"
    echo "  stop    Stop services"
    echo "  logs    Show service logs"
    echo "  status  Show service status"
    echo "  test    Run tests"
    echo "  clean   Clean up Docker resources"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                      # Setup development environment"
    echo "  $0 dev                  # Setup development environment"
    echo "  $0 prod                 # Setup production environment"

    echo "  $0 dev logs            # Show development logs"
    echo "  $0 prod stop           # Stop production services"
    echo "  $0 clean               # Clean up everything"
    echo ""
}

main() {
    local mode="${1:-dev}"
    local command="${2:-setup}"

    show_banner

    case $command in
        "setup")
            check_requirements
            setup_environment "$mode"
            build_services
            start_services
            show_status
            show_urls "$mode"
            log_success "Setup complete! Run '$0 $mode logs' to see logs."
            ;;
        "build")
            check_requirements
            setup_environment "$mode"
            build_services
            ;;
        "start")
            check_requirements
            setup_environment "$mode"
            start_services
            show_status
            show_urls "$mode"
            ;;
        "stop")
            setup_environment "$mode"
            stop_services
            ;;
        "logs")
            setup_environment "$mode"
            show_logs
            ;;
        "status")
            setup_environment "$mode"
            show_status
            ;;
        "test")
            check_requirements
            setup_environment "dev"
            run_tests
            ;;
        "clean")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
