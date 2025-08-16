#!/bin/bash

# Script to stop both manager-api backend and manager-web frontend

echo "🛑 Stopping Cheeko Dashboard Services..."
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Read PIDs from file if it exists
if [ -f ".dashboard-pids" ]; then
    echo "Reading PIDs from .dashboard-pids file..."
    JAVA_PID=$(sed -n '1p' .dashboard-pids)
    VUE_PID=$(sed -n '2p' .dashboard-pids)
    
    # Stop Java backend
    if ps -p $JAVA_PID > /dev/null 2>&1; then
        echo "Stopping Java backend (PID: $JAVA_PID)..."
        kill $JAVA_PID
        echo -e "${GREEN}✅ Java backend stopped${NC}"
    else
        echo -e "${YELLOW}Java backend not running (PID: $JAVA_PID)${NC}"
    fi
    
    # Stop Vue frontend
    if ps -p $VUE_PID > /dev/null 2>&1; then
        echo "Stopping Vue frontend (PID: $VUE_PID)..."
        kill $VUE_PID
        echo -e "${GREEN}✅ Vue frontend stopped${NC}"
    else
        echo -e "${YELLOW}Vue frontend not running (PID: $VUE_PID)${NC}"
    fi
    
    # Remove PID file
    rm .dashboard-pids
else
    echo -e "${YELLOW}No .dashboard-pids file found. Searching for processes...${NC}"
fi

# Also check for any remaining processes on the ports
echo ""
echo "Checking for any remaining processes..."

# Check port 8002 (Java backend)
if lsof -i :8002 > /dev/null 2>&1; then
    echo "Found process on port 8002, stopping..."
    kill $(lsof -t -i:8002) 2>/dev/null
    echo -e "${GREEN}✅ Stopped process on port 8002${NC}"
fi

# Check port 8001 (Vue frontend)
if lsof -i :8001 > /dev/null 2>&1; then
    echo "Found process on port 8001, stopping..."
    kill $(lsof -t -i:8001) 2>/dev/null
    echo -e "${GREEN}✅ Stopped process on port 8001${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Dashboard Services Stopped${NC}"
echo -e "${GREEN}========================================${NC}"