# MySQL to PostgreSQL (Supabase) Migration Guide

## Overview

This guide provides a comprehensive plan to migrate your Cheeko ESP32 Server from MySQL to PostgreSQL/Supabase while maintaining the exact same database structure and functionality.

## Current Setup Analysis

### Current Database: MySQL
- **Driver**: `com.mysql:mysql-connector-j`
- **Database**: Railway MySQL (production) / Local MySQL (dev)
- **ORM**: MyBatis-Plus 3.5.5
- **Migration Tool**: Liquibase 4.20.0
- **Total Changelog Files**: ~100+ SQL migration files

### Target Database: PostgreSQL (Supabase)
- **Driver**: `org.postgresql:postgresql`
- **Database**: Supabase (PostgreSQL 15+)
- **Same ORM**: MyBatis-Plus (compatible)
- **Same Migration Tool**: Liquibase (fully supports PostgreSQL)

---

## Migration Plan

### Phase 1: Preparation (Before Migration)

#### 1.1 Set Up Supabase Project
1. Create a new Supabase project at https://supabase.com
2. Note down the following connection details:
   - **Host**: `db.xxxxxxxxxxxxx.supabase.co`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **Username**: `postgres`
   - **Password**: `[your-password]`
   - **Connection String**: Available in Project Settings > Database

#### 1.2 Backup Current MySQL Database
```bash
# Export your current MySQL database
mysqldump -h [mysql-host] -u [username] -p [database-name] > backup_mysql.sql
```

---

### Phase 2: Code Changes

#### 2.1 Update Maven Dependencies (pom.xml)

**Change:**
```xml
<!-- BEFORE (MySQL) -->
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
</dependency>

<!-- AFTER (PostgreSQL) -->
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
</dependency>
```

#### 2.2 Update Application Configuration Files

**Files to Update:**
- `application-dev.yml`
- `application-prod.yml`
- `application-local.yml`
- `application-railway.yml` (if migrating Railway)
- Any other environment-specific configs

**Configuration Changes:**

**Before (MySQL):**
```yaml
spring:
  datasource:
    druid:
      driver-class-name: com.mysql.cj.jdbc.Driver
      url: jdbc:mysql://host:port/database?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&nullCatalogMeansCurrent=true&useSSL=true&allowPublicKeyRetrieval=true
      username: root
      password: your-password
```

**After (PostgreSQL/Supabase):**
```yaml
spring:
  datasource:
    druid:
      driver-class-name: org.postgresql.Driver
      url: jdbc:postgresql://db.xxxxxxxxxxxxx.supabase.co:5432/postgres?currentSchema=public
      username: postgres
      password: your-supabase-password
```

#### 2.3 Update MyBatis-Plus Configuration (application.yml)

**Add PostgreSQL-specific settings:**
```yaml
mybatis-plus:
  mapper-locations: classpath*:/mapper/**/*.xml
  typeAliasesPackage: xiaozhi.modules.*.entity
  global-config:
    db-config:
      id-type: ASSIGN_ID
    banner: false
  configuration:
    map-underscore-to-camel-case: true
    cache-enabled: false
    call-setters-on-nulls: true
    jdbc-type-for-null: "null"
  configuration-properties:
    prefix:
    # PostgreSQL specific
    blobType: BYTEA  # Changed from BLOB
    boolValue: TRUE
```

---

### Phase 3: SQL Migration Files Conversion

You have **100+ Liquibase changelog SQL files** that need MySQL-to-PostgreSQL syntax conversion.

#### 3.1 Key SQL Syntax Differences

| MySQL Syntax | PostgreSQL Equivalent | Notes |
|--------------|----------------------|-------|
| `tinyint` | `SMALLINT` or `BOOLEAN` | Use BOOLEAN for 0/1 flags |
| `tinyint unsigned` | `SMALLINT` | PostgreSQL has no unsigned |
| `datetime` | `TIMESTAMP` | More precise in PostgreSQL |
| `ENGINE=InnoDB` | *(remove)* | Not needed in PostgreSQL |
| `DEFAULT CHARSET=utf8mb4` | *(remove)* | UTF-8 is default in PostgreSQL |
| `COLLATE=utf8mb4_unicode_ci` | *(remove)* | Use PostgreSQL collations if needed |
| `COMMENT='...'` | `COMMENT ON TABLE ... IS '...'` | Different syntax |
| `AUTO_INCREMENT` | `SERIAL` or `BIGSERIAL` | Or use sequences |
| `` `column` `` (backticks) | `"column"` (quotes) | Or remove quotes |
| `CURRENT_TIMESTAMP` | `CURRENT_TIMESTAMP` | Same (works in both) |
| `ON UPDATE CURRENT_TIMESTAMP` | Use triggers | Not directly supported |

