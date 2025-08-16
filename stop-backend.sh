#!/bin/bash

# Cheeko Backend Stop Script
# This script stops all backend services

echo "========================================="
echo "Stopping Cheeko Backend Services"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Stop Java API Server
echo -e "${YELLOW}Stopping Java API Server...${NC}"
pkill -f "xiaozhi-esp32-api.jar" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Java API Server stopped${NC}"
else
    echo -e "${RED}Java API Server was not running${NC}"
fi

# Stop Python WebSocket Server
echo -e "${YELLOW}Stopping Python WebSocket Server...${NC}"
pkill -f "xiaozhi-server/app.py" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python WebSocket Server stopped${NC}"
else
    echo -e "${RED}Python WebSocket Server was not running${NC}"
fi

# Stop MQTT Gateway
echo -e "${YELLOW}Stopping MQTT Gateway...${NC}"
pkill -f "mqtt-gateway/app.js" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MQTT Gateway stopped${NC}"
else
    echo -e "${RED}MQTT Gateway was not running${NC}"
fi

echo ""
echo -e "${GREEN}All services have been stopped.${NC}"
echo ""