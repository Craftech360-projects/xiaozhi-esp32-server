# Design Document

## Overview

This design outlines the migration strategy from MySQL to Azure PostgreSQL for the xiaozhi-esp32-server application. The migration involves updating dependencies, modifying SQL syntax, updating configuration files, and ensuring data compatibility between the two database systems.

## Architecture

### Current Architecture
- **Database**: MySQL 8.0+ with Druid connection pool
- **ORM**: MyBatis-Plus with XML mappers
- **Migration Tool**: Liquibase for schema management
- **Caching**: Redis for session and configuration caching
- **Deployment**: Docker containers with MySQL container

### Target Architecture
- **Database**: Azure PostgreSQL Flexible Server
- **Connection Pool**: HikariCP (Spring Boot default) or Druid with PostgreSQL driver
- **ORM**: MyBatis-Plus with PostgreSQL-compatible XML mappers
- **Migration Tool**: Liquibase with PostgreSQL-compatible changesets
- **Caching**: Redis (unchanged)
- **Deployment**: Docker containers connecting to Azure PostgreSQL

## Components and Interfaces

### 1. Database Driver and Dependencies
**Changes Required:**
- Replace MySQL JDBC driver with PostgreSQL JDBC driver
- Update Maven dependencies in `pom.xml`
- Ensure MyBatis-Plus compatibility with PostgreSQL

**New Dependencies:**
```xml
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>
```

### 2. Configuration Updates
**Files to Modify:**
- `application-dev.yml` - Development database configuration
- `application.yml` - Base configuration
- Docker Compose files - Replace MySQL containers with PostgreSQL connection
- Environment variable templates

**Configuration Changes:**
```yaml
spring:
  datasource:
    driver-class-name: org.postgresql.Driver
    url: jdbc:postgresql://[server].postgres.database.azure.com:5432/xiaozhi_esp32_server?sslmode=require
    username: [username]@[server]
    password: [password]
```

### 3. SQL Syntax Migration
**Key Differences to Address:**

| MySQL | PostgreSQL | Impact |
|-------|------------|---------|
| `JSON_ARRAYAGG()` | `json_agg()` | Agent plugin mapping queries |
| `JSON_OBJECT()` | `json_build_object()` | Complex result mapping |
| `LIMIT 0,1` | `LIMIT 1 OFFSET 0` | Pagination queries |
| `AUTO_INCREMENT` | `SERIAL` or `IDENTITY` | Primary key generation |
| `TINYINT` | `SMALLINT` or `BOOLEAN` | Data type mapping |
| `DATETIME` | `TIMESTAMP` | Date/time fields |
| `LONGTEXT` | `TEXT` | Large text fields |

### 4. MyBatis Mapper Updates
**Files Requiring Updates:**
- `AgentDao.xml` - Complex JSON aggregation queries
- `ModelConfigDao.xml` - Data type mappings
- `AiAgentChatHistoryDao.xml` - Delete and update operations
- All other mapper files with MySQL-specific syntax

**Example Transformation:**
```xml
<!-- MySQL Version -->
<select id="selectAgentInfoById" resultMap="AgentInfoMap">
    SELECT a.*,
           COALESCE(
               (SELECT JSON_ARRAYAGG(
                   JSON_OBJECT(
                       'id', m.id,
                       'agentId', m.agent_id,
                       'pluginId', m.plugin_id,
                       'paramInfo', m.param_info
                   )
               )
               FROM ai_agent_plugin_mapping m
               WHERE m.agent_id = a.id),
               JSON_ARRAY()
           ) AS functions
    FROM ai_agent a
    WHERE a.id = #{agentId}
</select>

<!-- PostgreSQL Version -->
<select id="selectAgentInfoById" resultMap="AgentInfoMap">
    SELECT a.*,
           COALESCE(
               (SELECT json_agg(
                   json_build_object(
                       'id', m.id,
                       'agentId', m.agent_id,
                       'pluginId', m.plugin_id,
                       'paramInfo', m.param_info
                   )
               )
               FROM ai_agent_plugin_mapping m
               WHERE m.agent_id = a.id),
               '[]'::json
           ) AS functions
    FROM ai_agent a
    WHERE a.id = #{agentId}
</select>
```

## Data Models

### Schema Migration Strategy
1. **Data Type Mapping:**
   - `BIGINT` → `BIGINT` (compatible)
   - `VARCHAR(n)` → `VARCHAR(n)` (compatible)
   - `TINYINT` → `SMALLINT` or `BOOLEAN`
   - `DATETIME` → `TIMESTAMP`
   - `LONGTEXT` → `TEXT`
   - `JSON` → `JSONB` (for better performance)

2. **Primary Key Strategy:**
   - Replace `AUTO_INCREMENT` with `SERIAL` or `IDENTITY`
   - Update MyBatis-Plus ID generation strategy

3. **Index Migration:**
   - Convert MySQL indexes to PostgreSQL syntax
   - Optimize for PostgreSQL query planner

### Liquibase Migration Files
**Strategy:**
- Create new PostgreSQL-compatible migration files
- Maintain existing MySQL migrations for rollback capability
- Use conditional changesets for database-specific operations

## Error Handling

### Migration Risks and Mitigation
1. **Data Loss Risk:**
   - **Mitigation:** Comprehensive backup before migration
   - **Validation:** Data integrity checks post-migration

2. **Query Performance:**
   - **Risk:** Different query optimization in PostgreSQL
   - **Mitigation:** Performance testing and query optimization

3. **JSON Function Compatibility:**
   - **Risk:** Complex JSON operations may behave differently
   - **Mitigation:** Thorough testing of all JSON-related queries

4. **Connection Pool Issues:**
   - **Risk:** Different connection behavior with PostgreSQL
   - **Mitigation:** Connection pool tuning and monitoring

### Error Recovery
- Maintain MySQL configuration as fallback
- Implement database health checks
- Create rollback procedures for each migration step

## Testing Strategy

### Unit Testing
- Test all DAO methods with PostgreSQL
- Validate JSON operations and complex queries
- Test data type conversions

### Integration Testing
- Full application testing with PostgreSQL
- Performance comparison with MySQL baseline
- Load testing with realistic data volumes

### Migration Testing
- Test migration scripts on copy of production data
- Validate data integrity after migration
- Test rollback procedures

### Azure PostgreSQL Specific Testing
- Connection security and SSL requirements
- Azure-specific features and limitations
- Backup and restore procedures

## Deployment Strategy

### Phase 1: Development Environment
1. Set up Azure PostgreSQL Flexible Server
2. Update development configuration
3. Test all application features

### Phase 2: Staging Environment
1. Deploy to staging with PostgreSQL
2. Run comprehensive test suite
3. Performance benchmarking

### Phase 3: Production Migration
1. Schedule maintenance window
2. Backup MySQL data
3. Migrate data to PostgreSQL
4. Switch application configuration
5. Validate functionality
6. Monitor performance

### Rollback Plan
- Keep MySQL instance available during initial period
- Quick configuration switch capability
- Data synchronization strategy if needed