#### 3.2 Automated Conversion Script

I'll provide a Python script to convert all your SQL files automatically.

**Create file: `convert_sql_to_postgresql.py`**

```python
#!/usr/bin/env python3
"""
MySQL to PostgreSQL SQL Converter for Liquibase Changelog Files
Converts all SQL files in db/changelog directory
"""

import re
import os
from pathlib import Path

def convert_mysql_to_postgresql(sql_content):
    """Convert MySQL SQL syntax to PostgreSQL syntax"""

    # Remove ENGINE and CHARSET clauses
    sql_content = re.sub(r'\s*ENGINE\s*=\s*InnoDB', '', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'\s*DEFAULT\s+CHARSET\s*=\s*utf8mb4', '', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'\s*DEFAULT\s+CHARACTER\s+SET\s+utf8mb4', '', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'\s*COLLATE\s*=\s*utf8mb4_unicode_ci', '', sql_content, flags=re.IGNORECASE)

    # Convert tinyint to SMALLINT or BOOLEAN
    # For boolean-like columns (0/1 values with default 0 or 1)
    sql_content = re.sub(
        r'tinyint\s*\(\s*1\s*\)\s+(DEFAULT\s+[01])',
        r'BOOLEAN \1',
        sql_content,
        flags=re.IGNORECASE
    )

    # For regular tinyint (treat as SMALLINT)
    sql_content = re.sub(r'\btinyint\s+unsigned\b', 'SMALLINT', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'\btinyint\b', 'SMALLINT', sql_content, flags=re.IGNORECASE)

    # Convert datetime to TIMESTAMP
    sql_content = re.sub(r'\bdatetime\b', 'TIMESTAMP', sql_content, flags=re.IGNORECASE)

    # Convert AUTO_INCREMENT to SERIAL/BIGSERIAL
    sql_content = re.sub(
        r'(\w+)\s+BIGINT\s+AUTO_INCREMENT',
        r'\1 BIGSERIAL',
        sql_content,
        flags=re.IGNORECASE
    )
    sql_content = re.sub(
        r'(\w+)\s+INT\s+AUTO_INCREMENT',
        r'\1 SERIAL',
        sql_content,
        flags=re.IGNORECASE
    )

    # Remove backticks (MySQL) - PostgreSQL uses double quotes or no quotes
    sql_content = sql_content.replace('`', '')

    # Convert inline COMMENT syntax to separate statements
    # This is more complex and may need manual review for table comments
    # Column comments work differently in PostgreSQL

    # Handle ON UPDATE CURRENT_TIMESTAMP (not directly supported in PostgreSQL)
    # Replace with comment noting manual trigger needed
    if 'ON UPDATE CURRENT_TIMESTAMP' in sql_content.upper():
        sql_content = re.sub(
            r'ON\s+UPDATE\s+CURRENT_TIMESTAMP',
            '-- Note: ON UPDATE CURRENT_TIMESTAMP requires trigger in PostgreSQL',
            sql_content,
            flags=re.IGNORECASE
        )

    # Remove inline column COMMENT (PostgreSQL uses different syntax)
    # Keep the comment text but move to separate COMMENT ON statements
    sql_content = re.sub(r"\s+COMMENT\s+'[^']*'", '', sql_content)
    sql_content = re.sub(r'\s+COMMENT\s+"[^"]*"', '', sql_content)

    return sql_content

