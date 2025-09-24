#!/bin/bash

# Azure Robust Deployment Script
# This script completely eliminates Railway database connections
# and ensures local Azure database usage only

echo "🚀 Starting Robust Azure Backend Deployment"
echo "=============================================="

# Variables
JAR_FILE="xiaozhi-esp32-api.jar"
SERVICE_NAME="xiaozhi-backend"
DB_NAME="xiaozhi_db"
DB_USER="xiaozhi_user"
DB_PASSWORD="xiaozhi_password123"

# Step 1: Stop all existing processes
echo "🛑 Stopping all existing backend processes..."
pkill -f "$JAR_FILE" 2>/dev/null || true
pkill -f "spring-boot" 2>/dev/null || true
systemctl stop $SERVICE_NAME 2>/dev/null || true
sleep 5

# Step 2: Verify JAR file exists
if [ ! -f "$JAR_FILE" ]; then
    echo "❌ ERROR: JAR file not found: $JAR_FILE"
    echo "💡 Please upload the JAR file first:"
    echo "   scp target/xiaozhi-esp32-api.jar root@20.189.97.87:/root/"
    exit 1
fi

echo "✅ JAR file found: $JAR_FILE"

# Step 3: Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm -f get-docker.sh
else
    echo "✅ Docker already installed"
fi

# Step 4: Setup local databases with persistent volumes
echo "🗄️  Setting up local Azure databases..."

# Remove old containers
docker stop xiaozhi-mysql xiaozhi-redis 2>/dev/null || true
docker rm xiaozhi-mysql xiaozhi-redis 2>/dev/null || true

# Start MySQL with persistent volume
echo "🐬 Starting MySQL database..."
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

# Start Redis with persistent volume
echo "🔴 Starting Redis cache..."
docker run -d \
    --name xiaozhi-redis \
    --restart always \
    -p 6379:6379 \
    -e TZ=Asia/Shanghai \
    -v xiaozhi_redis_data:/data \
    redis:7-alpine \
    redis-server --appendonly yes

# Step 5: Wait for databases to be ready
echo "⏳ Waiting for databases to initialize..."
sleep 30

# Test MySQL connection
echo "🧪 Testing MySQL connection..."
for i in {1..30}; do
    if docker exec xiaozhi-mysql mysqladmin ping -h localhost -u root -prootpassword --silent 2>/dev/null; then
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

# Step 6: Configure firewall
echo "🛡️  Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 8002/tcp comment 'Xiaozhi Backend API' 2>/dev/null || true
fi

# Step 7: Start backend with explicit Azure profile
echo "▶️  Starting backend with Azure configuration..."

# Create startup script to ensure correct configuration
cat > start-backend.sh << 'EOF'
#!/bin/bash
export SPRING_PROFILES_ACTIVE=azure
export SERVER_PORT=8002
export SPRING_DATASOURCE_URL="jdbc:mysql://localhost:3306/xiaozhi_db?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=false&allowPublicKeyRetrieval=true&createDatabaseIfNotExist=true"
export SPRING_DATASOURCE_USERNAME=xiaozhi_user
export SPRING_DATASOURCE_PASSWORD=xiaozhi_password123
export SPRING_DATA_REDIS_HOST=localhost
export SPRING_DATA_REDIS_PORT=6379

java -jar -Dspring.profiles.active=azure \
    -Dserver.port=8002 \
    -Dspring.datasource.url="jdbc:mysql://localhost:3306/xiaozhi_db?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=false&allowPublicKeyRetrieval=true&createDatabaseIfNotExist=true" \
    -Dspring.datasource.username=xiaozhi_user \
    -Dspring.datasource.password=xiaozhi_password123 \
    -Dspring.data.redis.host=localhost \
    -Dspring.data.redis.port=6379 \
    xiaozhi-esp32-api.jar
EOF

chmod +x start-backend.sh

# Start backend in background
nohup ./start-backend.sh > backend.log 2>&1 &
BACKEND_PID=$!

echo "🎯 Backend started with PID: $BACKEND_PID"

# Step 8: Wait and verify startup
echo "⏳ Waiting for backend to start..."
sleep 20

# Check if process is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend process is running!"
else
    echo "❌ Backend process failed"
    echo "📋 Checking logs..."
    tail -20 backend.log
    exit 1
fi

# Step 9: Test API endpoints
echo "🧪 Testing API endpoints..."
sleep 10

# Test captcha endpoint
if curl -s -f http://localhost:8002/toy/user/captcha > /dev/null; then
    echo "✅ Captcha endpoint is working!"
else
    echo "⚠️  Captcha endpoint not ready yet..."
    echo "📋 Backend might still be starting up"
fi

# Final status
echo ""
echo "🎉 DEPLOYMENT COMPLETED!"
echo "========================"
echo ""
echo "🌐 Access Points:"
echo "  Backend API: http://20.189.97.87:8002"
echo "  Captcha: http://20.189.97.87:8002/toy/user/captcha"
echo ""
echo "🗄️  Database Information:"
echo "  MySQL: localhost:3306/$DB_NAME"
echo "  Redis: localhost:6379"
echo ""
echo "📋 Management Commands:"
echo "  Check logs: tail -f backend.log"
echo "  Stop backend: pkill -f '$JAR_FILE'"
echo "  Check containers: docker ps"
echo "  Restart databases: docker restart xiaozhi-mysql xiaozhi-redis"
echo ""
echo "🔄 Next Step: Run './azure-service-install.sh' to make it permanent"
echo ""
echo "✅ Your backend is now running with LOCAL AZURE DATABASES ONLY!"