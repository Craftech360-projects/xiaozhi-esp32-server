#!/bin/bash

# Xiaozhi ESP32 Server Service Management Script
# This script provides convenient commands to manage PM2 services

set -eo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service names
SERVICES=("manager-api" "manager-web" "mqtt-gateway")
DEPLOY_PATH=${DEPLOY_PATH:-"/opt/xiaozhi-esp32-server"}

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
    echo "Usage: $0 <command> [service_name]"
    echo ""
    echo "Commands:"
    echo "  start [service]         Start all services or a specific service"
    echo "  stop [service]          Stop all services or a specific service"
    echo "  restart [service]       Restart all services or a specific service"
    echo "  status                  Show status of all services"
    echo "  logs [service]          Show logs for all services or a specific service"
    echo "  monitor                 Monitor services in real-time"
    echo "  reload [service]        Reload all services or a specific service"
    echo "  delete [service]        Delete all services or a specific service"
    echo "  list                    List all PM2 processes"
    echo ""
    echo "Services:"
    echo "  manager-api             Java Spring Boot API"
    echo "  manager-web             Vue.js Frontend"
    echo "  mqtt-gateway            Node.js MQTT Gateway"
    echo ""
    echo "Examples:"
    echo "  $0 start                # Start all services"
    echo "  $0 start manager-api    # Start only manager-api"
    echo "  $0 restart mqtt-gateway # Restart mqtt-gateway"
    echo "  $0 logs                 # Show logs for all services"
    echo "  $0 status               # Show status of all services"
}

# Check if PM2 is installed
check_pm2() {
    if ! command -v pm2 &> /dev/null; then
        print_error "PM2 is not installed. Please install PM2 globally:"
        print_info "npm install -g pm2"
        exit 1
    fi
}

# Validate service name
validate_service() {
    local service="$1"
    if [[ ! " ${SERVICES[@]} " =~ " ${service} " ]]; then
        print_error "Invalid service name: $service"
        print_info "Valid services: ${SERVICES[*]}"
        return 1
    fi
    return 0
}

# Start services
start_services() {
    local service="$1"

    if [ -n "$service" ]; then
        validate_service "$service" || return 1
        print_info "Starting $service..."
        pm2 start "$service" 2>/dev/null || pm2 restart "$service"
        print_success "$service started successfully"
    else
        print_info "Starting all services..."
        cd "$DEPLOY_PATH"
        pm2 start ecosystem.config.js 2>/dev/null || pm2 restart ecosystem.config.js
        print_success "All services started successfully"
    fi
}

# Stop services
stop_services() {
    local service="$1"

    if [ -n "$service" ]; then
        validate_service "$service" || return 1
        print_info "Stopping $service..."
        pm2 stop "$service"
        print_success "$service stopped successfully"
    else
        print_info "Stopping all services..."
        for svc in "${SERVICES[@]}"; do
            pm2 stop "$svc" 2>/dev/null || true
        done
        print_success "All services stopped successfully"
    fi
}

# Restart services
restart_services() {
    local service="$1"

    if [ -n "$service" ]; then
        validate_service "$service" || return 1
        print_info "Restarting $service..."
        pm2 restart "$service"
        print_success "$service restarted successfully"
    else
        print_info "Restarting all services..."
        for svc in "${SERVICES[@]}"; do
            pm2 restart "$svc" 2>/dev/null || true
        done
        print_success "All services restarted successfully"
    fi
}

# Show service status
show_status() {
    print_info "Service Status:"
    pm2 list

    echo ""
    print_info "Detailed Status:"
    for service in "${SERVICES[@]}"; do
        echo ""
        echo "=== $service ==="
        pm2 describe "$service" 2>/dev/null || print_warning "$service not found"
    done
}

# Show logs
show_logs() {
    local service="$1"

    if [ -n "$service" ]; then
        validate_service "$service" || return 1
        print_info "Showing logs for $service (Press Ctrl+C to exit)..."
        pm2 logs "$service"
    else
        print_info "Showing logs for all services (Press Ctrl+C to exit)..."
        pm2 logs
    fi
}

# Monitor services
monitor_services() {
    print_info "Starting PM2 monitor (Press Ctrl+C to exit)..."
    pm2 monit
}

# Reload services
reload_services() {
    local service="$1"

    if [ -n "$service" ]; then
        validate_service "$service" || return 1
        print_info "Reloading $service..."
        pm2 reload "$service"
        print_success "$service reloaded successfully"
    else
        print_info "Reloading all services..."
        for svc in "${SERVICES[@]}"; do
            pm2 reload "$svc" 2>/dev/null || true
        done
        print_success "All services reloaded successfully"
    fi
}

# Delete services
delete_services() {
    local service="$1"

    if [ -n "$service" ]; then
        validate_service "$service" || return 1
        print_warning "Deleting $service..."
        read -p "Are you sure you want to delete $service? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pm2 delete "$service"
            print_success "$service deleted successfully"
        else
            print_info "Delete cancelled"
        fi
    else
        print_warning "Deleting all services..."
        read -p "Are you sure you want to delete all services? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for svc in "${SERVICES[@]}"; do
                pm2 delete "$svc" 2>/dev/null || true
            done
            print_success "All services deleted successfully"
        else
            print_info "Delete cancelled"
        fi
    fi
}

# List all PM2 processes
list_processes() {
    print_info "All PM2 processes:"
    pm2 list
}

# Save PM2 configuration
save_config() {
    print_info "Saving PM2 configuration..."
    pm2 save
    print_success "PM2 configuration saved"
}

# Main function
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    check_pm2

    local command="$1"
    local service="$2"

    case $command in
        start)
            start_services "$service"
            save_config
            ;;
        stop)
            stop_services "$service"
            ;;
        restart)
            restart_services "$service"
            save_config
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "$service"
            ;;
        monitor)
            monitor_services
            ;;
        reload)
            reload_services "$service"
            save_config
            ;;
        delete)
            delete_services "$service"
            ;;
        list)
            list_processes
            ;;
        save)
            save_config
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            print_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"