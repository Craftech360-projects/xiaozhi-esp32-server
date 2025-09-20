# CircleCI Pipeline Documentation

This repository contains two comprehensive CI/CD pipelines for the Xiaozhi ESP32 Server project with **clear dashboard identification**:

1. **🚀 Production Pipeline** (`config.yml`) - Production deployment pipeline for `dev` branch
2. **🧪 Testing Pipeline** (`testing-config.yml`) - Comprehensive testing pipeline for all branches

## 📊 Pipeline Overview & Dashboard Identification

### 🚀 Production Pipeline (config.yml)
- **Dashboard ID**: `[PROD]` prefix on all jobs
- **Workflow Name**: `prod-pipeline-xiaozhi-deployment`
- **Trigger**: Only `dev` branch
- **Purpose**: Production deployment to Azure with PM2
- **Services**: MQTT Gateway, Manager API, Manager Web, LiveKit Server
- **Environment**: Uses `azure-mqtt-gateway` context
- **First Job**: `[PROD] 🚀 Pipeline Type Notification`

### 🧪 Testing Pipeline (testing-config.yml)
- **Dashboard ID**: `[TEST]` prefix on all jobs
- **Workflow Name**: `test-pipeline-xiaozhi-qa`
- **Trigger**: ALL branches (including feature branches)
- **Purpose**: Comprehensive testing, quality gates, and test environment deployment
- **Features**: Code quality analysis, redundancy detection, security scanning, performance testing
- **First Job**: `[TEST] 🧪 Pipeline Type Notification`

## 🎯 Quick Recognition in CircleCI Dashboard

You'll immediately know which pipeline is running by looking at:
- **Workflow Names**: `prod-pipeline-*` vs `test-pipeline-*`
- **Job Prefixes**: `[PROD]` vs `[TEST]`
- **Pipeline Notifications**: First job shows detailed pipeline metadata
- **Visual Emojis**: 🚀 for production, 🧪 for testing

## Setup Instructions

### 1. CircleCI Configuration

### **✅ IMPORTANT: Pipeline Functionality Verified**
All job dependencies have been updated to work with the new dashboard naming. Both pipelines are fully functional and ready for deployment.

#### Option A: Use Testing Pipeline as Primary
Activate comprehensive testing for all branches:
```bash
mv .circleci/config.yml .circleci/production-config.yml
mv .circleci/testing-config.yml .circleci/config.yml
```

#### Option B: Use Both Pipelines (Recommended)
Set up both pipelines using CircleCI's dynamic configuration:

1. Create a main config that chooses which pipeline to run:
```yaml
# .circleci/config.yml
version: 2.1

setup: true

orbs:
  continuation: circleci/continuation@0.3.1

workflows:
  setup:
    jobs:
      - continuation/continue:
          configuration_path: |
            if [ "$CIRCLE_BRANCH" = "dev" ]; then
              echo ".circleci/production-config.yml"
            else
              echo ".circleci/testing-config.yml"
            fi
```

2. Rename current files:
```bash
mv .circleci/config.yml .circleci/production-config.yml
mv .circleci/testing-config.yml .circleci/config.yml
```

### 2. Environment Variables

Set up the following environment variables in CircleCI context `azure-mqtt-gateway`:

#### Required Variables:
- `AZURE_HOST` - Azure VM hostname/IP
- `AZURE_USER` - SSH username for Azure VM
- `AZURE_DEPLOY_PATH` - Base deployment path (e.g., `/home/xiaozhi/deploy`)

#### Optional Variables:
- `MYSQL_ROOT_PASSWORD` - MySQL root password (default: `rootpassword123`)
- `MYSQL_DATABASE` - Database name (default: `xiaozhi_db`)
- `MYSQL_USER` - Database user (default: `xiaozhi_user`)
- `MYSQL_PASSWORD` - Database password (default: `xiaozhi_password123`)

### 3. SSH Key Setup

1. Generate SSH key pair for Azure VM access:
```bash
ssh-keygen -t rsa -b 4096 -C "circleci@xiaozhi-deployment"
```

2. Add public key to Azure VM:
```bash
ssh-copy-id -i ~/.ssh/id_rsa.pub user@azure-vm-host
```

3. Add private key to CircleCI project settings:
   - Go to Project Settings → SSH Keys
   - Add the private key
   - Note the fingerprint (update in config files)

## Pipeline Features

### Testing Pipeline Features

#### 🔍 Code Quality Gates
- **JavaScript/Node.js**: ESLint, JSHint analysis
- **Python**: Flake8, Pylint, Bandit security scanning
- **Java**: SpotBugs, Checkstyle, PMD analysis
- **Security**: OWASP dependency check, Safety scanning

#### 🔄 Code Redundancy Detection
- **JavaScript**: jscpd for duplicate code detection
- **Python**: Vulture for dead code detection, Radon for complexity analysis
- **Duplicate threshold**: 10+ lines, 50+ tokens

#### 🧪 Comprehensive Testing
- **Unit Tests**: Service-specific test suites
- **Integration Tests**: API, MQTT, Frontend-Backend communication
- **Performance Tests**: Load testing, memory analysis, CPU profiling
- **Security Tests**: Vulnerability scanning, dependency analysis

#### 📊 Test Coverage & Reporting
- **Coverage Reports**: HTML and XML formats
- **Artifacts Storage**: Test results, coverage reports, security reports
- **Performance Metrics**: Response times, memory usage, CPU efficiency

#### 🚀 Test Environment Deployment
- **Isolated Environments**: Branch-specific test deployments
- **Port Management**: Unique ports per test environment
- **Cleanup**: Automatic environment cleanup (configure separately)

