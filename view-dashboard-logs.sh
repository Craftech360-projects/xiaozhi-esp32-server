#!/bin/bash

# Script to view logs for dashboard services

echo "📋 Cheeko Dashboard Logs Viewer"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "Choose which logs to view:"
echo "1) Java Backend (manager-api)"
echo "2) Vue Frontend (manager-web)"
echo "3) Both (in split view with tail -f)"
echo "4) Exit"
echo ""
echo -n "Enter your choice (1-4): "
read choice

case $choice in
    1)
        echo -e "\n${BLUE}Viewing Java Backend logs...${NC}"
        if [ -f "logs/manager-api.log" ]; then
            tail -f logs/manager-api.log
        else
            echo -e "${YELLOW}No backend logs found yet. Start the dashboard first.${NC}"
        fi
        ;;
    2)
        echo -e "\n${BLUE}Viewing Vue Frontend logs...${NC}"
        if [ -f "logs/manager-web.log" ]; then
            tail -f logs/manager-web.log
        else
            echo -e "${YELLOW}No frontend logs found yet. Start the dashboard first.${NC}"
        fi
        ;;
    3)
        echo -e "\n${BLUE}Viewing both logs (press Ctrl+C to exit)...${NC}"
        echo -e "${GREEN}=============== BACKEND LOGS ===============${NC}"
        if [ -f "logs/manager-api.log" ]; then
            tail -n 20 logs/manager-api.log
        else
            echo -e "${YELLOW}No backend logs found${NC}"
        fi
        echo -e "\n${GREEN}=============== FRONTEND LOGS ===============${NC}"
        if [ -f "logs/manager-web.log" ]; then
            tail -n 20 logs/manager-web.log
        else
            echo -e "${YELLOW}No frontend logs found${NC}"
        fi
        echo -e "\n${YELLOW}Watching for new logs...${NC}\n"
        
        # Use multitail if available, otherwise use a simple approach
        if command -v multitail &> /dev/null; then
            multitail logs/manager-api.log logs/manager-web.log
        else
            # Simple approach: alternate between files
            tail -f logs/manager-api.log logs/manager-web.log 2>/dev/null
        fi
        ;;
    4)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac