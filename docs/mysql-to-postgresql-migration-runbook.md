# MySQL to PostgreSQL Migration Runbook

This runbook provides step-by-step instructions for migrating the xiaozhi-esp32-server from MySQL to PostgreSQL.

## Pre-Migration Checklist

### Prerequisites
- [ ] PostgreSQL 15+ server available (local or Azure)
- [ ] Current MySQL database accessible
- [ ] Application downtime window scheduled
- [ ] Backup of current MySQL data created
- [ ] All team members notified of migration schedule

### Environment Preparation
- [ ] PostgreSQL server configured and accessible
- [ ] Database `xiaozhi_esp32_server` created in PostgreSQL
- [ ] Network connectivity verified between application and PostgreSQL
- [ ] SSL certificates configured (for Azure PostgreSQL)

## Migration Steps

### Phase 1: Preparation (30 minutes)

#### Step 1.1: Backup Current MySQL Data
```bash
# Create MySQL backup
mysqldump -u root -p xiaozhi_esp32_server > mysql_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup file
ls -la mysql_backup_*.sql
```

#### Step 1.2: Stop Application Services
```bash
# Stop all application containers
docker-compose down

# Verify no services are running
docker ps | grep xiaozhi
```

#### Step 1.3: Verify PostgreSQL Setup
```bash
# Test PostgreSQL connection
psql -h your-postgres-host -p 5432 -U postgres -d xiaozhi_esp32_server -c "SELECT version();"

# For Azure PostgreSQL
psql -h your-server.postgres.database.azure.com -p 5432 -U username@your-server -d xiaozhi_esp32_server -c "SELECT version();"
```

### Phase 2: Code Deployment (15 minutes)

#### Step 2.1: Deploy Updated Application Code
```bash
# Pull latest code with PostgreSQL support
git pull origin main

# Verify PostgreSQL driver in pom.xml
grep -A 3 "postgresql" main/manager-api/pom.xml
```

#### Step 2.2: Update Configuration
```bash
# For local PostgreSQL
export SPRING_PROFILES_ACTIVE=postgresql

# For Azure PostgreSQL
export SPRING_PROFILES_ACTIVE=azure
export AZURE_POSTGRES_SERVER=your-server-name
export AZURE_POSTGRES_DATABASE=xiaozhi_esp32_server
export AZURE_POSTGRES_USERNAME=your-username
export AZURE_POSTGRES_PASSWORD=your-password
```

### Phase 3: Database Migration (45 minutes)

#### Step 3.1: Run Schema Migration
```bash
# Start application to run Liquibase migrations
docker-compose -f docker-compose-postgresql-dev.yml up -d xiaozhi-esp32-server-web

# Monitor logs for migration completion
docker-compose -f docker-compose-postgresql-dev.yml logs -f xiaozhi-esp32-server-web
```

#### Step 3.2: Migrate Data Using API
```bash
# Export data from MySQL
curl -X POST "http://localhost:8002/xiaozhi/migration/export-mysql" \
  -d "host=127.0.0.1&port=3306&database=xiaozhi_esp32_server&username=root&password=123456"

# Import data to PostgreSQL
curl -X POST "http://localhost:8002/xiaozhi/migration/import-postgresql" \
  -d "host=127.0.0.1&port=5432&database=xiaozhi_esp32_server&username=postgres&password=123456&inputDir=/path/to/export"
```

#### Step 3.3: Alternative - Quick Migration
```bash
# Use quick migration endpoint for local setup
curl -X POST "http://localhost:8002/xiaozhi/migration/quick-migrate"
```

### Phase 4: Validation (30 minutes)

#### Step 4.1: Validate Data Migration
```bash
# Use validation endpoint
curl -X POST "http://localhost:8002/xiaozhi/migration/validate"
```

#### Step 4.2: Manual Data Verification
```sql
-- Connect to PostgreSQL
psql -h localhost -p 5432 -U postgres -d xiaozhi_esp32_server

-- Check table counts
SELECT 
    schemaname,
    tablename,
    n_tup_ins as "rows"
FROM pg_stat_user_tables 
ORDER BY n_tup_ins DESC;

-- Verify specific tables
SELECT COUNT(*) FROM sys_user;
SELECT COUNT(*) FROM ai_agent;
SELECT COUNT(*) FROM ai_device;
SELECT COUNT(*) FROM ai_model_config;
```

#### Step 4.3: Application Functionality Test
```bash
# Test API endpoints                              
curl -X GET "http://localhost:8002/xiaozhi/config/getConfig"          

# Test agent operations   
curl -X GET "http://localhost:8002/xiaozhi/agent/getUserAgents"

# Test model operations
curl -X GET "http://localhost:8002/xiaozhi/model/getModelNames?modelType=LLM"
```

