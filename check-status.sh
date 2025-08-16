#!/bin/bash

# Cheeko Backend Status Check
# This script checks the status of all backend services

echo "========================================="
echo "Cheeko Backend Services Status"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check service
check_service() {
    local port=$1
    local name=$2
    local url=$3
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✓ $name${NC}"
        echo "  Port: $port"
        echo "  Status: Running"
        if [ ! -z "$url" ]; then
            echo "  URL: $url"
        fi
        echo ""
        return 0
    else
        echo -e "${RED}✗ $name${NC}"
        echo "  Port: $port"
        echo "  Status: Stopped"
        echo ""
        return 1
    fi
}

# Check each service
echo -e "${BLUE}Service Status:${NC}"
echo "----------------------------------------"

SERVICES_RUNNING=0

check_service 8002 "Java Spring Boot API" "http://localhost:8002/xiaozhi"
if [ $? -eq 0 ]; then
    ((SERVICES_RUNNING++))
fi

check_service 8000 "Python WebSocket Server" "ws://192.168.1.239:8000/xiaozhi/v1/"
if [ $? -eq 0 ]; then
    ((SERVICES_RUNNING++))
fi

check_service 8003 "Python HTTP/OTA Server" "http://192.168.1.239:8003/xiaozhi/ota/"
if [ $? -eq 0 ]; then
    ((SERVICES_RUNNING++))
fi

check_service 1883 "MQTT Gateway" "mqtt://192.168.1.239:1883"
if [ $? -eq 0 ]; then
    ((SERVICES_RUNNING++))
fi

check_service 8884 "UDP Server (MQTT)" "udp://192.168.1.239:8884"
if [ $? -eq 0 ]; then
    ((SERVICES_RUNNING++))
fi

# Summary
echo "========================================="
echo -e "${BLUE}Summary:${NC}"
echo "----------------------------------------"

if [ $SERVICES_RUNNING -eq 5 ]; then
    echo -e "${GREEN}All services are running! ($SERVICES_RUNNING/5)${NC}"
    echo ""
    echo "ESP32 Device Configuration:"
    echo "  MQTT Host: 192.168.1.239"
    echo "  MQTT Port: 1883"
    echo "  OTA URL: http://192.168.1.239:8003/xiaozhi/ota/"
    echo "  WebSocket: ws://192.168.1.239:8000/xiaozhi/v1/"
elif [ $SERVICES_RUNNING -eq 0 ]; then
    echo -e "${RED}No services are running! (0/5)${NC}"
    echo ""
    echo "To start all services, run:"
    echo "  ./start-backend.sh"
else
    echo -e "${YELLOW}Some services are running ($SERVICES_RUNNING/5)${NC}"
    echo ""
    echo "To restart all services, run:"
    echo "  ./stop-backend.sh"
    echo "  ./start-backend.sh"
fi

echo ""
echo "========================================="

# Check for connected devices
echo -e "${BLUE}Connected Devices:${NC}"
echo "----------------------------------------"

# Check MQTT connections
if lsof -Pi :1883 -sTCP:LISTEN -t >/dev/null ; then
    CONNECTIONS=$(lsof -i :1883 | grep -c "ESTABLISHED" 2>/dev/null || echo "0")
    if [ "$CONNECTIONS" -gt 0 ]; then
        echo -e "${GREEN}$CONNECTIONS device(s) connected via MQTT${NC}"
    else
        echo "No devices currently connected"
    fi
else
    echo "MQTT Gateway not running"
fi

echo ""