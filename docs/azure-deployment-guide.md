# Azure Deployment Guide for xiaozhi-esp32-server

This guide provides complete instructions for deploying xiaozhi-esp32-server on Azure with PostgreSQL.

## Prerequisites

- Azure CLI installed and configured
- Docker and Docker Compose installed
- Azure subscription with appropriate permissions

## Step 1: Azure PostgreSQL Setup

### Automated Setup (Recommended)
```bash
# Run the automated setup script
./scripts/setup-azure-postgresql.sh
```

### Manual Setup
```bash
# Login to Azure
az login

# Create resource group
az group create --name xiaozhi-rg --location "East Asia"

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group xiaozhi-rg \
  --name xiaozhi-postgres-server \
  --location "East Asia" \
  --admin-user xiaozhi_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0

# Create database
az postgres flexible-server db create \
  --resource-group xiaozhi-rg \
  --server-name xiaozhi-postgres-server \
  --database-name xiaozhi_esp32_server
```

## Step 2: Configure Environment Variables

Create a `.env` file in your project root:

```bash
# Azure PostgreSQL Configuration
AZURE_POSTGRES_SERVER=xiaozhi-postgres-server
AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server
AZURE_POSTGRES_USERNAME=xiaozhi_admin
AZURE_POSTGRES_PASSWORD=YourSecurePassword123!

# Optional: Azure Redis Cache
AZURE_REDIS_HOST=your-redis-cache.redis.cache.windows.net
AZURE_REDIS_PORT=6380
AZURE_REDIS_PASSWORD=your-redis-password
AZURE_REDIS_SSL=true
```

## Step 3: Deploy Application

### Option A: Docker Compose (Recommended)
```bash
# Load environment variables
source .env

# Deploy all services
docker-compose -f main/xiaozhi-server/docker-compose_all.yml up -d

# Monitor deployment
docker-compose -f main/xiaozhi-server/docker-compose_all.yml logs -f
```

### Option B: Azure Container Instances
```bash
# Create container group
az container create \
  --resource-group xiaozhi-rg \
  --name xiaozhi-app \
  --image ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:web_latest \
  --ports 8002 \
  --environment-variables \
    AZURE_POSTGRES_SERVER=xiaozhi-postgres-server \
    AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server \
    AZURE_POSTGRES_USERNAME=xiaozhi_admin \
    AZURE_POSTGRES_PASSWORD=YourSecurePassword123! \
    SPRING_PROFILES_ACTIVE=azure
```

## Step 4: Database Migration

### From Existing MySQL Data
```bash
# Export MySQL data
curl -X POST "http://localhost:8002/xiaozhi/migration/export-mysql" \
  -d "host=your-mysql-host&database=xiaozhi_esp32_server&username=root&password=your-password"

# Import to Azure PostgreSQL
curl -X POST "http://localhost:8002/xiaozhi/migration/import-postgresql" \
  -d "host=xiaozhi-postgres-server.postgres.database.azure.com&database=xiaozhi_esp32_server&username=xiaozhi_admin@xiaozhi-postgres-server&password=YourSecurePassword123!&inputDir=/path/to/export"
```

### Fresh Installation
The application will automatically create the database schema on first startup using Liquibase migrations.

## Step 5: Verification

### Health Check
```bash
# Test application health
curl -X GET "http://your-app-url:8002/xiaozhi/config/getConfig"

# Test database connection
curl -X POST "http://your-app-url:8002/xiaozhi/migration/validate"
```

### Database Verification
```bash
# Connect to Azure PostgreSQL
psql -h xiaozhi-postgres-server.postgres.database.azure.com \
     -U xiaozhi_admin@xiaozhi-postgres-server \
     -d xiaozhi_esp32_server

# Check tables
\dt

# Verify data
SELECT COUNT(*) FROM sys_user;
SELECT COUNT(*) FROM ai_model_config;
```

## Step 6: Production Optimization

### PostgreSQL Configuration
```bash
# Optimize for production workload
az postgres flexible-server parameter set \
  --resource-group xiaozhi-rg \
  --server-name xiaozhi-postgres-server \
  --name shared_buffers \
  --value "256MB"

az postgres flexible-server parameter set \
  --resource-group xiaozhi-rg \
  --server-name xiaozhi-postgres-server \
  --name effective_cache_size \
  --value "1GB"
```

### Monitoring Setup
```bash
# Enable query store
az postgres flexible-server parameter set \
  --resource-group xiaozhi-rg \
  --server-name xiaozhi-postgres-server \
  --name pg_qs.query_capture_mode \
  --value "ALL"
```

## Security Configuration

### Network Security
```bash
# Configure firewall rules
az postgres flexible-server firewall-rule create \
  --resource-group xiaozhi-rg \
  --name xiaozhi-postgres-server \
  --rule-name "AllowApplicationSubnet" \
  --start-ip-address 10.0.1.0 \
  --end-ip-address 10.0.1.255
```

### SSL Configuration
The application is configured to use SSL by default with `sslmode=require`. Ensure your Azure PostgreSQL server has SSL enabled.

## Backup and Recovery

### Automated Backups
Azure PostgreSQL Flexible Server provides automated backups with point-in-time recovery up to 35 days.

### Manual Backup
```bash
# Create manual backup
pg_dump -h xiaozhi-postgres-server.postgres.database.azure.com \
        -U xiaozhi_admin@xiaozhi-postgres-server \
        -d xiaozhi_esp32_server \
        --no-password > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check firewall rules
   - Verify network connectivity
   - Ensure SSL configuration

2. **Authentication Failed**
   - Verify username format: `username@servername`
   - Check password complexity requirements
   - Ensure user has necessary permissions

3. **Migration Errors**
   - Check Liquibase logs
   - Verify PostgreSQL version compatibility
   - Ensure database exists and is accessible

### Monitoring Commands
```bash
# Check application logs
docker-compose -f main/xiaozhi-server/docker-compose_all.yml logs xiaozhi-esp32-server-web

# Monitor PostgreSQL performance
az postgres flexible-server show \
  --resource-group xiaozhi-rg \
  --name xiaozhi-postgres-server
```

## Cost Optimization

### Right-sizing
- Start with `Standard_B1ms` for development
- Scale to `Standard_D2s_v3` for production
- Use `Burstable` tier for variable workloads

### Storage Optimization
- Start with 32GB storage
- Enable auto-grow for production
- Monitor storage usage regularly

## Support and Maintenance

### Regular Tasks
- Monitor database performance metrics
- Review and optimize slow queries
- Update firewall rules as needed
- Test backup and restore procedures

### Scaling
```bash
# Scale up server
az postgres flexible-server update \
  --resource-group xiaozhi-rg \
  --name xiaozhi-postgres-server \
  --sku-name Standard_D2s_v3

# Scale storage
az postgres flexible-server update \
  --resource-group xiaozhi-rg \
  --name xiaozhi-postgres-server \
  --storage-size 64
```

This completes the Azure deployment setup for xiaozhi-esp32-server with full PostgreSQL integration.