def process_directory(changelog_dir):
    """Process all SQL files in the changelog directory"""

    changelog_path = Path(changelog_dir)
    if not changelog_path.exists():
        print(f"Error: Directory not found: {changelog_dir}")
        return

    sql_files = list(changelog_path.glob("*.sql"))

    if not sql_files:
        print(f"No SQL files found in {changelog_dir}")
        return

    print(f"Found {len(sql_files)} SQL files to convert")

    # Create backup directory
    backup_dir = changelog_path / "mysql_backup"
    backup_dir.mkdir(exist_ok=True)

    converted_count = 0

    for sql_file in sql_files:
        print(f"Processing: {sql_file.name}")

        # Backup original file
        backup_file = backup_dir / sql_file.name
        with open(sql_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        # Convert SQL
        converted_content = convert_mysql_to_postgresql(original_content)

        # Write converted SQL
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(converted_content)

        converted_count += 1

    print(f"\n✅ Conversion complete!")
    print(f"   - Converted: {converted_count} files")
    print(f"   - Backups saved to: {backup_dir}")
    print(f"\n⚠️  IMPORTANT: Review the converted files manually for:")
    print(f"   - Table and column COMMENT statements")
    print(f"   - ON UPDATE CURRENT_TIMESTAMP triggers")
    print(f"   - Complex data type conversions")

if __name__ == "__main__":
    # Update this path to your changelog directory
    changelog_directory = r"C:\Users\Acer\Cheeko-esp32-server\main\manager-api\src\main\resources\db\changelog"

    print("=" * 60)
    print("MySQL to PostgreSQL SQL Converter")
    print("=" * 60)

    process_directory(changelog_directory)
```

#### 3.3 Manual Review Items

After running the automated conversion, manually review:

1. **COMMENT Statements**: PostgreSQL uses separate `COMMENT ON` statements
   ```sql
   -- MySQL
   CREATE TABLE users (...) COMMENT='User table';

   -- PostgreSQL
   CREATE TABLE users (...);
   COMMENT ON TABLE users IS 'User table';
   ```

2. **ON UPDATE CURRENT_TIMESTAMP**: Requires triggers in PostgreSQL
   ```sql
   -- Create a generic update trigger function (add to a new migration file)
   CREATE OR REPLACE FUNCTION update_updated_at_column()
   RETURNS TRIGGER AS $$
   BEGIN
       NEW.update_date = CURRENT_TIMESTAMP;
       RETURN NEW;
   END;
   $$ language 'plpgsql';

   -- Apply to tables that need it
   CREATE TRIGGER update_sys_user_updated_at
       BEFORE UPDATE ON sys_user
       FOR EACH ROW
       EXECUTE FUNCTION update_updated_at_column();
   ```

3. **Boolean Columns**: Convert tinyint(1) with 0/1 values to proper BOOLEAN type

4. **Case Sensitivity**: PostgreSQL is case-sensitive by default
   - Use lowercase for table/column names
   - Or use double quotes for mixed case

---

### Phase 4: Data Migration

#### Option A: Fresh Start (Recommended for Clean Migration)

1. **Start with empty Supabase database**
2. **Run your application** - Liquibase will execute all converted changelog files
3. **Migrate data** using one of these tools:
   - **pgLoader** (fastest, automated)
   - Manual data export/import
   - Custom migration scripts

**Using pgLoader (Recommended):**

Install pgLoader:
```bash
# Ubuntu/Debian
sudo apt-get install pgloader

# macOS
brew install pgloader

# Windows (WSL or Docker)
docker pull dimitri/pgloader
```

Create migration config `mysql-to-postgres.load`:
```conf
LOAD DATABASE
    FROM mysql://username:password@mysql-host:3306/database_name
    INTO postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres

WITH include drop, create tables, create indexes, reset sequences

SET maintenance_work_mem to '128MB', work_mem to '12MB'

CAST type datetime to timestamp
     drop default drop not null using zero-dates-to-null,
     type date drop not null drop default using zero-dates-to-null,
     type tinyint to smallint,
     type year to integer

BEFORE LOAD DO
    $$ DROP SCHEMA IF EXISTS public CASCADE; $$,
    $$ CREATE SCHEMA public; $$;
```

Run migration:
```bash
pgloader mysql-to-postgres.load
```

#### Option B: Manual Data Export/Import

```bash
# 1. Export data from MySQL (data only, no structure)
mysqldump --no-create-info --skip-triggers -h mysql-host -u username -p database_name > data.sql

# 2. Convert SQL syntax (use provided Python script)
python convert_data_dump.py data.sql > data_postgresql.sql

# 3. Import to PostgreSQL
psql -h db.xxxxx.supabase.co -U postgres -d postgres -f data_postgresql.sql
```

---

### Phase 5: Testing & Validation

#### 5.1 Pre-deployment Checklist

- [ ] All Maven dependencies updated
- [ ] All application YAML files updated with PostgreSQL config
- [ ] All SQL changelog files converted and backed up
- [ ] SQL conversion script executed successfully
- [ ] Manual review of converted SQL completed
- [ ] Triggers created for ON UPDATE CURRENT_TIMESTAMP columns
- [ ] Supabase project created and connection tested

#### 5.2 Local Testing

1. **Update your local application-local.yml** to point to Supabase
2. **Clean and rebuild**:
   ```bash
   mvn clean install
   ```
3. **Run application**:
   ```bash
   mvn spring-boot:run
   ```
4. **Check Liquibase execution**:
   - Watch console for Liquibase changelog execution
   - Should see all changesets applying successfully

#### 5.3 Verify Database Schema

Connect to Supabase and verify:
```sql
-- Check tables created
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- Check row counts
SELECT
    schemaname,
    tablename,
    n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Verify Liquibase tracking
SELECT * FROM databasechangelog ORDER BY dateexecuted DESC LIMIT 10;
```

#### 5.4 Functional Testing

Test all critical application features:
- [ ] User authentication and login
- [ ] Device management (CRUD operations)
- [ ] Agent configuration
- [ ] Voice/audio processing
- [ ] Firmware updates
- [ ] Redis integration
- [ ] API endpoints

---

### Phase 6: Production Deployment

#### 6.1 Deployment Strategy

**Option 1: Blue-Green Deployment (Zero Downtime)**
1. Keep MySQL running
2. Deploy new version with PostgreSQL to staging
3. Test thoroughly
4. Switch traffic to new version
5. Keep MySQL as backup for rollback

**Option 2: Maintenance Window**
1. Schedule maintenance window
2. Take application offline
3. Migrate data
4. Deploy new version
5. Verify and bring online

#### 6.2 Rollback Plan

If issues occur:
1. **Keep MySQL backup** for at least 7 days
2. **Revert code changes**:
   ```bash
   git revert [commit-hash]
   ```
3. **Restore application.yml** to MySQL config
4. **Redeploy** previous version

---

## Important Notes

### Things That Work Without Changes

✅ **MyBatis-Plus**: Fully compatible with PostgreSQL
✅ **Liquibase**: Full PostgreSQL support
✅ **Spring Boot**: Database-agnostic
✅ **Druid Connection Pool**: Works with PostgreSQL
✅ **Redis**: Not affected (no changes needed)
✅ **Application Logic**: No changes needed

### Potential Issues to Watch

⚠️ **String Comparison**: PostgreSQL is case-sensitive by default
⚠️ **Date/Time Handling**: Slightly different behavior
⚠️ **Implicit Type Casting**: PostgreSQL is stricter
⚠️ **Sequence Reset**: May need manual adjustment after data import

### Performance Considerations

- **Indexes**: Will need to be rebuilt (Liquibase handles this)
- **Vacuum**: Run `VACUUM ANALYZE` after large data imports
- **Connection Pooling**: Adjust pool sizes for PostgreSQL (generally same as MySQL)

---

## Cost Comparison

### MySQL (Railway)
- Current costs: Variable based on usage

### PostgreSQL (Supabase)
- **Free Tier**: 500MB database, 50,000 requests
- **Pro**: $25/month (8GB database, unlimited requests)
- **Includes**: Built-in auth, storage, realtime, APIs

---

## Timeline Estimate

| Phase | Duration | Notes |
|-------|----------|-------|
| Preparation & Setup | 1-2 hours | Supabase setup, backup |
| Code Changes | 2-3 hours | Maven, YAML configs |
| SQL Conversion | 3-4 hours | Automated + manual review |
| Data Migration | 2-4 hours | Depends on data size |
| Testing | 4-8 hours | Thorough testing |
| Production Deploy | 2-3 hours | With monitoring |
| **Total** | **14-24 hours** | Spread over multiple days |

---

## Support & Resources

### Documentation
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Supabase Documentation](https://supabase.com/docs)
- [Liquibase PostgreSQL](https://docs.liquibase.com/install/tutorials/postgresql.html)
- [MyBatis PostgreSQL](https://mybatis.org/mybatis-3/)

### Migration Tools
- [pgLoader Documentation](https://pgloader.readthedocs.io/)
- [AWS Database Migration Service](https://aws.amazon.com/dms/) (alternative)

---

## Next Steps

1. **Review this guide** thoroughly
2. **Set up Supabase project** (free tier for testing)
3. **Test conversion script** on a few sample SQL files
4. **Create test environment** with PostgreSQL
5. **Run pilot migration** with small dataset
6. **Plan production cutover** date

---

## Questions to Answer Before Migration

- [ ] What is the current database size?
- [ ] What is the acceptable downtime window?
- [ ] Do you need to maintain MySQL as backup?
- [ ] Will you use Supabase's additional features (Auth, Storage)?
- [ ] Do you have a staging environment for testing?

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Author**: Claude Code Migration Assistant
