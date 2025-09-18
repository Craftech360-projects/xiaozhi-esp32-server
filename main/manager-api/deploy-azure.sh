#!/bin/bash

# Azure Deployment Script
# This script ensures the backend ALWAYS uses local Azure VM databases

echo "Starting Azure deployment..."

# Stop any existing Java processes
echo "Stopping existing backend processes..."
pkill -f "xiaozhi-esp32-api.jar" || true

# Wait for processes to stop
sleep 5

# Start with AZURE profile (local database only)
echo "Starting backend with Azure local database configuration..."
nohup java -jar xiaozhi-esp32-api.jar \
    --spring.profiles.active=azure \
    --server.port=8002 \
    --spring.datasource.url="jdbc:mysql://localhost:3306/xiaozhi_db?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=false&allowPublicKeyRetrieval=true&createDatabaseIfNotExist=true" \
    --spring.datasource.username=xiaozhi_user \
    --spring.datasource.password=xiaozhi_password123 \
    --spring.data.redis.host=localhost \
    --spring.data.redis.port=6379 \
    > backend.log 2>&1 &

echo "Backend started with PID: $!"
echo "Using LOCAL Azure VM database - NO external cloud databases"
echo "Check logs: tail -f backend.log"

# Verify it's running
sleep 10
if pgrep -f "xiaozhi-esp32-api.jar" > /dev/null; then
    echo "✅ Backend successfully started with local Azure database"
    echo "✅ NO Railway or external databases will be used"
else
    echo "❌ Failed to start backend"
    exit 1
fi