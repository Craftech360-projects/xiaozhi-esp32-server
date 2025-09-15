# Deployment Scripts

This directory contains scripts for building, deploying, and managing the Xiaozhi ESP32 Server services using PM2.

## Scripts Overview

### 1. `build-all.sh`
Builds all project components (Manager API, Manager Web, MQTT Gateway).

**Usage:**
```bash
./scripts/build-all.sh [OPTIONS]

Options:
  -s, --service SERVICE    Build specific service (api|web|gateway|all) [default: all]
  -t, --tests             Run tests during build
  -c, --clean             Clean before building
  -h, --help              Show help message
```

**Examples:**
```bash
# Build all services
./scripts/build-all.sh

# Build only Manager API with tests
./scripts/build-all.sh -s api -t

# Clean build of Manager Web
./scripts/build-all.sh -s web -c
```

### 2. `deploy.sh`
Deploys the built applications to the target environment using PM2.

**Usage:**
```bash
./scripts/deploy.sh [OPTIONS]

Options:
  -e, --env ENV            Environment (dev|staging|production) [default: staging]
  -p, --path PATH          Deployment path [default: /opt/xiaozhi-esp32-server]
  -h, --help              Show help message
```

**Examples:**
```bash
# Deploy to staging
./scripts/deploy.sh -e staging

# Deploy to production
./scripts/deploy.sh -e production

# Deploy to custom path
./scripts/deploy.sh -p /custom/deployment/path
```

### 3. `manage-services.sh`
Manages PM2 services after deployment.

**Usage:**
```bash
./scripts/manage-services.sh <command> [service_name]

Commands:
  start [service]         Start all services or a specific service
  stop [service]          Stop all services or a specific service
  restart [service]       Restart all services or a specific service
  status                  Show status of all services
  logs [service]          Show logs for all services or a specific service
  monitor                 Monitor services in real-time
  reload [service]        Reload all services or a specific service
  delete [service]        Delete all services or a specific service
  list                    List all PM2 processes
```

**Examples:**
```bash
# Start all services
./scripts/manage-services.sh start

# Restart only MQTT Gateway
./scripts/manage-services.sh restart mqtt-gateway

# View logs for Manager API
./scripts/manage-services.sh logs manager-api

# Show status of all services
./scripts/manage-services.sh status
```

## Services

The project consists of three main services:

1. **manager-api** - Java Spring Boot API server
2. **manager-web** - Vue.js frontend application
3. **mqtt-gateway** - Node.js MQTT gateway service

## Prerequisites

Before using these scripts, ensure you have the following installed:

- **Node.js 18+** and **npm**
- **Java 17+** and **Maven** (for Manager API)
- **PM2** (`npm install -g pm2`)
- **serve** (`npm install -g serve`) (for serving static web files)

## Deployment Workflow

1. **Build** all services:
   ```bash
   ./scripts/build-all.sh
   ```

2. **Deploy** to your target environment:
   ```bash
   ./scripts/deploy.sh -e staging
   ```

3. **Manage** services as needed:
   ```bash
   ./scripts/manage-services.sh status
   ./scripts/manage-services.sh logs
   ```

## Environment Configuration

The deployment supports three environments:

- **dev** - Development environment
- **staging** - Staging environment
- **production** - Production environment

Each environment uses different configuration settings defined in the `ecosystem.config.js` file.

## CircleCI Integration

The project includes CircleCI configuration for automated building and deployment. The pipeline:

1. Builds all three services in parallel
2. Runs security scans on build artifacts
3. Deploys to staging (develop branch) or production (main branch with approval)

## Directory Structure

After deployment, the directory structure will be:

```
/opt/xiaozhi-esp32-server/
├── ecosystem.config.js           # PM2 configuration
├── main/
│   ├── manager-api/
│   │   └── target/
│   │       └── xiaozhi-esp32-api.jar
│   ├── manager-web/
│   │   └── dist/                 # Built Vue.js app
│   └── mqtt-gateway/
│       ├── app.js               # Main Node.js application
│       ├── package.json
│       └── node_modules/
└── logs/                        # PM2 logs
```

## Troubleshooting

### Common Issues

1. **Permission denied errors:**
   ```bash
   sudo chown -R $USER:$USER /opt/xiaozhi-esp32-server
   sudo chown -R $USER:$USER /var/log/pm2
   ```

2. **PM2 not found:**
   ```bash
   npm install -g pm2
   ```

3. **Java not found:**
   - Install Java 17 or higher
   - Ensure `JAVA_HOME` is set properly

4. **Build failures:**
   - Clean build: `./scripts/build-all.sh -c`
   - Check prerequisites: `./scripts/build-all.sh -h`

### Logs and Monitoring

- View all service logs: `./scripts/manage-services.sh logs`
- Monitor services: `./scripts/manage-services.sh monitor`
- Check service status: `./scripts/manage-services.sh status`

PM2 logs are stored in `/var/log/pm2/` with separate files for each service.

## Environment Variables

Set the following environment variables in your CircleCI contexts:

### Staging Context (`staging-deploy`)
- `STAGING_SERVER_HOST` - Staging server hostname
- `STAGING_SERVER_USER` - Staging server username

### Production Context (`production-deploy`)
- `PROD_SERVER_HOST` - Production server hostname
- `PROD_SERVER_USER` - Production server username

## Security

- Build artifacts are scanned for vulnerabilities using Trivy
- Services run with non-root users where possible
- SSH keys are used for secure deployment
- Environment-specific configurations isolate sensitive data