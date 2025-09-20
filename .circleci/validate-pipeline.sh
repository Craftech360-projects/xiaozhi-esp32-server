#!/bin/bash

# CircleCI Pipeline Validation Script
# This script validates the pipeline configuration and checks prerequisites

set -e

echo "🔍 CircleCI Pipeline Validation Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2

    case $status in
        "ok")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# Check if CircleCI CLI is installed
check_circleci_cli() {
    echo "Checking CircleCI CLI..."

    if command -v circleci >/dev/null 2>&1; then
        local version=$(circleci version)
        print_status "ok" "CircleCI CLI found: $version"
    else
        print_status "warning" "CircleCI CLI not found. Install with: curl -fLSs https://raw.githubusercontent.com/CircleCI-Public/circleci-cli/master/install.sh | bash"
    fi
}

# Validate CircleCI configuration files
validate_configs() {
    echo
    echo "Validating CircleCI configuration files..."

    # Check if config files exist
    if [ -f ".circleci/config.yml" ]; then
        print_status "ok" "Main config file found"

        if command -v circleci >/dev/null 2>&1; then
            if circleci config validate .circleci/config.yml >/dev/null 2>&1; then
                print_status "ok" "Main config validation passed"
            else
                print_status "error" "Main config validation failed"
                circleci config validate .circleci/config.yml
            fi
        fi
    else
        print_status "error" "Main config file (.circleci/config.yml) not found"
    fi

    if [ -f ".circleci/testing-config.yml" ]; then
        print_status "ok" "Testing config file found"

        if command -v circleci >/dev/null 2>&1; then
            if circleci config validate .circleci/testing-config.yml >/dev/null 2>&1; then
                print_status "ok" "Testing config validation passed"
            else
                print_status "error" "Testing config validation failed"
                circleci config validate .circleci/testing-config.yml
            fi
        fi
    else
        print_status "error" "Testing config file (.circleci/testing-config.yml) not found"
    fi
}

# Check service directories
check_service_directories() {
    echo
    echo "Checking service directories..."

    local services=("main/mqtt-gateway" "main/manager-api" "main/manager-web" "main/livekit-server")

    for service in "${services[@]}"; do
        if [ -d "$service" ]; then
            print_status "ok" "Service directory found: $service"

            # Check for specific files
            case $service in
                "main/mqtt-gateway")
                    if [ -f "$service/package.json" ] && [ -f "$service/app.js" ]; then
                        print_status "ok" "  Required files found (package.json, app.js)"
                    else
                        print_status "warning" "  Missing required files (package.json or app.js)"
                    fi
                    ;;
                "main/manager-api")
                    if [ -f "$service/pom.xml" ]; then
                        print_status "ok" "  Required files found (pom.xml)"
                    else
                        print_status "warning" "  Missing required files (pom.xml)"
                    fi
                    ;;
                "main/manager-web")
                    if [ -f "$service/package.json" ]; then
                        print_status "ok" "  Required files found (package.json)"
                    else
                        print_status "warning" "  Missing required files (package.json)"
                    fi
                    ;;
                "main/livekit-server")
                    if [ -f "$service/requirements.txt" ] || [ -f "$service/main.py" ]; then
                        print_status "ok" "  Required files found"
                    else
                        print_status "warning" "  Missing required files (requirements.txt or main.py)"
                    fi
                    ;;
            esac
        else
            print_status "error" "Service directory missing: $service"
        fi
    done
}

# Check environment variables (if running in CircleCI context)
check_environment_variables() {
    echo
    echo "Checking environment variables..."

    local required_vars=("AZURE_HOST" "AZURE_USER" "AZURE_DEPLOY_PATH")
    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -n "${!var}" ]; then
            print_status "ok" "$var is set"
        else
            print_status "warning" "$var is not set (required for Azure deployment)"
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo
        echo "Missing environment variables. Set them in CircleCI context 'azure-mqtt-gateway':"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
    fi
}

