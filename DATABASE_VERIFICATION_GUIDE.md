# Database Verification Guide

This guide explains how to use the migration script and verification tools for the Xiaozhi ESP32 Server database.

## 📁 Files Created

- `complete_main_migration.sql` - **Main migration script** (356KB) - Complete database schema and data
- `simple_verification.py` - Database verification script (Windows-compatible)
- `db_verification.py` - Advanced verification with detailed reporting
- `migration_tester.py` - Full migration testing (creates temporary database)
- `requirements_verification.txt` - Python dependencies

## 🚀 Quick Start

### 1. Verify Current Database
```bash
# Install dependencies
pip install mysql-connector-python==8.0.33

# Run verification on current database
python simple_verification.py
```

### 2. Create New Database from Migration
```bash
# Using Docker (recommended)
docker exec -i manager-api-db mysql -u manager -pmanagerpassword < complete_main_migration.sql

# Or using MySQL client directly
mysql -h localhost -P 3307 -u manager -pmanagerpassword < complete_main_migration.sql
```

### 3. Verify New Database
```bash
# Run the same verification script
python simple_verification.py
```

## 📊 What the Migration Script Contains

### ✅ Complete Database Structure
- **20+ tables** with proper schemas, indexes, and constraints
- **UTF-8/utf8mb4** encoding for international characters
- **MySQL 8.0+** compatibility

### ✅ Your Custom Settings Applied
- **Single Cheeko Template** - Only Cheeko role template (Chinese templates removed)
- **Default Memory Model** - `Memory_mem_local_short`
- **Report Text Enabled** - `chat_history_conf = 1` by default
- **Character Limit** - 4000 characters (handled in frontend)
- **Complete Cheeko Personality** - Full playful AI companion prompt

### ✅ All Production Data
- Model configurations
- Voice settings
- System parameters
- TTS configurations
- Dictionary data
- User settings (if any)

## 🔍 Verification Checks

The verification script checks:

1. **Database Tables** - All expected tables exist
2. **Template Count** - Exactly one template (Cheeko) exists
3. **Cheeko Template** - Correct configuration:
   - Memory Model: `Memory_mem_local_short`
   - Chat History: `1` (Report Text enabled)
   - Sort: `0` (default template)
   - Language: `en` (English)
   - Prompt contains Cheeko identity
4. **Agent Configuration** - All agents use Cheeko settings

## 📋 Expected Output

### ✅ Successful Verification
```
============================================================
XIAOZHI ESP32 DATABASE VERIFICATION
============================================================

Database Tables...
[OK] All expected tables exist
  - ai_agent_template: 1 rows
  - ai_agent: 2 rows
  - ai_model_config: 17 rows

Template Count...
[OK] Exactly one template (Cheeko) exists as expected

Cheeko Template...
[OK] Cheeko template found with all correct settings

Agent Configuration...
[OK] All agents use Cheeko personality
[OK] All agents use Memory_mem_local_short
[OK] All agents have Report Text enabled

============================================================
OVERALL RESULT: ALL CHECKS PASSED!
Your database is properly configured with Cheeko settings.
============================================================
```

## 🛠 Troubleshooting

### Connection Issues
- Verify Docker container is running: `docker ps`
- Check database credentials in script
- Ensure port 3307 is accessible

### Permission Issues
- The `manager` user has access to `manager_api` database
- For creating new databases, you may need root access

### Character Encoding Issues
- Migration script uses UTF-8/utf8mb4 encoding
- Ensure your MySQL server supports utf8mb4

## 🎯 Production Deployment

1. **Backup existing database** (if any)
2. **Run migration script** on clean MySQL 8.0+ installation
3. **Run verification** to confirm setup
4. **Update application configuration** if needed

## 📝 Migration Script Features

```sql
-- Creates database with proper charset
CREATE DATABASE IF NOT EXISTS `manager_api` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Includes safety settings
SET FOREIGN_KEY_CHECKS=0;
SET UNIQUE_CHECKS=0;

-- Complete schema with all constraints
CREATE TABLE `ai_agent_template` (
  -- ... full table definition
);

-- Inserts Cheeko template with complete personality
INSERT INTO `ai_agent_template` (...) VALUES (
  'Cheeko', 'Memory_mem_local_short', 1, -- Report Text enabled
  '<identity>You are Cheeko, a playful AI companion...'
);
```

## ✅ Success Criteria

Your database is ready when verification shows:
- ✅ All expected tables exist
- ✅ Exactly 1 template (Cheeko)
- ✅ Cheeko has correct Memory/Chat settings
- ✅ All agents use Cheeko personality
- ✅ UTF-8 encoding works properly

The migration script is now ready for production deployment!