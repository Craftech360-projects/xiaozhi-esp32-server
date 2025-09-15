# XiaoZhi ESP32 Server - PM2 Deployment Guide

This guide covers the CircleCI and PM2-based deployment pipeline for the XiaoZhi ESP32 Server project.

## Architecture Overview

The deployment pipeline builds and deploys three services:

1. **Manager API** - Java Spring Boot REST API (Port: 8080)
2. **Manager Web** - Vue.js frontend application (Port: 8081)
3. **MQTT Gateway** - Node.js MQTT message broker service (Port: 8884)

## Deployment Process Flow

### 1. Build Phase (Parallel)
- **Manager API**: Maven build → JAR packaging
- **Manager Web**: npm install → Vue.js build → dist folder
- **MQTT Gateway**: npm install → Node.js app preparation

### 2. Security Scanning
- Trivy vulnerability scanning on all build artifacts
- Scans for HIGH and CRITICAL vulnerabilities
- Fails deployment if critical issues found

### 3. Deployment Phase
- Automatic backup creation before deployment
- Graceful PM2 process shutdown
- Artifact deployment to target server
- Service startup with environment-specific configurations
- Health checks for all services
- Rollback on failure

## Environment Configurations

### Development Environment
```bash
NODE_ENV=development
SPRING_PROFILES_ACTIVE=dev
MQTT_PORT=1883
HTTP_PORT=8884
```

### Staging Environment
```bash
NODE_ENV=staging
SPRING_PROFILES_ACTIVE=staging
MQTT_PORT=1883
HTTP_PORT=8884
```

### Production Environment
```bash
NODE_ENV=production
SPRING_PROFILES_ACTIVE=prod
MQTT_PORT=1883
HTTP_PORT=8884
JAVA_OPTS=-Xms1g -Xmx2g
```

## Setup Requirements

### 1. CircleCI Configuration

#### Required Contexts:

**`staging-deploy` Context:**
```
STAGING_SERVER_HOST=your-staging-server.com
STAGING_SERVER_USER=deploy
```

**`production-deploy` Context:**
```
PROD_SERVER_HOST=your-production-server.com
PROD_SERVER_USER=deploy
```

#### SSH Key Setup:
1. Generate SSH key pair for deployment
2. Add public key to target servers' `authorized_keys`
3. Add private key fingerprint to CircleCI project SSH keys
4. Update fingerprint in `.circleci/config.yml`

### 2. Server Prerequisites

#### Target Server Requirements:
- Ubuntu 18.04+ or CentOS 7+
- Node.js 18.20+
- Java 17+
- PM2 installed globally
- `serve` package for static hosting

#### Directory Structure:
```
/opt/xiaozhi-esp32-server/
├── main/
│   ├── manager-api/
│   │   └── target/
│   ├── manager-web/
│   │   └── dist/
│   └── mqtt-gateway/
└── ecosystem.config.js
```

#### Log Directory:
```
/var/log/pm2/
├── manager-api-error.log
├── manager-api-out.log
├── manager-web-error.log
├── manager-web-out.log
├── mqtt-gateway-error.log
└── mqtt-gateway-out.log
```

### 3. Local Development

Each service has its own ecosystem config for local development:

#### Start Individual Services:
```bash
# Manager API
cd main/manager-api
pm2 start ecosystem.config.js

# Manager Web
cd main/manager-web
pm2 start ecosystem.config.js

# MQTT Gateway
cd main/mqtt-gateway
pm2 start ecosystem.config.js
```

#### Start All Services:
```bash
# From project root
pm2 start ecosystem.config.js
```

## Health Checks

The deployment includes comprehensive health checks:

### Manager API Health Check
- Endpoint: `http://localhost:8080/actuator/health`
- Timeout: 60 seconds (30 attempts × 2s)

### Manager Web Health Check
- Endpoint: `http://localhost:8081/`
- Timeout: 30 seconds (15 attempts × 2s)

### MQTT Gateway Health Check
- Endpoint: `http://localhost:8884/health`
- Timeout: 30 seconds (15 attempts × 2s)

## Deployment Commands

### Manual Deployment Trigger
```bash
# Staging deployment (automatic on develop branch)
# Push to develop branch

# Production deployment (requires approval)
# 1. Push to main branch
# 2. Approve deployment in CircleCI UI
```

