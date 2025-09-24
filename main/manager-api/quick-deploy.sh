#!/bin/bash

# Quick Azure VM Deployment - Get Backend Running Now!
# Run this on your Azure VM to start the backend service

echo "🚀 Quick Azure VM Backend Deployment"
echo "======================================"

# Variables
JAR_FILE="xiaozhi-esp32-api.jar"
PROFILE="azure"
PORT="8002"

# Step 1: Stop any existing backend processes
echo "🛑 Stopping existing backend processes..."
pkill -f "$JAR_FILE" 2>/dev/null || true
pkill -f "spring-boot" 2>/dev/null || true
sleep 3

# Step 2: Check if JAR file exists
if [ ! -f "$JAR_FILE" ]; then
    echo "❌ JAR file not found: $JAR_FILE"
    echo "💡 Please build it first: mvn clean package -DskipTests"
    exit 1
fi

# Step 3: Setup local databases (MySQL & Redis)
echo "🗄️  Setting up local databases..."

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# Stop and remove old containers
docker stop xiaozhi-mysql xiaozhi-redis 2>/dev/null || true
docker rm xiaozhi-mysql xiaozhi-redis 2>/dev/null || true

# Start MySQL
echo "🐬 Starting MySQL database..."
docker run -d \
    --name xiaozhi-mysql \
    --restart always \
    -p 3306:3306 \
    -e MYSQL_ROOT_PASSWORD=rootpassword \
    -e MYSQL_DATABASE=xiaozhi_db \
    -e MYSQL_USER=xiaozhi_user \
    -e MYSQL_PASSWORD=xiaozhi_password123 \
    mysql:8.0

# Start Redis
echo "🔴 Starting Redis cache..."
docker run -d \
    --name xiaozhi-redis \
    --restart always \
    -p 6379:6379 \
    redis:7-alpine

# Wait for databases
echo "⏳ Waiting for databases to start..."
sleep 20

# Step 4: Start backend service
echo "▶️  Starting Java backend service..."
nohup java -jar "$JAR_FILE" \
    --spring.profiles.active=$PROFILE \
    --server.port=$PORT \
    --spring.datasource.url="jdbc:mysql://localhost:3306/xiaozhi_db?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=false&allowPublicKeyRetrieval=true&createDatabaseIfNotExist=true" \
    --spring.datasource.username=xiaozhi_user \
    --spring.datasource.password=xiaozhi_password123 \
    --spring.data.redis.host=localhost \
    --spring.data.redis.port=6379 \
    > backend.log 2>&1 &

BACKEND_PID=$!
echo "🎯 Backend started with PID: $BACKEND_PID"

# Step 5: Wait and verify
echo "⏳ Waiting for backend to start..."
sleep 15

# Check if process is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend process is running!"
else
    echo "❌ Backend process failed to start"
    echo "📋 Check logs: tail -f backend.log"
    exit 1
fi

# Test the API
echo "🧪 Testing API endpoint..."
sleep 5
if curl -s -f http://localhost:$PORT/toy/user/captcha > /dev/null; then
    echo "✅ API is responding!"
    echo ""
    echo "🌐 Your backend is now running at:"
    echo "   - Internal: http://localhost:$PORT"
    echo "   - External: http://YOUR_AZURE_IP:$PORT"
    echo ""
    echo "🔍 Captcha endpoint: http://YOUR_AZURE_IP:$PORT/toy/user/captcha"
    echo ""
    echo "📋 Management commands:"
    echo "   Check logs: tail -f backend.log"
    echo "   Stop service: pkill -f '$JAR_FILE'"
    echo "   Check process: ps aux | grep java"
    echo ""
    echo "✅ DEPLOYMENT COMPLETE - Users can now access your server!"
else
    echo "⚠️  API not responding yet, but service is starting..."
    echo "📋 Check logs: tail -f backend.log"
    echo "🔄 It may take a few more minutes to fully start"
fi