### Phase 5: Go-Live (15 minutes)
                              
#### Step 5.1: Start All Services
```bash
# Start all application services
docker-compose -f docker-compose-postgresql-dev.yml up -d

# Verify all services are healthy
docker-compose -f docker-compose-postgresql-dev.yml ps
```

#### Step 5.2: Monitor Application Health
```bash
# Check application logs
docker-compose -f docker-compose-postgresql-dev.yml logs -f

# Test critical endpoints
curl -X GET "http://localhost:8002/xiaozhi/doc.html"
```

## Post-Migration Tasks

### Immediate (Day 1)
- [ ] Monitor application performance and error logs
- [ ] Verify all user-facing functionality works correctly
- [ ] Check database connection pool metrics
- [ ] Validate backup and restore procedures

### Short-term (Week 1)
- [ ] Performance tuning based on usage patterns
- [ ] Update monitoring and alerting for PostgreSQL
- [ ] Train team on PostgreSQL-specific operations
- [ ] Document any issues and resolutions

### Long-term (Month 1)
- [ ] Remove MySQL dependencies and configurations
- [ ] Optimize PostgreSQL configuration for production workload
- [ ] Implement PostgreSQL-specific monitoring
- [ ] Review and update disaster recovery procedures

## Rollback Procedures

### Emergency Rollback (if migration fails)

#### Step 1: Stop PostgreSQL Application
```bash
docker-compose -f docker-compose-postgresql-dev.yml down
```

#### Step 2: Restore MySQL Configuration
```bash
# Revert to MySQL configuration
git checkout HEAD~1 -- main/manager-api/pom.xml
git checkout HEAD~1 -- main/manager-api/src/main/resources/application-dev.yml

# Start MySQL services
docker-compose -f docker-compose_all.yml up -d
```

#### Step 3: Restore MySQL Data (if needed)
```bash
# Restore from backup
mysql -u root -p xiaozhi_esp32_server < mysql_backup_YYYYMMDD_HHMMSS.sql
```

## Troubleshooting Guide

### Common Issues

#### Connection Refused
**Symptoms:** Application cannot connect to PostgreSQL
**Solutions:**
1. Verify PostgreSQL service is running
2. Check firewall rules and network connectivity
3. Validate connection string format
4. Ensure SSL configuration is correct (for Azure)

#### Authentication Failed
**Symptoms:** Login errors to PostgreSQL
**Solutions:**
1. Verify username/password combination
2. Check username format for Azure: `username@servername`
3. Ensure user has necessary permissions
4. Validate SSL certificate configuration

#### Migration Data Mismatch
**Symptoms:** Row counts don't match between MySQL and PostgreSQL
**Solutions:**
1. Re-run data validation
2. Check for data type conversion issues
3. Verify all tables were migrated
4. Check for foreign key constraint violations

#### Performance Issues
**Symptoms:** Slow query performance after migration
**Solutions:**
1. Update table statistics: `ANALYZE;`
2. Check query execution plans
3. Verify indexes are created correctly
4. Adjust PostgreSQL configuration parameters

### Emergency Contacts
- Database Administrator: [Contact Info]
- DevOps Team: [Contact Info]
- Application Team Lead: [Contact Info]

## Validation Checklist

### Data Integrity
- [ ] All tables migrated successfully
- [ ] Row counts match between MySQL and PostgreSQL
- [ ] Foreign key relationships maintained
- [ ] JSON data properly converted
- [ ] Date/time values correctly formatted

### Application Functionality
- [ ] User authentication works
- [ ] Agent management functions correctly
- [ ] Device operations successful
- [ ] Model configuration accessible
- [ ] File uploads/downloads working
- [ ] WebSocket connections stable

### Performance
- [ ] Response times within acceptable limits
- [ ] Database connection pool stable
- [ ] Memory usage normal
- [ ] No connection leaks detected

### Monitoring
- [ ] Application logs show no errors
- [ ] Database logs clean
- [ ] Monitoring alerts configured
- [ ] Backup procedures tested

## Success Criteria

The migration is considered successful when:
1. All data has been migrated with 100% integrity
2. All application functionality works as expected
3. Performance meets or exceeds previous benchmarks
4. No critical errors in logs for 24 hours
5. All team members trained on new procedures

## Sign-off

- [ ] Database Administrator: _________________ Date: _______
- [ ] Application Team Lead: _________________ Date: _______
- [ ] DevOps Engineer: _________________ Date: _______
- [ ] Project Manager: _________________ Date: _______