### Rollback Deployment
```bash
# Emergency rollback via CircleCI API
curl -X POST \
  -H "Circle-Token: YOUR_TOKEN" \
  https://circleci.com/api/v2/project/gh/YOUR_ORG/YOUR_REPO/pipeline \
  -d '{"parameters":{"run_rollback":true,"target_env":"production"}}'
```

## Monitoring and Maintenance

### PM2 Process Management
```bash
# Check service status
pm2 list

# View logs
pm2 logs
pm2 logs manager-api
pm2 logs manager-web
pm2 logs mqtt-gateway

# Restart services
pm2 restart ecosystem.config.js

# Stop services
pm2 stop ecosystem.config.js

# Delete processes
pm2 delete ecosystem.config.js
```

### Log Monitoring
```bash
# Real-time log monitoring
tail -f /var/log/pm2/manager-api-combined.log
tail -f /var/log/pm2/manager-web-combined.log
tail -f /var/log/pm2/mqtt-gateway-combined.log
```

### Backup Management
```bash
# List available backups
ls -la /opt/xiaozhi-esp32-server-backup-*

# Manual backup creation
BACKUP_DIR="/opt/xiaozhi-esp32-server-backup-$(date +%Y%m%d-%H%M%S)"
sudo cp -r /opt/xiaozhi-esp32-server $BACKUP_DIR
```

## Troubleshooting

### Common Issues

#### 1. Build Failures
- **Manager API**: Check Maven dependencies in `pom.xml`
- **Manager Web**: Verify Node.js version and package-lock.json
- **MQTT Gateway**: Check app.js exists and dependencies

#### 2. Deployment Failures
- Verify SSH access to target server
- Check PM2 is installed on target server
- Verify directory permissions
- Check available disk space

#### 3. Health Check Failures
- Verify services are actually running: `pm2 list`
- Check service logs: `pm2 logs [service-name]`
- Verify ports are not in use by other processes
- Check firewall settings

#### 4. Performance Issues
- Monitor memory usage: `pm2 monit`
- Adjust max_memory_restart values in ecosystem.config.js
- Check Java heap settings for manager-api

### Emergency Procedures

#### Service Recovery
```bash
# Stop all services
pm2 stop ecosystem.config.js

# Clear PM2 processes
pm2 delete ecosystem.config.js

# Restart from clean state
pm2 start ecosystem.config.js --env production

# Save configuration
pm2 save
```

#### Complete Rollback
```bash
# Find latest backup
BACKUP_DIR=$(ls -td /opt/xiaozhi-esp32-server-backup-* | head -1)

# Stop current services
pm2 stop ecosystem.config.js

# Restore from backup
sudo rm -rf /opt/xiaozhi-esp32-server
sudo cp -r $BACKUP_DIR /opt/xiaozhi-esp32-server
sudo chown -R $USER:$USER /opt/xiaozhi-esp32-server

# Start restored services
cd /opt/xiaozhi-esp32-server
pm2 start ecosystem.config.js --env production
pm2 save
```

## Security Considerations

### Access Control
- SSH key-based authentication only
- Separate deployment users for staging/production
- Limited sudo permissions for deployment user

### Network Security
- Firewall rules restricting access to service ports
- VPN or private network for server access
- SSL/TLS termination at load balancer level

### Secret Management
- Environment variables for sensitive configuration
- No hardcoded credentials in code
- Regular rotation of deployment keys

## Performance Optimization

### PM2 Configuration
- Set appropriate memory limits per service
- Use cluster mode for CPU-intensive services
- Configure log rotation to prevent disk issues

### Build Optimization
- Maven dependency caching
- Node.js module caching
- Parallel build execution

### Deployment Optimization
- Incremental deployments when possible
- Artifact compression for faster transfers
- Health check timeouts tuned per service

## Support and Maintenance

### Regular Maintenance Tasks
- Weekly backup cleanup (keep last 10 backups)
- Monthly security patch updates
- Quarterly performance review and optimization

### Support Contacts
- DevOps Team: devops@xiaozhi.com
- CircleCI Issues: Check build logs first
- PM2 Issues: Verify process status and logs
- Server Issues: Check system resources and connectivity