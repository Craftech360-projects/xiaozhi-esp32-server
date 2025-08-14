# Database Setup Guide for AI Toy Analytics

## 1. Database Selection: Why MySQL?

### Recommended: MySQL 8.0+
**Reasons to stick with MySQL:**
- ✅ Xiaozhi server already uses MySQL (no refactoring needed)
- ✅ Excellent for relational data (parent-child, device-user relationships)
- ✅ Mature ecosystem with great tooling (DBeaver works perfectly)
- ✅ JSON column support for flexible analytics data
- ✅ Good performance for analytics queries with proper indexing
- ✅ Free and open source

### Alternative Options (if starting fresh):

| Database | Pros | Cons | Use When |
|----------|------|------|----------|
| **PostgreSQL** | Better JSON support, advanced analytics | Need migration from MySQL | Starting completely fresh |
| **MongoDB** | Flexible schema, good for unstructured data | Not good for relationships | Chat logs only, no analytics |
| **TimescaleDB** | Optimized for time-series | Overkill for your needs | Millions of interactions/day |
| **SQLite** | Simple, embedded | Not for production | Development/testing only |

**My Recommendation: Stick with MySQL** - The migration effort isn't worth it since MySQL handles your requirements well.

## 2. Installation & Setup

### Option A: Local Development (Recommended for Testing)

#### macOS Installation:
```bash
# Install MySQL using Homebrew
brew install mysql

# Start MySQL service
brew services start mysql

# Secure the installation
mysql_secure_installation

# Create database and user
mysql -u root -p
```

```sql
-- In MySQL prompt:
CREATE DATABASE xiaozhi_ai_toy CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'xiaozhi_dev'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON xiaozhi_ai_toy.* TO 'xiaozhi_dev'@'localhost';
FLUSH PRIVILEGES;
```

#### Windows Installation:
```powershell
# Download MySQL Installer from https://dev.mysql.com/downloads/installer/
# Run installer and select "Developer Default"
# Follow setup wizard

# After installation, open MySQL Workbench or command line
```

#### Linux (Ubuntu/Debian):
```bash
# Update package index
sudo apt update

# Install MySQL
sudo apt install mysql-server

# Secure installation
sudo mysql_secure_installation

# Create database
sudo mysql -u root -p
```

### Option B: Docker (Recommended for Consistency)

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: xiaozhi_mysql
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: root_password_change_me
      MYSQL_DATABASE: xiaozhi_ai_toy
      MYSQL_USER: xiaozhi_dev
      MYSQL_PASSWORD: dev_password_change_me
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    command: 
      --default-authentication-plugin=mysql_native_password
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: xiaozhi_phpmyadmin
    restart: unless-stopped
    environment:
      PMA_HOST: mysql
      PMA_PORT: 3306
      UPLOAD_LIMIT: 100M
    ports:
      - "8080:80"
    depends_on:
      - mysql

volumes:
  mysql_data:
```

Run Docker setup:
```bash
# Start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f mysql

# Stop containers
docker-compose down
```

### Option C: Cloud Databases (Production Ready)

#### 1. Railway (Currently Used by Xiaozhi)
```yaml
# Already configured in application.yml
# Good for small-medium projects
# $5-20/month
```

#### 2. PlanetScale (Recommended for Scaling)
```bash
# Serverless MySQL, great for scaling
# Free tier available
# Automatic backups and branching

# Install CLI
brew install planetscale/tap/pscale

# Create database
pscale database create xiaozhi-ai-toy

# Get connection string
pscale password create xiaozhi-ai-toy main
```

#### 3. AWS RDS
```bash
# Enterprise-grade, more complex
# $15-50/month for small instances
# Use AWS Console or CLI to create
```

#### 4. Google Cloud SQL
```bash
# Similar to AWS RDS
# Good integration with GCP services
# $10-40/month
```

## 3. Database Initialization

### Step 1: Create Initial Schema

Create `init.sql`:
```sql
-- =============================================
-- Database Initialization Script
-- =============================================

-- Ensure UTF8MB4 for emoji support
ALTER DATABASE xiaozhi_ai_toy CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- =============================================
-- Core System Tables (From Xiaozhi)
-- =============================================

