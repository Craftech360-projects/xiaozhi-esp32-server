#!/bin/bash

# Azure Environment Setup Script
# This script sets up the complete environment for the Azure server

echo "🔧 Setting up Azure Environment..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script as root (use sudo)"
    exit 1
fi

# Variables
DB_NAME="xiaozhi_db"
DB_USER="xiaozhi_user"
DB_PASSWORD="xiaozhi_password123"

echo "📦 Installing required packages..."

# Update package list
apt-get update

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    rm get-docker.sh
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "🐙 Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose already installed"
fi

# Install Java if not already installed
if ! command -v java &> /dev/null; then
    echo "☕ Installing Java..."
    apt-get install -y openjdk-17-jdk
else
    echo "✅ Java already installed"
fi

# Install curl if not already installed
if ! command -v curl &> /dev/null; then
    echo "🌐 Installing curl..."
    apt-get install -y curl
else
    echo "✅ curl already installed"
fi

echo "🗄️  Setting up databases..."

# Stop existing containers
docker stop xiaozhi-mysql xiaozhi-redis 2>/dev/null || true
docker rm xiaozhi-mysql xiaozhi-redis 2>/dev/null || true

# Start MySQL container
echo "🐬 Starting MySQL..."
docker run -d \
    --name xiaozhi-mysql \
    --restart always \
    -p 3306:3306 \
    -e MYSQL_ROOT_PASSWORD=rootpassword \
    -e MYSQL_DATABASE=$DB_NAME \
    -e MYSQL_USER=$DB_USER \
    -e MYSQL_PASSWORD=$DB_PASSWORD \
    -e TZ=Asia/Shanghai \
    -v xiaozhi_mysql_data:/var/lib/mysql \
    mysql:8.0 \
    --character-set-server=utf8mb4 \
    --collation-server=utf8mb4_unicode_ci

# Start Redis container
echo "🔴 Starting Redis..."
docker run -d \
    --name xiaozhi-redis \
    --restart always \
    -p 6379:6379 \
    -e TZ=Asia/Shanghai \
    -v xiaozhi_redis_data:/data \
    redis:7-alpine \
    redis-server --appendonly yes

# Wait for databases to be ready
echo "⏳ Waiting for databases to be ready..."
sleep 30

# Test MySQL connection
echo "🧪 Testing MySQL connection..."
for i in {1..30}; do
    if docker exec xiaozhi-mysql mysqladmin ping -h localhost -u root -prootpassword --silent; then
        echo "✅ MySQL is ready!"
        break
    fi
    echo "  Waiting for MySQL... ($i/30)"
    sleep 2
done

# Test Redis connection
echo "🧪 Testing Redis connection..."
if docker exec xiaozhi-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready!"
else
    echo "❌ Redis connection failed"
    exit 1
fi

echo "🔥 Setting up firewall rules..."

# Install ufw if not already installed
if ! command -v ufw &> /dev/null; then
    echo "🛡️  Installing UFW firewall..."
    apt-get install -y ufw
fi

# Configure firewall
echo "🛡️  Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 8002/tcp comment 'Xiaozhi Backend API'
ufw allow 8886/tcp comment 'Xiaozhi Frontend'
ufw --force enable

echo "🎯 Environment setup complete!"
echo ""
echo "📋 Database Information:"
echo "  MySQL Host: localhost:3306"
echo "  Database: $DB_NAME"
echo "  Username: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo ""
echo "  Redis Host: localhost:6379"
echo ""
echo "🛡️  Firewall Configuration:"
echo "  Port 8002: Backend API (OPEN)"
echo "  Port 8886: Frontend (OPEN)"
echo "  SSH: OPEN"
echo ""
echo "📝 Next steps:"
echo "  1. Build your JAR file: mvn clean package -DskipTests"
echo "  2. Deploy the service: sudo ./deploy-azure.sh"
echo "  3. Check status: sudo ./service-manager.sh status"
echo "  4. Test external access: curl http://20.189.97.87:8002/toy/user/captcha"
echo ""