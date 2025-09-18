#!/bin/bash

# Install Xiaozhi Backend as Permanent Service
# This makes the backend run continuously and restart automatically

echo "⚙️  Installing Xiaozhi Backend Service"
echo "====================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo ./install-service.sh"
    exit 1
fi

# Variables
SERVICE_NAME="xiaozhi-backend"
WORK_DIR=$(pwd)
JAR_FILE="xiaozhi-esp32-api.jar"

# Check if JAR file exists
if [ ! -f "$JAR_FILE" ]; then
    echo "❌ JAR file not found: $JAR_FILE"
    echo "💡 Please build it first: mvn clean package -DskipTests"
    exit 1
fi

# Create systemd service file
echo "📝 Creating systemd service..."
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Xiaozhi ESP32 Backend Service
After=network.target docker.service
Wants=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$WORK_DIR
ExecStartPre=/bin/bash -c 'docker start xiaozhi-mysql xiaozhi-redis || true'
ExecStart=/usr/bin/java -jar $JAR_FILE --spring.profiles.active=azure --server.port=8002 --spring.datasource.url="jdbc:mysql://localhost:3306/xiaozhi_db?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=false&allowPublicKeyRetrieval=true&createDatabaseIfNotExist=true" --spring.datasource.username=xiaozhi_user --spring.datasource.password=xiaozhi_password123 --spring.data.redis.host=localhost --spring.data.redis.port=6379
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "🔄 Installing service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Stop any existing processes
echo "🛑 Stopping existing processes..."
pkill -f "$JAR_FILE" 2>/dev/null || true
sleep 3

# Start the service
echo "▶️  Starting service..."
systemctl start $SERVICE_NAME

# Wait and check status
sleep 10
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service installed and started successfully!"
    echo ""
    echo "📊 Service Status:"
    systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    echo "🎯 Your backend is now running permanently!"
    echo ""
    echo "📋 Service Management Commands:"
    echo "   sudo systemctl start $SERVICE_NAME    # Start service"
    echo "   sudo systemctl stop $SERVICE_NAME     # Stop service"
    echo "   sudo systemctl restart $SERVICE_NAME  # Restart service"
    echo "   sudo systemctl status $SERVICE_NAME   # Check status"
    echo "   sudo journalctl -u $SERVICE_NAME -f   # View logs"
    echo ""
    echo "🌐 Access Points:"
    echo "   Backend API: http://20.189.97.87:8002"
    echo "   Captcha: http://20.189.97.87:8002/toy/user/captcha"
    echo ""
    echo "✅ Users can now access your server 24/7!"
else
    echo "❌ Service failed to start"
    echo "📋 Check logs: sudo journalctl -u $SERVICE_NAME"
    systemctl status $SERVICE_NAME --no-pager -l
fi