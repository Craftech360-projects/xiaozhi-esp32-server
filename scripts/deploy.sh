#!/bin/bash

# Xiaozhi ESP32 Server Deployment Script
# This script handles deployment of all services using PM2

set -eo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEFAULT_ENV="staging"
DEFAULT_DEPLOY_PATH="/opt/xiaozhi-esp32-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --env ENV            Environment (dev|staging|production) [default: staging]"
    echo "  -p, --path PATH          Deployment path [default: $DEFAULT_DEPLOY_PATH]"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e production"
    echo "  $0 --env staging --path /opt/custom/path"
}

# Parse command line arguments
ENV="$DEFAULT_ENV"
DEPLOY_PATH="$DEFAULT_DEPLOY_PATH"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENV="$2"
            shift 2
            ;;
        -p|--path)
            DEPLOY_PATH="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENV" =~ ^(dev|staging|production)$ ]]; then
    print_error "Invalid environment: $ENV"
    print_info "Valid environments: dev, staging, production"
    exit 1
fi

print_info "Starting deployment for environment: $ENV"
print_info "Deploy path: $DEPLOY_PATH"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    print_error "PM2 is not installed. Please install PM2 globally:"
    print_info "npm install -g pm2"
    exit 1
fi

# Check if serve is installed (for manager-web)
if ! command -v serve &> /dev/null; then
    print_warning "serve is not installed. Installing serve globally..."
    npm install -g serve
fi

# Check if Java is installed (for manager-api)
if ! command -v java &> /dev/null; then
    print_error "Java is not installed. Please install Java 17 or higher."
    exit 1
fi

# Function to backup current deployment
backup_deployment() {
    if [ -d "$DEPLOY_PATH" ]; then
        local backup_dir="${DEPLOY_PATH}_backup_$(date +%Y%m%d_%H%M%S)"
        print_info "Creating backup: $backup_dir"
        cp -r "$DEPLOY_PATH" "$backup_dir"
    fi
}

# Function to create directory structure
create_directories() {
    print_info "Creating directory structure..."

    mkdir -p "$DEPLOY_PATH/main/manager-api/target"
    mkdir -p "$DEPLOY_PATH/main/manager-web"
    mkdir -p "$DEPLOY_PATH/main/mqtt-gateway"
    mkdir -p "/var/log/pm2"

    # Set permissions
    if [ "$USER" != "root" ]; then
        sudo chown -R $USER:$USER "$DEPLOY_PATH" 2>/dev/null || true
        sudo chown -R $USER:$USER "/var/log/pm2" 2>/dev/null || true
    fi
}

# Function to deploy manager-api (Java)
deploy_manager_api() {
    print_info "Deploying Manager API..."

    local jar_file="$PROJECT_ROOT/main/manager-api/target/xiaozhi-esp32-api.jar"

    if [ ! -f "$jar_file" ]; then
        print_warning "JAR file not found. Building Manager API..."
        cd "$PROJECT_ROOT/main/manager-api"
        mvn clean package -DskipTests
    fi

    if [ ! -f "$jar_file" ]; then
        print_error "Failed to build Manager API JAR"
        return 1
    fi

    cp "$jar_file" "$DEPLOY_PATH/main/manager-api/target/"
    print_success "Manager API deployed successfully"
}

# Function to deploy manager-web (Vue.js)
deploy_manager_web() {
    print_info "Deploying Manager Web..."

    local build_dir="$PROJECT_ROOT/main/manager-web/dist"

    if [ ! -d "$build_dir" ]; then
        print_warning "Build directory not found. Building Manager Web..."
        cd "$PROJECT_ROOT/main/manager-web"
        npm ci --legacy-peer-deps
        npm run build
    fi

    if [ ! -d "$build_dir" ]; then
        print_error "Failed to build Manager Web"
        return 1
    fi

    # Copy build files
    rm -rf "$DEPLOY_PATH/main/manager-web/dist"
    cp -r "$build_dir" "$DEPLOY_PATH/main/manager-web/"
    print_success "Manager Web deployed successfully"
}

# Function to deploy mqtt-gateway (Node.js)
deploy_mqtt_gateway() {
    print_info "Deploying MQTT Gateway..."

    # Copy source files
    cp -r "$PROJECT_ROOT/main/mqtt-gateway"/* "$DEPLOY_PATH/main/mqtt-gateway/"

    # Install dependencies
    cd "$DEPLOY_PATH/main/mqtt-gateway"
    npm ci --omit=dev --no-audit --no-fund

    print_success "MQTT Gateway deployed successfully"
}

# Function to start services with PM2
start_services() {
    print_info "Starting services with PM2..."

    # Copy ecosystem configuration
    cp "$PROJECT_ROOT/ecosystem.config.js" "$DEPLOY_PATH/"

    cd "$DEPLOY_PATH"

    # Stop existing processes
    pm2 delete ecosystem.config.js 2>/dev/null || print_info "No existing processes to delete"

    # Start all services with environment-specific config
    case $ENV in
        dev)
            pm2 start ecosystem.config.js
            ;;
        staging)
            pm2 start ecosystem.config.js --env staging
            ;;
        production)
            pm2 start ecosystem.config.js --env production
            ;;
    esac

    # Save PM2 configuration
    pm2 save

    # Show status
    pm2 list

    print_success "All services started successfully"
}

# Function to verify deployment
verify_deployment() {
    print_info "Verifying deployment..."

    # Check if all processes are running
    local failed_services=()

    if ! pm2 describe manager-api | grep -q "online"; then
        failed_services+=("manager-api")
    fi

    if ! pm2 describe manager-web | grep -q "online"; then
        failed_services+=("manager-web")
    fi

    if ! pm2 describe mqtt-gateway | grep -q "online"; then
        failed_services+=("mqtt-gateway")
    fi

    if [ ${#failed_services[@]} -eq 0 ]; then
        print_success "All services are running successfully"
        print_info "You can check service logs with: pm2 logs"
        return 0
    else
        print_error "The following services failed to start: ${failed_services[*]}"
        print_info "Check logs with: pm2 logs"
        return 1
    fi
}

# Main deployment flow
main() {
    print_info "Starting deployment process..."

    # Create backup
    backup_deployment

    # Create directory structure
    create_directories

    # Deploy each service
    deploy_manager_api || exit 1
    deploy_manager_web || exit 1
    deploy_mqtt_gateway || exit 1

    # Start services
    start_services || exit 1

    # Verify deployment
    verify_deployment || exit 1

    print_success "Deployment completed successfully!"
    print_info "Environment: $ENV"
    print_info "Deployment path: $DEPLOY_PATH"
}

# Run main function
main "$@"