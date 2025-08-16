#!/bin/bash

# Cheeko Backend Startup Script
# This script starts all three backend services with detailed console logging

echo "========================================="
echo "Starting Cheeko Backend Services"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}Port $1 is already in use!${NC}"
        echo "Please stop the existing service or change the port."
        return 1
    fi
    return 0
}

# Kill existing services
echo -e "${YELLOW}Stopping any existing services...${NC}"
pkill -f "xiaozhi-esp32-api.jar" 2>/dev/null
pkill -f "xiaozhi-server/app.py" 2>/dev/null
pkill -f "mqtt-gateway/app.js" 2>/dev/null
sleep 2

# Check ports
echo -e "${YELLOW}Checking ports availability...${NC}"
check_port 8002 || exit 1
check_port 8000 || exit 1
check_port 8003 || exit 1
check_port 1883 || exit 1

echo -e "${GREEN}All ports are available!${NC}"
echo ""

# Start Java API Server
echo -e "${GREEN}[1/3] Starting Java Spring Boot API Server...${NC}"
echo "Port: 8002"
echo "Database: Railway MySQL"
echo "----------------------------------------"
cd "$SCRIPT_DIR/main/manager-api"
java -jar target/xiaozhi-esp32-api.jar 2>&1 | while IFS= read -r line; do
    echo "[JAVA-API] $line"
done &
JAVA_PID=$!
echo "Java API PID: $JAVA_PID"
echo ""

# Wait for Java API to start
echo "Waiting for Java API to initialize..."
sleep 10

# Start Python WebSocket Server
echo -e "${GREEN}[2/3] Starting Python WebSocket Server...${NC}"
echo "WebSocket Port: 8000"
echo "HTTP/OTA Port: 8003"
echo "----------------------------------------"
cd "$SCRIPT_DIR/main/xiaozhi-server"
python app.py 2>&1 | while IFS= read -r line; do
    echo "[PYTHON-WS] $line"
done &
PYTHON_PID=$!
echo "Python WebSocket PID: $PYTHON_PID"
echo ""

# Wait for Python server to start
echo "Waiting for Python server to initialize..."
sleep 5

# Start MQTT Gateway
echo -e "${GREEN}[3/3] Starting MQTT Gateway...${NC}"
echo "MQTT Port: 1883"
echo "UDP Port: 8884"
echo "----------------------------------------"
cd "$SCRIPT_DIR/main/mqtt-gateway"
node app.js 2>&1 | while IFS= read -r line; do
    echo "[MQTT-GW] $line"
done &
MQTT_PID=$!
echo "MQTT Gateway PID: $MQTT_PID"
echo ""

# Display service information
echo ""
echo "========================================="
echo -e "${GREEN}All Services Started Successfully!${NC}"
echo "========================================="
echo ""
echo "Service URLs:"
echo "-------------"
echo "📊 Java API Documentation: http://localhost:8002/xiaozhi/doc.html"
echo "🔌 WebSocket Endpoint: ws://192.168.1.239:8000/xiaozhi/v1/"
echo "📦 OTA Update URL: http://192.168.1.239:8003/xiaozhi/ota/"
echo "👁️ Vision API: http://192.168.1.239:8003/mcp/vision/explain"
echo "📡 MQTT Broker: 192.168.1.239:1883"
echo ""
echo "ESP32 Configuration:"
echo "-------------------"
echo "MQTT Host: 192.168.1.239"
echo "MQTT Port: 1883"
echo "OTA URL: http://192.168.1.239:8003/xiaozhi/ota/"
echo ""
echo "Process IDs:"
echo "------------"
echo "Java API: $JAVA_PID"
echo "Python WebSocket: $PYTHON_PID"
echo "MQTT Gateway: $MQTT_PID"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""
echo "========================================="
echo "Live Logs (All Services)"
echo "========================================="
echo ""

# Function to handle Ctrl+C
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping all services...${NC}"
    kill $JAVA_PID 2>/dev/null
    kill $PYTHON_PID 2>/dev/null
    kill $MQTT_PID 2>/dev/null
    pkill -f "xiaozhi-esp32-api.jar" 2>/dev/null
    pkill -f "xiaozhi-server/app.py" 2>/dev/null
    pkill -f "mqtt-gateway/app.js" 2>/dev/null
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

# Set up trap for Ctrl+C
trap cleanup INT

# Keep the script running
wait