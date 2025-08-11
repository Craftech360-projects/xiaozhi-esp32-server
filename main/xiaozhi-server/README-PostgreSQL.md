# Azure PostgreSQL Deployment Setup

This guide explains how to run the xiaozhi-esp32-server with Azure PostgreSQL.

## Quick Start

### Azure PostgreSQL Setup (Required)

The application now exclusively uses Azure PostgreSQL. Set up your Azure PostgreSQL server first:

```bash
# Run the automated Azure setup script
./scripts/setup-azure-postgresql.sh
```

### Deploy Application

Use the Docker Compose files with Azure PostgreSQL environment variables:

```bash
# Set environment variables for Azure PostgreSQL
export AZURE_POSTGRES_SERVER=your-server-name
export AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server
export AZURE_POSTGRES_USERNAME=your-username
export AZURE_POSTGRES_PASSWORD=your-password

# Start services (will connect to external PostgreSQL)
docker-compose -f docker-compose_all.yml up -d
```

## Database Migration

### From MySQL to Azure PostgreSQL

1. **Backup MySQL data** (if migrating from existing MySQL setup):
   ```bash
   # Export MySQL data
   mysqldump -u root -p xiaozhi_esp32_server > mysql_backup.sql
   ```

2. **Set up Azure PostgreSQL**:
   ```bash
   # Run the Azure setup script
   ./scripts/setup-azure-postgresql.sh
   ```

3. **Run Liquibase migrations**:
   The application will automatically run PostgreSQL-compatible migrations on startup.

4. **Import data** (if needed):
   ```bash
   # Use the migration API to import data
   curl -X POST "http://localhost:8002/xiaozhi/migration/quick-migrate"
   ```

## Configuration Files

### Development Profiles

- `application-dev.yml` - Updated for PostgreSQL
- `application-postgresql.yml` - PostgreSQL-specific configuration
- `application-azure.yml` - Azure PostgreSQL template

### Docker Compose Files

- `docker-compose_all.yml` - Production deployment with Azure PostgreSQL
- `docker-compose-local.yml` - Local development with Azure PostgreSQL

## Database Access

### Azure PostgreSQL (All Environments)

Connection details are configured via environment variables:
- `AZURE_POSTGRES_SERVER`
- `AZURE_POSTGRES_DATABASE`
- `AZURE_POSTGRES_USERNAME`
- `AZURE_POSTGRES_PASSWORD`

## Data Persistence

### Azure PostgreSQL
- Database: Managed by Azure PostgreSQL Flexible Server
- Automated backups: 7-35 days retention
- Point-in-time recovery available
- Upload files: `./uploadfile` (local container storage)

### Backup and Restore

```bash
# Backup Azure PostgreSQL database
pg_dump -h ${AZURE_POSTGRES_SERVER}.postgres.database.azure.com \
        -U ${AZURE_POSTGRES_USERNAME}@${AZURE_POSTGRES_SERVER} \
        -d ${AZURE_POSTGRES_DATABASE} > backup.sql

# Restore to Azure PostgreSQL database
psql -h ${AZURE_POSTGRES_SERVER}.postgres.database.azure.com \
     -U ${AZURE_POSTGRES_USERNAME}@${AZURE_POSTGRES_SERVER} \
     -d ${AZURE_POSTGRES_DATABASE} < backup.sql
```

## Troubleshooting

### Common Issues

1. **Connection refused**:
   - Verify Azure PostgreSQL server is running
   - Check firewall rules in Azure portal
   - Ensure network connectivity to Azure

2. **Authentication failed**:
   - Verify username/password in environment variables
   - For Azure PostgreSQL, ensure username format is `username@servername`
   - Check Azure PostgreSQL access permissions

3. **SSL connection errors**:
   - Ensure `sslmode=require` in connection URL
   - Verify Azure PostgreSQL SSL configuration
   - Check SSL certificate validity

4. **Migration errors**:
   - Check Liquibase logs for specific errors
   - Ensure PostgreSQL-compatible migration files are being used
   - Verify Azure PostgreSQL version compatibility

### Logs and Monitoring

```bash
# View application logs
docker-compose -f docker-compose_all.yml logs xiaozhi-esp32-server-web

# Monitor Azure PostgreSQL performance
az postgres flexible-server show \
  --resource-group your-resource-group \
  --name ${AZURE_POSTGRES_SERVER}

# Connect to Azure PostgreSQL for monitoring
psql -h ${AZURE_POSTGRES_SERVER}.postgres.database.azure.com \
     -U ${AZURE_POSTGRES_USERNAME}@${AZURE_POSTGRES_SERVER} \
     -d ${AZURE_POSTGRES_DATABASE} \
     -c "SELECT * FROM pg_stat_activity;"
```

## Performance Tuning

### PostgreSQL Configuration

The PostgreSQL container uses default settings. For production, consider:

1. **Memory settings**:
   - `shared_buffers`
   - `effective_cache_size`
   - `work_mem`

2. **Connection settings**:
   - `max_connections`
   - `connection_limit`

3. **Logging**:
   - `log_statement`
   - `log_min_duration_statement`

### Application Configuration

Connection pool settings in `application-postgresql.yml`:
- `initial-size`: 5
- `max-active`: 50
- `min-idle`: 5

Adjust based on your workload and PostgreSQL server capacity.

## Migration from MySQL

See the comprehensive migration guide in `docs/azure-postgresql-setup.md` for detailed instructions on migrating from MySQL to PostgreSQL.