# Azure PostgreSQL Setup Guide

This guide explains how to configure the xiaozhi-esp32-server application to work with Azure PostgreSQL.

## Prerequisites

1. Azure PostgreSQL Flexible Server instance
2. Database created: `xiaozhi_esp32_server`
3. Firewall rules configured to allow your application's IP addresses
4. SSL certificate downloaded (if using SSL verification)

## Environment Variables

Set the following environment variables for Azure PostgreSQL connection:

### Required Variables

```bash
# Azure PostgreSQL Server Configuration
AZURE_POSTGRES_SERVER=your-server-name
AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server
AZURE_POSTGRES_USERNAME=your-username
AZURE_POSTGRES_PASSWORD=your-password

# Optional: Azure Redis Cache (if using)
AZURE_REDIS_HOST=your-redis-cache.redis.cache.windows.net
AZURE_REDIS_PORT=6380
AZURE_REDIS_PASSWORD=your-redis-password
AZURE_REDIS_SSL=true

# Optional: Knife4j Security
KNIFE4J_USERNAME=admin
KNIFE4J_PASSWORD=your-secure-password
```

### Example Production Values

```bash
# Example for a server named "xiaozhi-prod" in East Asia region
AZURE_POSTGRES_SERVER=xiaozhi-prod
AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server
AZURE_POSTGRES_USERNAME=xiaozhi_admin
AZURE_POSTGRES_PASSWORD=YourSecurePassword123!

# Example Azure Redis Cache
AZURE_REDIS_HOST=xiaozhi-prod.redis.cache.windows.net
AZURE_REDIS_PORT=6380
AZURE_REDIS_PASSWORD=YourRedisPassword123!
AZURE_REDIS_SSL=true
```

## Configuration Files

### Development Environment
Use `application-dev.yml` for local development with local PostgreSQL.

### Azure Production Environment
1. Copy `application-azure.yml` to `application-prod.yml`
2. Update the environment variables as shown above
3. Set Spring profile to `prod`: `SPRING_PROFILES_ACTIVE=prod`

## Azure PostgreSQL Connection URL Format

The connection URL format for Azure PostgreSQL is:
```
jdbc:postgresql://[server-name].postgres.database.azure.com:5432/[database-name]?sslmode=require
```

### SSL Configuration

Azure PostgreSQL requires SSL connections by default. The configuration includes:
- `sslmode=require` - Enforces SSL connection
- Connection timeout settings optimized for Azure
- Validation queries for connection health checks

## Database Migration

### Initial Setup
1. Create the database in Azure PostgreSQL:
   ```sql
   CREATE DATABASE xiaozhi_esp32_server;
   ```

2. Run Liquibase migrations:
   ```bash
   mvn liquibase:update
   ```

### Data Migration from MySQL
If migrating from existing MySQL data:
1. Export data from MySQL using the migration utilities (Task 7)
2. Import data to Azure PostgreSQL
3. Verify data integrity

## Connection Pool Settings

The configuration includes optimized connection pool settings for Azure:
- Initial connections: 5
- Maximum connections: 50
- Connection timeout: 30 seconds
- Validation query: `SELECT 1`

## Monitoring and Troubleshooting

### Connection Issues
1. Verify firewall rules in Azure PostgreSQL
2. Check SSL certificate configuration
3. Validate connection string format
4. Test connectivity using `psql` or Azure CLI

### Performance Monitoring
- Enable slow query logging (queries > 2 seconds)
- Monitor connection pool usage
- Use Azure PostgreSQL insights for performance analysis

### Common Issues

1. **SSL Connection Errors**
   - Ensure `sslmode=require` in connection URL
   - Verify Azure PostgreSQL SSL configuration

2. **Authentication Errors**
   - Username format: `username@servername`
   - Verify password complexity requirements

3. **Connection Timeouts**
   - Check Azure PostgreSQL firewall rules
   - Verify network connectivity
   - Adjust connection timeout settings

## Security Best Practices

1. Use Azure Key Vault for storing database passwords
2. Enable Azure AD authentication when possible
3. Configure network security groups appropriately
4. Regular security updates and patches
5. Monitor access logs and unusual activity

## Backup and Recovery

Azure PostgreSQL provides automated backups:
- Point-in-time recovery up to 35 days
- Geo-redundant backups available
- Manual backup export options

For application-level backups, use the migration utilities to export data periodically.