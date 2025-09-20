#!/bin/bash

# Xiaozhi Backend Service Manager
# Convenient script for managing the backend service

SERVICE_NAME="xiaozhi-backend"

show_help() {
    echo "🔧 Xiaozhi Backend Service Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the backend service"
    echo "  stop      Stop the backend service"
    echo "  restart   Restart the backend service"
    echo "  status    Show service status"
    echo "  logs      Show live logs"
    echo "  install   Install and start the service"
    echo "  health    Check API health"
    echo "  help      Show this help message"
    echo ""
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "❌ Please run this script as root (use sudo)"
        exit 1
    fi
}

start_service() {
    check_root
    echo "▶️  Starting $SERVICE_NAME..."
    systemctl start $SERVICE_NAME
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Service started successfully!"
    else
        echo "❌ Failed to start service"
        systemctl status $SERVICE_NAME --no-pager -l
    fi
}

stop_service() {
    check_root
    echo "🛑 Stopping $SERVICE_NAME..."
    systemctl stop $SERVICE_NAME
    sleep 2
    if ! systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Service stopped successfully!"
    else
        echo "❌ Failed to stop service"
    fi
}

restart_service() {
    check_root
    echo "🔄 Restarting $SERVICE_NAME..."
    systemctl restart $SERVICE_NAME
    sleep 5
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Service restarted successfully!"
    else
        echo "❌ Failed to restart service"
        systemctl status $SERVICE_NAME --no-pager -l
    fi
}

show_status() {
    echo "📊 Service Status:"
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "🟢 Service is RUNNING"
    else
        echo "🔴 Service is STOPPED"
    fi
}

show_logs() {
    echo "📋 Live logs (Press Ctrl+C to exit):"
    journalctl -u $SERVICE_NAME -f
}

install_service() {
    check_root
    echo "📦 Installing $SERVICE_NAME..."
    ./deploy-azure.sh
}

check_health() {
    echo "🏥 Checking API health..."
    if curl -s -f http://localhost:8002/toy/user/captcha > /dev/null; then
        echo "✅ API is healthy and responding!"
        echo "🌐 Backend URL: http://localhost:8002"
    else
        echo "❌ API is not responding"
        echo "💡 Try: $0 status or $0 logs"
    fi
}

case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    install)
        install_service
        ;;
    health)
        check_health
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac