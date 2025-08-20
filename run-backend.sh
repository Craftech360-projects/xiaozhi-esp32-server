#!/bin/bash

# Cheeko Backend Startup Script
# This script handles the complete backend setup for the Cheeko parental control application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_DIR="main/manager-api"
BACKEND_PORT=8002
DATABASE_HOST="caboose.proxy.rlwy.net"
DATABASE_PORT=41629
DATABASE_NAME="railway"

echo -e "${BLUE}🚀 Starting Cheeko Backend Services${NC}"
echo "=================================="

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}⚠️  Port $1 is already in use${NC}"
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    echo -e "${BLUE}⏳ Waiting for $service_name to start...${NC}"
    
    for i in {1..30}; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is running${NC}"
            return 0
        fi
        sleep 2
    done
    echo -e "${RED}❌ $service_name failed to start within 60 seconds${NC}"
    return 1
}

# Function to test database connectivity
test_database() {
    echo -e "${BLUE}🔍 Testing database connectivity...${NC}"
    
    if [ ! -d "$BACKEND_DIR" ]; then
        echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}⚠️  Database connection test skipped (using Railway MySQL directly)${NC}"
    return 0
}

# Function to start the backend
start_backend() {
    echo -e "${BLUE}🏗️  Starting Spring Boot Backend...${NC}"
    
    if check_port $BACKEND_PORT; then
        echo -e "${YELLOW}Backend may already be running on port $BACKEND_PORT${NC}"
        read -p "Do you want to continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Startup cancelled${NC}"
            exit 1
        fi
    fi
    
    cd $BACKEND_DIR
    echo -e "${BLUE}📦 Building and starting Spring Boot application...${NC}"
    
    # Start Spring Boot in background
    nohup mvn spring-boot:run > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    
    echo -e "${GREEN}🔧 Backend started with PID: $BACKEND_PID${NC}"
    cd - > /dev/null
}

# Function to test endpoints
test_endpoints() {
    echo -e "${BLUE}🧪 Testing API endpoints...${NC}"
    
    BASE_URL="http://localhost:$BACKEND_PORT/xiaozhi"
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s "$BASE_URL/api/mobile/health" | grep -q "success"; then
        echo -e "${GREEN}✅ Health endpoint working${NC}"
    else
        echo -e "${RED}❌ Health endpoint failed${NC}"
    fi
    
    # Test activation code check
    echo "Testing activation code endpoint..."
    if curl -s "$BASE_URL/api/mobile/activation/check-code?code=123456" | grep -q "valid"; then
        echo -e "${GREEN}✅ Activation endpoint working${NC}"
    else
        echo -e "${RED}❌ Activation endpoint failed${NC}"
    fi
    
    # Test API documentation
    echo "Testing API documentation..."
    if curl -s -f "$BASE_URL/doc.html" > /dev/null; then
        echo -e "${GREEN}✅ API documentation available at: $BASE_URL/doc.html${NC}"
    else
        echo -e "${YELLOW}⚠️  API documentation not accessible${NC}"
    fi
}

# Function to show status
show_status() {
    echo -e "${BLUE}📊 Backend Status${NC}"
    echo "=================="
    echo "Backend URL: http://localhost:$BACKEND_PORT/xiaozhi"
    echo "API Documentation: http://localhost:$BACKEND_PORT/xiaozhi/doc.html"
    echo "Health Check: http://localhost:$BACKEND_PORT/xiaozhi/api/mobile/health"
    echo "Database: $DATABASE_HOST:$DATABASE_PORT/$DATABASE_NAME"
    echo
    echo -e "${BLUE}🔍 Mobile API Endpoints:${NC}"
    echo "• GET  /api/mobile/health - Health check"
    echo "• GET  /api/mobile/activation/check-code?code={code} - Check activation code"
    echo "• POST /api/mobile/activation/validate - Activate toy (requires auth)"
    echo "• GET  /api/mobile/profile - Get parent profile (requires auth)"
    echo "• POST /api/mobile/profile/create - Create parent profile (requires auth)"
    echo
    echo -e "${YELLOW}📝 Logs: tail -f main/backend.log${NC}"
    echo -e "${YELLOW}🛑 Stop: kill \$(cat main/backend.pid)${NC}"
}

# Main execution
main() {
    case "${1:-start}" in
        "start")
            test_database
            start_backend
            wait_for_service "http://localhost:$BACKEND_PORT/xiaozhi/api/mobile/health" "Spring Boot Backend"
            test_endpoints
            show_status
            ;;
        "status")
            show_status
            ;;
        "test")
            test_endpoints
            ;;
        "stop")
            if [ -f "main/backend.pid" ]; then
                PID=$(cat main/backend.pid)
                echo -e "${YELLOW}🛑 Stopping backend (PID: $PID)...${NC}"
                kill $PID 2>/dev/null || echo -e "${RED}❌ Process not found${NC}"
                rm -f main/backend.pid
                echo -e "${GREEN}✅ Backend stopped${NC}"
            else
                echo -e "${YELLOW}⚠️  No backend PID file found${NC}"
            fi
            ;;
        "logs")
            if [ -f "main/backend.log" ]; then
                tail -f main/backend.log
            else
                echo -e "${RED}❌ No log file found${NC}"
            fi
            ;;
        "restart")
            $0 stop
            sleep 3
            $0 start
            ;;
        *)
            echo "Usage: $0 {start|stop|restart|status|test|logs}"
            echo ""
            echo "Commands:"
            echo "  start   - Start the backend services"
            echo "  stop    - Stop the backend services"
            echo "  restart - Restart the backend services"
            echo "  status  - Show current status and endpoints"
            echo "  test    - Test API endpoints"
            echo "  logs    - Show backend logs"
            exit 1
            ;;
    esac
}

main "$@"