-- System users (parents)
CREATE TABLE IF NOT EXISTS sys_user (
  id BIGINT NOT NULL AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL,
  password VARCHAR(100),
  super_admin TINYINT UNSIGNED DEFAULT 0,
  status TINYINT DEFAULT 1,
  email VARCHAR(100),
  phone VARCHAR(20),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username),
  UNIQUE KEY uk_email (email),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='System users (parents)';

-- User tokens for authentication
CREATE TABLE IF NOT EXISTS sys_user_token (
  id BIGINT NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  token VARCHAR(100) NOT NULL,
  expire_date DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_user_id (user_id),
  UNIQUE KEY uk_token (token),
  FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='User authentication tokens';

-- =============================================
-- Device Management
-- =============================================

CREATE TABLE IF NOT EXISTS ai_device (
  id VARCHAR(32) NOT NULL,
  mac_address VARCHAR(50) NOT NULL,
  device_name VARCHAR(100),
  device_type VARCHAR(50) DEFAULT 'esp32',
  firmware_version VARCHAR(20),
  last_connected_at DATETIME,
  is_online BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_mac (mac_address),
  INDEX idx_online (is_online),
  INDEX idx_last_connected (last_connected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='IoT devices';

-- =============================================
-- Child Profiles & Relationships
-- =============================================

CREATE TABLE IF NOT EXISTS child_profile (
  id VARCHAR(32) NOT NULL,
  parent_user_id BIGINT NOT NULL,
  child_name VARCHAR(100) NOT NULL,
  age INT,
  gender VARCHAR(10),
  device_id VARCHAR(32),
  avatar_url VARCHAR(255),
  preferences JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (parent_user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
  FOREIGN KEY (device_id) REFERENCES ai_device(id) ON DELETE SET NULL,
  INDEX idx_parent (parent_user_id),
  INDEX idx_device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Child profiles';

-- =============================================
-- Conversation Storage
-- =============================================

CREATE TABLE IF NOT EXISTS chat_sessions (
  id VARCHAR(32) NOT NULL,
  child_profile_id VARCHAR(32) NOT NULL,
  device_id VARCHAR(32),
  session_start DATETIME NOT NULL,
  session_end DATETIME,
  duration_seconds INT,
  interaction_count INT DEFAULT 0,
  PRIMARY KEY (id),
  FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE,
  FOREIGN KEY (device_id) REFERENCES ai_device(id) ON DELETE SET NULL,
  INDEX idx_child (child_profile_id),
  INDEX idx_start_time (session_start),
  INDEX idx_child_date (child_profile_id, session_start)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Chat sessions';

CREATE TABLE IF NOT EXISTS chat_messages (
  id BIGINT NOT NULL AUTO_INCREMENT,
  session_id VARCHAR(32) NOT NULL,
  role ENUM('user', 'assistant', 'system') NOT NULL,
  content TEXT NOT NULL,
  audio_url VARCHAR(255),
  timestamp DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
  processing_time_ms INT,
  tokens_used INT,
  PRIMARY KEY (id),
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
  INDEX idx_session (session_id),
  INDEX idx_timestamp (timestamp),
  INDEX idx_session_time (session_id, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Individual chat messages';

-- =============================================
-- Analytics Tables
-- =============================================

CREATE TABLE IF NOT EXISTS daily_analytics (
  id BIGINT NOT NULL AUTO_INCREMENT,
  child_profile_id VARCHAR(32) NOT NULL,
  analytics_date DATE NOT NULL,
  total_sessions INT DEFAULT 0,
  total_minutes INT DEFAULT 0,
  total_interactions INT DEFAULT 0,
  unique_topics JSON,
  vocabulary_stats JSON,
  sentiment_summary JSON,
  learning_metrics JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_child_date (child_profile_id, analytics_date),
  FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE,
  INDEX idx_date (analytics_date),
  INDEX idx_child_date_desc (child_profile_id, analytics_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Daily analytics summary';

CREATE TABLE IF NOT EXISTS interaction_categories (
  id BIGINT NOT NULL AUTO_INCREMENT,
  message_id BIGINT NOT NULL,
  category VARCHAR(50),
  confidence DECIMAL(3,2),
  keywords JSON,
  sentiment_score DECIMAL(3,2),
  educational_value INT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
  INDEX idx_message (message_id),
  INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Message categorization';

CREATE TABLE IF NOT EXISTS learning_milestones (
  id BIGINT NOT NULL AUTO_INCREMENT,
  child_profile_id VARCHAR(32) NOT NULL,
  milestone_type VARCHAR(50),
  milestone_name VARCHAR(100),
  milestone_description TEXT,
  achieved_at DATETIME,
  evidence JSON,
  PRIMARY KEY (id),
  FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE,
  INDEX idx_child (child_profile_id),
  INDEX idx_achieved (achieved_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Learning achievements';

-- =============================================
-- Parental Controls
-- =============================================

CREATE TABLE IF NOT EXISTS parental_settings (
  id BIGINT NOT NULL AUTO_INCREMENT,
  child_profile_id VARCHAR(32) NOT NULL,
  daily_time_limit_minutes INT DEFAULT 60,
  allowed_hours_start TIME DEFAULT '07:00:00',
  allowed_hours_end TIME DEFAULT '21:00:00',
  content_filter_level ENUM('low', 'medium', 'high') DEFAULT 'medium',
  audio_recording_enabled BOOLEAN DEFAULT TRUE,
  data_retention_days INT DEFAULT 90,
  notification_preferences JSON,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_child (child_profile_id),
  FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Parent control settings';

-- =============================================
-- Indexes for Performance
-- =============================================

-- Optimize for common queries
CREATE INDEX idx_analytics_lookup 
ON daily_analytics(child_profile_id, analytics_date DESC);

CREATE INDEX idx_message_search 
ON chat_messages(session_id, timestamp DESC);

CREATE INDEX idx_category_analysis 
ON interaction_categories(category, created_at DESC);

-- =============================================
-- Initial Data
-- =============================================

-- Create admin user (change password immediately!)
INSERT INTO sys_user (username, password, super_admin, email) 
VALUES ('admin', '$2a$10$EblZqNptyYvcLm/VwDCVAuBjzZOI7khzdyGPBr08PpIi0na624b8.', 1, 'admin@xiaozhi.ai');

-- Add sample parent account
INSERT INTO sys_user (username, password, email) 
VALUES ('parent_demo', '$2a$10$EblZqNptyYvcLm/VwDCVAuBjzZOI7khzdyGPBr08PpIi0na624b8.', 'parent@demo.com');

-- =============================================
-- Views for Easy Querying
-- =============================================

CREATE OR REPLACE VIEW v_child_activity AS
SELECT 
    cp.id as child_id,
    cp.child_name,
    cp.parent_user_id,
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(cm.id) as total_messages,
    MAX(cs.session_start) as last_activity
FROM child_profile cp
LEFT JOIN chat_sessions cs ON cp.id = cs.child_profile_id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
GROUP BY cp.id;

CREATE OR REPLACE VIEW v_daily_summary AS
SELECT 
    da.*,
    cp.child_name,
    cp.parent_user_id
FROM daily_analytics da
JOIN child_profile cp ON da.child_profile_id = cp.id;

-- =============================================
-- Stored Procedures
-- =============================================

DELIMITER //

CREATE PROCEDURE sp_get_child_summary(
    IN p_child_id VARCHAR(32),
    IN p_date DATE
)
BEGIN
    SELECT 
        child_profile_id,
        analytics_date,
        total_sessions,
        total_minutes,
        total_interactions,
        unique_topics,
        sentiment_summary,
        learning_metrics
    FROM daily_analytics
    WHERE child_profile_id = p_child_id 
    AND analytics_date = p_date;
END //

CREATE PROCEDURE sp_generate_daily_analytics(
    IN p_date DATE
)
BEGIN
    INSERT INTO daily_analytics (
        child_profile_id,
        analytics_date,
        total_sessions,
        total_minutes,
        total_interactions
    )
    SELECT 
        cs.child_profile_id,
        p_date,
        COUNT(DISTINCT cs.id),
        SUM(cs.duration_seconds) / 60,
        SUM(cs.interaction_count)
    FROM chat_sessions cs
    WHERE DATE(cs.session_start) = p_date
    GROUP BY cs.child_profile_id
    ON DUPLICATE KEY UPDATE
        total_sessions = VALUES(total_sessions),
        total_minutes = VALUES(total_minutes),
        total_interactions = VALUES(total_interactions);
END //

DELIMITER ;

-- =============================================
-- Triggers
-- =============================================

DELIMITER //

CREATE TRIGGER tr_update_session_metrics
AFTER INSERT ON chat_messages
FOR EACH ROW
BEGIN
    UPDATE chat_sessions 
    SET interaction_count = interaction_count + 1
    WHERE id = NEW.session_id;
END //

DELIMITER ;
```

### Step 2: Run Initialization

```bash
# Using MySQL command line
mysql -u xiaozhi_dev -p xiaozhi_ai_toy < init.sql

# Or using Docker
docker exec -i xiaozhi_mysql mysql -u xiaozhi_dev -p xiaozhi_ai_toy < init.sql

# Verify tables created
mysql -u xiaozhi_dev -p xiaozhi_ai_toy -e "SHOW TABLES;"
```

## 4. Application Configuration

### Update application.yml:
```yaml
spring:
  datasource:
    # Local development
    url: jdbc:mysql://localhost:3306/xiaozhi_ai_toy?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false
    username: xiaozhi_dev
    password: your_secure_password
    
    # Docker
    # url: jdbc:mysql://mysql:3306/xiaozhi_ai_toy?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai
    
    # Production (PlanetScale example)
    # url: jdbc:mysql://aws.connect.psdb.cloud/xiaozhi-ai-toy?sslMode=REQUIRED
    # username: ${DB_USERNAME}
    # password: ${DB_PASSWORD}
    
    druid:
      driver-class-name: com.mysql.cj.jdbc.Driver
      initial-size: 5
      max-active: 20
      min-idle: 5
      max-wait: 60000
      time-between-eviction-runs-millis: 60000
      min-evictable-idle-time-millis: 300000
      validation-query: SELECT 1
      test-while-idle: true
      test-on-borrow: false
      test-on-return: false
      
  # Liquibase for migrations
  liquibase:
    enabled: true
    change-log: classpath:db/changelog/db.changelog-master.yaml
    
  # Redis for caching
  redis:
    host: localhost
    port: 6379
    password: 
    timeout: 2000ms
    lettuce:
      pool:
        max-active: 8
        max-idle: 8
        min-idle: 0

# MyBatis Plus configuration
mybatis-plus:
  mapper-locations: classpath*:/mapper/**/*.xml
  type-aliases-package: xiaozhi.modules.*.entity
  global-config:
    db-config:
      id-type: ASSIGN_ID
      logic-delete-value: 1
      logic-not-delete-value: 0
  configuration:
    map-underscore-to-camel-case: true
    cache-enabled: false
    call-setters-on-nulls: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl # Enable SQL logging in dev
```

### Environment Variables (.env):
```bash
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=xiaozhi_ai_toy
DB_USERNAME=xiaozhi_dev
DB_PASSWORD=your_secure_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Application
APP_ENV=development
APP_PORT=8002
```

## 5. DBeaver Connection Setup

### Steps to Connect:
1. Open DBeaver
2. Click "New Database Connection"
3. Select "MySQL"
4. Enter connection details:
   - Server Host: `localhost` (or your server IP)
   - Port: `3306`
   - Database: `xiaozhi_ai_toy`
   - Username: `xiaozhi_dev`
   - Password: Your password

5. Test Connection
6. Advanced Settings:
   - Set "serverTimezone" to "Asia/Shanghai" or your timezone
   - Enable "allowPublicKeyRetrieval" if needed

### Connection URL for DBeaver:
```
jdbc:mysql://localhost:3306/xiaozhi_ai_toy?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false
```

## 6. Testing Database Connection

### Java Test:
```java
@SpringBootTest
public class DatabaseConnectionTest {
    
    @Autowired
    private DataSource dataSource;
    
    @Test
    public void testConnection() throws SQLException {
        try (Connection conn = dataSource.getConnection()) {
            assertNotNull(conn);
            System.out.println("Database connected: " + conn.getMetaData().getURL());
        }
    }
}
```

### Python Test:
```python
import mysql.connector
from mysql.connector import Error

def test_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='xiaozhi_ai_toy',
            user='xiaozhi_dev',
            password='your_secure_password'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"Connected to MySQL: {version[0]}")
            
            # Test query
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"Tables: {[table[0] for table in tables]}")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

test_connection()
```

### Node.js Test:
```javascript
const mysql = require('mysql2/promise');

async function testConnection() {
    const connection = await mysql.createConnection({
        host: 'localhost',
        user: 'xiaozhi_dev',
        password: 'your_secure_password',
        database: 'xiaozhi_ai_toy'
    });
    
    const [rows] = await connection.execute('SELECT VERSION() as version');
    console.log('Connected to MySQL:', rows[0].version);
    
    const [tables] = await connection.execute('SHOW TABLES');
    console.log('Tables:', tables);
    
    await connection.end();
}

testConnection().catch(console.error);
```

## 7. Monitoring & Maintenance

### Database Health Check:
```sql
-- Check database size
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'xiaozhi_ai_toy'
GROUP BY table_schema;

-- Check table sizes
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)',
    table_rows AS 'Rows'
FROM information_schema.tables
WHERE table_schema = 'xiaozhi_ai_toy'
ORDER BY (data_length + index_length) DESC;

-- Check slow queries
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- Active connections
SHOW PROCESSLIST;

-- Connection pool status
SHOW STATUS LIKE 'Threads%';
```

### Backup Script:
```bash
#!/bin/bash
# backup.sh

DB_NAME="xiaozhi_ai_toy"
DB_USER="xiaozhi_dev"
DB_PASS="your_secure_password"
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/backup_$DATE.sql

# Delete old backups (keep 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### Automated Daily Analytics:
```sql
-- Create event for daily analytics generation
CREATE EVENT IF NOT EXISTS e_daily_analytics
ON SCHEDULE EVERY 1 DAY
STARTS '2025-01-15 02:00:00'
DO
    CALL sp_generate_daily_analytics(DATE_SUB(CURDATE(), INTERVAL 1 DAY));
```

## 8. Performance Optimization

### Query Optimization:
```sql
-- Add indexes for common queries
CREATE INDEX idx_chat_child_date 
ON chat_sessions(child_profile_id, session_start DESC);

CREATE INDEX idx_analytics_recent 
ON daily_analytics(analytics_date DESC, child_profile_id);

-- Partition large tables by date
ALTER TABLE chat_messages 
PARTITION BY RANGE (TO_DAYS(timestamp)) (
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p202503 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### Connection Pool Tuning:
```yaml
# Optimal settings for medium load
spring:
  datasource:
    druid:
      initial-size: 10      # Initial connections
      max-active: 50        # Maximum connections
      min-idle: 10          # Minimum idle connections
      max-wait: 30000       # Max wait time for connection (ms)
      time-between-eviction-runs-millis: 60000
      min-evictable-idle-time-millis: 300000
      max-evictable-idle-time-millis: 900000
      validation-query: SELECT 1
      test-while-idle: true
      test-on-borrow: false
      test-on-return: false
      pool-prepared-statements: true
      max-pool-prepared-statement-per-connection-size: 20
```

## 9. Troubleshooting

### Common Issues:

#### 1. Connection Refused
```bash
# Check if MySQL is running
sudo systemctl status mysql
# or
brew services list | grep mysql

# Check port
netstat -an | grep 3306
```

#### 2. Access Denied
```sql
-- Reset password
ALTER USER 'xiaozhi_dev'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

#### 3. Too Many Connections
```sql
-- Check max connections
SHOW VARIABLES LIKE 'max_connections';

-- Increase if needed
SET GLOBAL max_connections = 200;
```

#### 4. Slow Queries
```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- Analyze slow queries
SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 10;
```

## Next Steps

1. **Run the initialization script** to create your database schema
2. **Configure your application.yml** with the correct connection details
3. **Test the connection** using DBeaver or the provided test scripts
4. **Start collecting data** from your AI toy devices
5. **Implement the analytics pipeline** to process conversations
6. **Build the parent dashboard** to visualize the data

This setup gives you a production-ready MySQL database optimized for your parental analytics use case!