### Production Pipeline Features

#### 🏗️ Service Building
- **Node.js Services**: Production dependency installation
- **Java Services**: Maven compilation and packaging
- **Vue.js Frontend**: Production build with optimization
- **Python Services**: Virtual environment and dependency setup

#### 🔒 Security Scanning
- **Bundle Scanning**: Trivy vulnerability scanning
- **JAR Scanning**: Java-specific security analysis
- **Dependency Scanning**: npm audit, safety, OWASP checks

#### 🚀 PM2 Deployment
- **Process Management**: PM2 ecosystem configuration
- **Health Checks**: Comprehensive service health verification
- **Blue-Green Support**: Zero-downtime deployment capability
- **Log Management**: Centralized logging with PM2

## Service Architecture

### Services Overview
1. **MQTT Gateway** (Node.js) - MQTT message handling
2. **Manager API** (Java/Spring Boot) - REST API backend
3. **Manager Web** (Vue.js) - Frontend application
4. **LiveKit Server** (Python) - Real-time communication

### Port Configuration

#### Production Environment
- MQTT Gateway: HTTP 8884, MQTT 1883
- Manager API: 8002
- Manager Web: 8885
- LiveKit Server: 8887, 7880

#### Test Environment (Dynamic)
- MQTT Gateway: 18840
- Manager API: 18020
- Manager Web: 18850
- LiveKit Server: 18870

## Usage Examples

### Running Tests Locally
```bash
# Run JavaScript tests
cd main/mqtt-gateway
npm test

# Run Java tests
cd main/manager-api
mvn test

# Run Python tests
cd main/livekit-server
python -m pytest tests/

# Run Vue.js tests
cd main/manager-web
npm run test:unit
```

### Manual Deployment Commands
```bash
# Deploy specific service
circleci local execute --job deploy_java_pm2_azure

# Run quality checks
circleci local execute --job code_quality_check

# Run performance tests
circleci local execute --job performance_test_services
```

### Monitoring and Debugging

#### Service Health Checks
```bash
# Check PM2 processes
pm2 status

# View service logs
pm2 logs mqtt-gateway
pm2 logs manager-api
pm2 logs manager-web
pm2 logs livekit-server

# Check service endpoints
curl http://localhost:8002/toy/doc.html  # Manager API
curl http://localhost:8885/             # Manager Web
curl http://localhost:7880/             # LiveKit Server
```

#### Performance Monitoring
```bash
# PM2 monitoring
pm2 monit

# System resources
htop
free -h
df -h
```

## Troubleshooting

### Common Issues

#### 1. SSH Connection Failures
```bash
# Test SSH connection
ssh -o StrictHostKeyChecking=no user@azure-host

# Check SSH key fingerprint
ssh-keygen -l -f ~/.ssh/id_rsa
```

#### 2. Service Start Failures
```bash
# Check PM2 logs
pm2 logs --lines 50

# Restart service
pm2 restart service-name

# Check port conflicts
netstat -tuln | grep :8002
```

#### 3. Test Failures
- Check test artifacts in CircleCI
- Review coverage reports
- Examine security scan results

#### 4. Performance Issues
- Review performance test reports
- Check memory usage patterns
- Analyze load test results

### Configuration Validation

#### Validate CircleCI Config
```bash
# Install CircleCI CLI
circleci config validate .circleci/config.yml
circleci config validate .circleci/testing-config.yml
```

#### Test Environment Variables
```bash
# Check required variables
echo $AZURE_HOST
echo $AZURE_USER
echo $AZURE_DEPLOY_PATH
```

## Best Practices

### 1. Branch Strategy
- Use feature branches for development
- Merge to `dev` for production deployment
- Testing pipeline runs on all branches

### 2. Test Writing
- Maintain test coverage above 80%
- Write integration tests for API endpoints
- Include performance benchmarks

### 3. Security
- Regular dependency updates
- Security scan reviews
- Credential rotation

### 4. Performance
- Monitor service startup times
- Track memory usage patterns
- Set performance budgets

## Support

For issues or questions:
1. Check CircleCI job logs
2. Review test artifacts and reports
3. Examine service health checks
4. Contact DevOps team

---

## ✅ Pipeline Functionality Status

### **Verified & Ready for Production**
Both pipelines have been thoroughly tested and verified:

- ✅ **YAML Syntax**: Both configurations validated
- ✅ **Job Dependencies**: All `requires` references updated to new display names
- ✅ **Workflow Logic**: Dependency chains preserved and functional
- ✅ **Build Order**: Services still build in parallel as before
- ✅ **Environment Variables**: Same Azure context (`azure-mqtt-gateway`) used
- ✅ **PM2 Deployment**: All deployment logic unchanged
- ✅ **Branch Filters**: Production pipeline still dev-branch only
- ✅ **Dashboard Clarity**: Clear visual identification with `[PROD]` and `[TEST]` prefixes

### **Files Ready for Deployment**
- `config.yml` - Production pipeline (dev branch only)
- `testing-config.yml` - Testing pipeline (all branches)
- `PIPELINE-GUIDE.md` - Dashboard identification guide
- `PIPELINE-FIXES.md` - Technical details of functionality preservation
- `validate-pipeline.sh` - Validation script

**🚀 Both pipelines are fully functional and maintain all existing capabilities while providing clear dashboard identification!**

---

**Note**: This pipeline setup provides comprehensive testing and robust deployment capabilities. Customize thresholds and checks based on your specific requirements.