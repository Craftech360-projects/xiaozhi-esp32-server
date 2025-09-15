#!/bin/bash

# Xiaozhi ESP32 Server Build Script
# This script builds all components of the project

set -eo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
    echo "  -s, --service SERVICE    Build specific service (api|web|gateway|all) [default: all]"
    echo "  -t, --tests             Run tests during build"
    echo "  -c, --clean             Clean before building"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Services:"
    echo "  api                     Manager API (Java Spring Boot)"
    echo "  web                     Manager Web (Vue.js)"
    echo "  gateway                 MQTT Gateway (Node.js)"
    echo "  all                     All services"
    echo ""
    echo "Examples:"
    echo "  $0                      # Build all services"
    echo "  $0 -s api              # Build only Manager API"
    echo "  $0 -s web -c           # Clean and build Manager Web"
    echo "  $0 -t                  # Build all services with tests"
}

# Parse command line arguments
SERVICE="all"
RUN_TESTS=false
CLEAN_BUILD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -t|--tests)
            RUN_TESTS=true
            shift
            ;;
        -c|--clean)
            CLEAN_BUILD=true
            shift
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

# Validate service
if [[ ! "$SERVICE" =~ ^(api|web|gateway|all)$ ]]; then
    print_error "Invalid service: $SERVICE"
    print_info "Valid services: api, web, gateway, all"
    exit 1
fi

print_info "Build configuration:"
print_info "  Service: $SERVICE"
print_info "  Run tests: $RUN_TESTS"
print_info "  Clean build: $CLEAN_BUILD"
echo ""

# Function to check prerequisites
check_prerequisites() {
    local missing_tools=()

    # Check Node.js and npm
    if ! command -v node &> /dev/null; then
        missing_tools+=("Node.js")
    fi

    if ! command -v npm &> /dev/null; then
        missing_tools+=("npm")
    fi

    # Check Java and Maven for API build
    if [[ "$SERVICE" == "api" || "$SERVICE" == "all" ]]; then
        if ! command -v java &> /dev/null; then
            missing_tools+=("Java")
        fi

        if ! command -v mvn &> /dev/null; then
            missing_tools+=("Maven")
        fi
    fi

    if [ ${#missing_tools[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing_tools[*]}"
        exit 1
    fi

    print_success "All prerequisites are available"
}

# Function to build Manager API (Java Spring Boot)
build_manager_api() {
    print_info "Building Manager API..."

    cd "$PROJECT_ROOT/main/manager-api"

    # Clean if requested
    if [ "$CLEAN_BUILD" = true ]; then
        print_info "Cleaning Manager API..."
        mvn clean
    fi

    # Compile
    print_info "Compiling Manager API..."
    mvn compile

    # Run tests if requested
    if [ "$RUN_TESTS" = true ]; then
        print_info "Running Manager API tests..."
        mvn test
    fi

    # Package
    print_info "Packaging Manager API..."
    if [ "$RUN_TESTS" = true ]; then
        mvn package
    else
        mvn package -DskipTests
    fi

    # Verify JAR was created
    if [ ! -f "target/xiaozhi-esp32-api.jar" ]; then
        print_error "Failed to create JAR file"
        return 1
    fi

    print_success "Manager API built successfully"
    print_info "JAR location: $PROJECT_ROOT/main/manager-api/target/xiaozhi-esp32-api.jar"
}

# Function to build Manager Web (Vue.js)
build_manager_web() {
    print_info "Building Manager Web..."

    cd "$PROJECT_ROOT/main/manager-web"

    # Clean if requested
    if [ "$CLEAN_BUILD" = true ]; then
        print_info "Cleaning Manager Web..."
        rm -rf node_modules dist
    fi

    # Install dependencies
    print_info "Installing Manager Web dependencies..."
    npm ci --legacy-peer-deps

    # Run tests if requested
    if [ "$RUN_TESTS" = true ]; then
        print_info "Running Manager Web tests..."
        # npm test (uncomment if you have tests)
        print_warning "No tests configured for Manager Web"
    fi

    # Build for production
    print_info "Building Manager Web for production..."
    npm run build

    # Verify build output
    if [ ! -d "dist" ]; then
        print_error "Failed to create build output"
        return 1
    fi

    print_success "Manager Web built successfully"
    print_info "Build location: $PROJECT_ROOT/main/manager-web/dist"
}

# Function to build MQTT Gateway (Node.js)
build_mqtt_gateway() {
    print_info "Building MQTT Gateway..."

    cd "$PROJECT_ROOT/main/mqtt-gateway"

    # Clean if requested
    if [ "$CLEAN_BUILD" = true ]; then
        print_info "Cleaning MQTT Gateway..."
        rm -rf node_modules
    fi

    # Install dependencies
    print_info "Installing MQTT Gateway dependencies..."
    npm ci --omit=dev --no-audit --no-fund

    # Run tests if requested
    if [ "$RUN_TESTS" = true ]; then
        print_info "Running MQTT Gateway tests..."
        # npm test (uncomment if you have tests)
        print_warning "No tests configured for MQTT Gateway"
    fi

    # Verify main application file exists
    if [ ! -f "app.js" ]; then
        print_error "Main application file (app.js) not found"
        return 1
    fi

    print_success "MQTT Gateway built successfully"
    print_info "Application location: $PROJECT_ROOT/main/mqtt-gateway/app.js"
}

# Function to show build summary
show_build_summary() {
    echo ""
    print_info "Build Summary:"
    echo "=============="

    if [[ "$SERVICE" == "api" || "$SERVICE" == "all" ]]; then
        if [ -f "$PROJECT_ROOT/main/manager-api/target/xiaozhi-esp32-api.jar" ]; then
            print_success "✓ Manager API - Built successfully"
            local jar_size=$(du -h "$PROJECT_ROOT/main/manager-api/target/xiaozhi-esp32-api.jar" | cut -f1)
            print_info "  JAR size: $jar_size"
        else
            print_error "✗ Manager API - Build failed"
        fi
    fi

    if [[ "$SERVICE" == "web" || "$SERVICE" == "all" ]]; then
        if [ -d "$PROJECT_ROOT/main/manager-web/dist" ]; then
            print_success "✓ Manager Web - Built successfully"
            local dist_size=$(du -sh "$PROJECT_ROOT/main/manager-web/dist" | cut -f1)
            print_info "  Build size: $dist_size"
        else
            print_error "✗ Manager Web - Build failed"
        fi
    fi

    if [[ "$SERVICE" == "gateway" || "$SERVICE" == "all" ]]; then
        if [ -f "$PROJECT_ROOT/main/mqtt-gateway/app.js" ]; then
            print_success "✓ MQTT Gateway - Ready"
        else
            print_error "✗ MQTT Gateway - Build failed"
        fi
    fi

    echo ""
    print_info "Next steps:"
    print_info "  1. Test your builds locally"
    print_info "  2. Run deployment script: ./scripts/deploy.sh"
    print_info "  3. Manage services: ./scripts/manage-services.sh"
}

# Main build function
main() {
    print_info "Starting build process..."

    # Check prerequisites
    check_prerequisites

    # Build services based on selection
    case $SERVICE in
        api)
            build_manager_api || exit 1
            ;;
        web)
            build_manager_web || exit 1
            ;;
        gateway)
            build_mqtt_gateway || exit 1
            ;;
        all)
            build_manager_api || exit 1
            build_manager_web || exit 1
            build_mqtt_gateway || exit 1
            ;;
    esac

    # Show build summary
    show_build_summary

    print_success "Build process completed successfully!"
}

# Run main function
main "$@"