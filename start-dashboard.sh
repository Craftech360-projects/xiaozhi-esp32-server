#!/bin/bash

# Script to start both manager-api backend and manager-web frontend

echo "🚀 Starting Cheeko Dashboard Services..."
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo -e "${RED}❌ Java is not installed. Please install Java 17 or higher.${NC}"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed. Please install Node.js and npm.${NC}"
    exit 1
fi

# Check if ports are already in use
if check_port 8002; then
    echo -e "${YELLOW}⚠️  Port 8002 is already in use, killing existing process...${NC}"
    kill $(lsof -t -i:8002) 2>/dev/null
    sleep 2
fi

if check_port 8001; then
    echo -e "${YELLOW}⚠️  Port 8001 is already in use, killing existing process...${NC}"
    kill $(lsof -t -i:8001) 2>/dev/null
    sleep 2
fi

# Start Java backend (manager-api)
echo -e "\n${GREEN}1. Starting Java Backend (manager-api) on port 8002...${NC}"
cd main/manager-api

# Check if target JAR exists, if not build it
if [ ! -f "target/xiaozhi-esp32-api.jar" ]; then
    echo "Building Java backend..."
    mvn clean package -DskipTests
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to build Java backend${NC}"
        exit 1
    fi
fi

# Start the Java application in background
nohup java -jar target/xiaozhi-esp32-api.jar > ../../logs/manager-api.log 2>&1 &
JAVA_PID=$!
echo "Java backend started with PID: $JAVA_PID"

# Wait for Java backend to be ready
echo "Waiting for Java backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8002/xiaozhi > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Java backend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

# Go back to root directory
cd ../..

# Start Vue frontend (manager-web)
echo -e "\n${GREEN}2. Starting Vue Frontend (manager-web) on port 8001...${NC}"
cd main/manager-web

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    fi
fi

# Start the Vue application in background
nohup npm run serve > ../../logs/manager-web.log 2>&1 &
VUE_PID=$!
echo "Vue frontend started with PID: $VUE_PID"

# Go back to root directory
cd ../..

# Save PIDs to file for later shutdown
echo "$JAVA_PID" > .dashboard-pids
echo "$VUE_PID" >> .dashboard-pids

# Wait for Vue frontend to be ready
echo "Waiting for Vue frontend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8001 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Vue frontend is ready!${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Dashboard Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Access the dashboard at: http://localhost:8001"
echo "🔧 Java API backend running at: http://localhost:8002/xiaozhi"
echo ""
echo "📝 Logs are available at:"
echo "   - Backend: logs/manager-api.log"
echo "   - Frontend: logs/manager-web.log"
echo ""
echo "To stop all services, run: ./stop-dashboard.sh"
echo ""
echo -e "${YELLOW}Default credentials:${NC}"
echo "   Username: admin"
echo "   Password: admin (you should change this!)"