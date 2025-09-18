#!/bin/bash

# Azure Manual Deployment Script
# Copy and paste this entire script on your Azure VM terminal

echo "🚀 Starting Azure Backend Deployment"
echo "===================================="

# Step 1: Install required packages
echo "📦 Installing required packages..."
apt-get update
apt-get install -y openjdk-17-jdk curl docker.io

# Start Docker
systemctl start docker
systemctl enable docker

# Step 2: Setup databases
echo "🗄️  Setting up local databases..."

# Stop and remove old containers
docker stop xiaozhi-mysql xiaozhi-redis 2>/dev/null || true
docker rm xiaozhi-mysql xiaozhi-redis 2>/dev/null || true

# Start MySQL
echo "🐬 Starting MySQL..."
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
echo "🔴 Starting Redis..."
docker run -d \
    --name xiaozhi-redis \
    --restart always \
    -p 6379:6379 \
    redis:7-alpine

# Wait for databases
echo "⏳ Waiting for databases to start..."
sleep 30

# Step 3: Create the JAR file URL (you need to replace this)
echo "📥 You need to upload the JAR file first!"
echo ""
echo "Either:"
echo "1. Upload xiaozhi-esp32-api.jar to /root/ using your preferred method"
echo "2. Or download it from a URL:"
echo "   wget -O /root/xiaozhi-esp32-api.jar YOUR_JAR_FILE_URL"
echo ""
echo "After uploading the JAR file, run:"
echo ""
echo "# Start the backend service"
echo "cd /root"
echo "nohup java -jar xiaozhi-esp32-api.jar \\"
echo "    --spring.profiles.active=azure \\"
echo "    --server.port=8002 \\"
echo "    --spring.datasource.url=\"jdbc:mysql://localhost:3306/xiaozhi_db?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=false&allowPublicKeyRetrieval=true&createDatabaseIfNotExist=true\" \\"
echo "    --spring.datasource.username=xiaozhi_user \\"
echo "    --spring.datasource.password=xiaozhi_password123 \\"
echo "    --spring.data.redis.host=localhost \\"
echo "    --spring.data.redis.port=6379 \\"
echo "    > backend.log 2>&1 &"
echo ""
echo "# Check if it's running"
echo "sleep 15"
echo "curl http://localhost:8002/toy/user/captcha"
echo ""
echo "# Open firewall"
echo "ufw allow 8002"
echo ""
echo "✅ After this, your backend will be available at http://20.189.97.87:8002"