# Check dependencies
check_dependencies() {
    echo
    echo "Checking build dependencies..."

    # Node.js
    if command -v node >/dev/null 2>&1; then
        local node_version=$(node --version)
        print_status "ok" "Node.js found: $node_version"
    else
        print_status "warning" "Node.js not found (required for Node.js and Vue.js services)"
    fi

    # npm
    if command -v npm >/dev/null 2>&1; then
        local npm_version=$(npm --version)
        print_status "ok" "npm found: $npm_version"
    else
        print_status "warning" "npm not found"
    fi

    # Maven
    if command -v mvn >/dev/null 2>&1; then
        local mvn_version=$(mvn --version | head -1)
        print_status "ok" "Maven found: $mvn_version"
    else
        print_status "warning" "Maven not found (required for Java service)"
    fi

    # Python
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version)
        print_status "ok" "Python found: $python_version"
    else
        print_status "warning" "Python3 not found (required for Python service)"
    fi

    # pip
    if command -v pip3 >/dev/null 2>&1; then
        local pip_version=$(pip3 --version)
        print_status "ok" "pip3 found: $pip_version"
    else
        print_status "warning" "pip3 not found"
    fi
}

# Test basic pipeline functionality
test_basic_functionality() {
    echo
    echo "Testing basic functionality..."

    # Test Node.js service if present
    if [ -d "main/mqtt-gateway" ] && [ -f "main/mqtt-gateway/package.json" ]; then
        echo "Testing MQTT Gateway..."
        cd main/mqtt-gateway
        if npm list >/dev/null 2>&1; then
            print_status "ok" "  Dependencies are installed"
        else
            print_status "warning" "  Dependencies not installed (run 'npm install')"
        fi

        if [ -f "app.js" ]; then
            if node --check app.js >/dev/null 2>&1; then
                print_status "ok" "  Syntax check passed"
            else
                print_status "error" "  Syntax check failed"
            fi
        fi
        cd ../..
    fi

    # Test Java service if present
    if [ -d "main/manager-api" ] && [ -f "main/manager-api/pom.xml" ]; then
        echo "Testing Manager API..."
        cd main/manager-api
        if mvn validate >/dev/null 2>&1; then
            print_status "ok" "  Maven configuration is valid"
        else
            print_status "warning" "  Maven validation failed"
        fi
        cd ../..
    fi

    # Test Vue.js service if present
    if [ -d "main/manager-web" ] && [ -f "main/manager-web/package.json" ]; then
        echo "Testing Manager Web..."
        cd main/manager-web
        if npm list >/dev/null 2>&1; then
            print_status "ok" "  Dependencies are installed"
        else
            print_status "warning" "  Dependencies not installed (run 'npm install')"
        fi
        cd ../..
    fi

    # Test Python service if present
    if [ -d "main/livekit-server" ]; then
        echo "Testing LiveKit Server..."
        cd main/livekit-server

        if [ -f "requirements.txt" ]; then
            print_status "ok" "  Requirements file found"
        fi

        if [ -f "main.py" ]; then
            if python3 -m py_compile main.py >/dev/null 2>&1; then
                print_status "ok" "  Syntax check passed"
            else
                print_status "error" "  Syntax check failed"
            fi
        fi
        cd ../..
    fi
}

# Generate summary report
generate_summary() {
    echo
    echo "🏁 Validation Summary"
    echo "===================="
    echo
    echo "Next steps:"
    echo "1. Fix any errors shown above"
    echo "2. Install missing dependencies"
    echo "3. Set required environment variables in CircleCI"
    echo "4. Test pipeline with a sample commit"
    echo
    echo "Pipeline files:"
    echo "  - Production: .circleci/config.yml (dev branch)"
    echo "  - Testing: .circleci/testing-config.yml (all branches)"
    echo "  - Documentation: .circleci/README.md"
    echo
    echo "For more information, see .circleci/README.md"
}

# Main execution
main() {
    # Change to repository root
    if [ -f ".circleci/config.yml" ] || [ -f ".circleci/testing-config.yml" ]; then
        echo "Running from repository root"
    elif [ -f "../.circleci/config.yml" ]; then
        cd ..
        echo "Changed to repository root"
    else
        print_status "error" "Cannot find .circleci directory. Run this script from the repository root."
        exit 1
    fi

    check_circleci_cli
    validate_configs
    check_service_directories
    check_environment_variables
    check_dependencies
    test_basic_functionality
    generate_summary
}

# Run the validation
main "$@"