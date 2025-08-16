#!/bin/bash

# Cheeko Backend Log Viewer
# This script shows live logs from all running backend services

echo "========================================="
echo "Cheeko Backend - Live Log Viewer"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check which services are running
echo -e "${YELLOW}Checking running services...${NC}"
echo ""

JAVA_RUNNING=false
PYTHON_RUNNING=false
MQTT_RUNNING=false

if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Java API Server is running on port 8002${NC}"
    JAVA_RUNNING=true
else
    echo -e "${RED}✗ Java API Server is not running${NC}"
fi

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ Python WebSocket Server is running on port 8000${NC}"
    PYTHON_RUNNING=true
else
    echo -e "${RED}✗ Python WebSocket Server is not running${NC}"
fi

if lsof -Pi :1883 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓ MQTT Gateway is running on port 1883${NC}"
    MQTT_RUNNING=true
else
    echo -e "${RED}✗ MQTT Gateway is not running${NC}"
fi

echo ""
echo "========================================="
echo "Starting Log Viewers"
echo "========================================="
echo ""

# Function to monitor logs
monitor_logs() {
    # Monitor Java API logs
    if [ "$JAVA_RUNNING" = true ]; then
        echo -e "${BLUE}[Starting Java API log monitor]${NC}"
        tail -f "$SCRIPT_DIR/main/manager-api/logs/xiaozhi-esp32-api.log" 2>/dev/null | while IFS= read -r line; do
            echo -e "${GREEN}[JAVA-API]${NC} $line"
        done &
    fi
    
    # Monitor Python WebSocket logs
    if [ "$PYTHON_RUNNING" = true ]; then
        echo -e "${BLUE}[Starting Python WebSocket log monitor]${NC}"
        tail -f "$SCRIPT_DIR/main/xiaozhi-server/websocket_full.log" 2>/dev/null | while IFS= read -r line; do
            echo -e "${YELLOW}[PYTHON-WS]${NC} $line"
        done &
    fi
    
    # Monitor MQTT Gateway logs
    if [ "$MQTT_RUNNING" = true ]; then
        echo -e "${BLUE}[Starting MQTT Gateway log monitor]${NC}"
        tail -f "$SCRIPT_DIR/main/mqtt-gateway/mqtt.log" 2>/dev/null | while IFS= read -r line; do
            echo -e "${BLUE}[MQTT-GW]${NC} $line"
        done &
    fi
}

# Start monitoring
monitor_logs

echo ""
echo -e "${YELLOW}Press Ctrl+C to stop viewing logs${NC}"
echo -e "${YELLOW}(This will NOT stop the services, only the log viewer)${NC}"
echo ""
echo "========================================="
echo ""

# Wait for Ctrl+C
wait