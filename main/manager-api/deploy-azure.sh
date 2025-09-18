#!/bin/bash

# Azure Production Deployment Script
# This script sets up the backend to run continuously with systemd service

echo "🚀 Starting Azure Production Deployment..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script as root (use sudo)"
    exit 1
fi

# Variables
SERVICE_NAME="xiaozhi-backend"
APP_DIR="/root/xiaozhi-esp32-server/main/manager-api"
JAR_FILE="xiaozhi-esp32-api.jar"

# Stop existing service if running
echo "🛑 Stopping existing service..."
systemctl stop $SERVICE_NAME 2>/dev/null || true
pkill -f "$JAR_FILE" || true
sleep 5

# Ensure directories exist
echo "📁 Setting up directories..."
mkdir -p $APP_DIR/logs

# Copy service file to systemd
echo "⚙️  Installing systemd service..."
cp $APP_DIR/xiaozhi-backend.service /etc/systemd/system/
chmod 644 /etc/systemd/system/xiaozhi-backend.service

# Reload systemd and enable service
echo "🔄 Reloading systemd..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Start the service
echo "▶️  Starting $SERVICE_NAME service..."
systemctl start $SERVICE_NAME

# Wait a moment for startup
sleep 15

# Check service status
echo "🔍 Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service is running successfully!"

    # Show service status
    systemctl status $SERVICE_NAME --no-pager -l

    # Test the endpoint
    echo ""
    echo "🧪 Testing API endpoint..."
    sleep 5
    if curl -s -f http://localhost:8002/toy/user/captcha > /dev/null; then
        echo "✅ API endpoint is responding!"
    else
        echo "⚠️  API endpoint not responding yet (may still be starting up)"
    fi

    echo ""
    echo "📋 Service Management Commands:"
    echo "  Start:   sudo systemctl start $SERVICE_NAME"
    echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
    echo "  Restart: sudo systemctl restart $SERVICE_NAME"
    echo "  Status:  sudo systemctl status $SERVICE_NAME"
    echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    echo "🌐 Backend is now running continuously at: http://localhost:8002"
    echo "✅ Using LOCAL Azure VM database - NO external cloud databases"
else
    echo "❌ Service failed to start!"
    echo "📋 Check logs with: sudo journalctl -u $SERVICE_NAME -f"
    systemctl status $SERVICE_NAME --no-pager -l
    exit 1
fi