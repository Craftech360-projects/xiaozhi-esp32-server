#!/usr/bin/env python3
"""
XiaoZhi ESP32 Server - Migration Script Generator
Extracts complete schema from main database with essential configuration data only
"""

import mysql.connector
import re
import sys
from datetime import datetime

# Main database configuration
MAIN_DB_CONFIG = {
    'host': 'localhost',
    'port': 3307,
    'user': 'manager',
    'password': 'managerpassword',
    'database': 'manager_api',
    'charset': 'utf8mb4'
}

def sanitize_api_key(value):
    """Replace API keys with placeholders"""
    if not value:
        return value

    # Replace common API key patterns
    if re.match(r'^gsk_[a-zA-Z0-9]+', value):
        return 'YOUR_GROQ_API_KEY'
    elif re.match(r'^sk-[a-zA-Z0-9]+', value):
        return 'YOUR_OPENAI_API_KEY'
    elif re.match(r'^m0-[a-zA-Z0-9]+', value):
        return 'YOUR_MEM0_API_KEY'
    elif 'key' in value.lower() and len(value) > 20:
        return 'YOUR_API_KEY'

    return value

def get_table_schema(cursor, table_name):
    """Get CREATE TABLE statement for a table"""
    cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
    result = cursor.fetchone()
    return result[1] if result else None

def get_essential_data(cursor, table_name):
    """Get essential configuration data for specific tables"""

    # Tables to include data from (configuration only, no user/device/agent data)
    config_tables = {
        'sys_params': 'SELECT * FROM sys_params',
        'sys_dict_type': 'SELECT * FROM sys_dict_type',
        'sys_dict_data': 'SELECT * FROM sys_dict_data',
        'ai_model_config': 'SELECT * FROM ai_model_config',
        'ai_model_provider': 'SELECT * FROM ai_model_provider',
        'ai_tts_voice': 'SELECT * FROM ai_tts_voice WHERE is_default = 1 LIMIT 5',  # Only default voices
        'ai_agent_template': 'SELECT * FROM ai_agent_template WHERE agent_name = "Cheeko"'  # Only Cheeko template
    }

    if table_name not in config_tables:
        return []

    try:
        cursor.execute(config_tables[table_name])
        return cursor.fetchall()
    except Exception as e:
        print(f"Warning: Could not fetch data from {table_name}: {e}")
        return []

def generate_insert_statements(cursor, table_name, data):
    """Generate INSERT statements for table data"""
    if not data:
        return []

    # Get column information
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = [col[0] for col in cursor.fetchall()]

    statements = []
    statements.append(f"-- Data for table `{table_name}`")
    statements.append(f"LOCK TABLES `{table_name}` WRITE;")
    statements.append(f"/*!40000 ALTER TABLE `{table_name}` DISABLE KEYS */;")

    # Build INSERT statement
    values_list = []
    for row in data:
        sanitized_row = []
        for i, value in enumerate(row):
            if value is None:
                sanitized_row.append('NULL')
            elif isinstance(value, str):
                # Sanitize API keys and escape quotes
                sanitized_value = sanitize_api_key(value)
                sanitized_value = sanitized_value.replace("'", "\\'").replace('"', '\\"')
                sanitized_row.append(f"'{sanitized_value}'")
            elif isinstance(value, (int, float)):
                sanitized_row.append(str(value))
            else:
                # Handle other types (datetime, etc.)
                sanitized_row.append(f"'{str(value)}'")

        values_list.append(f"({','.join(sanitized_row)})")

    if values_list:
        column_names = ','.join([f'`{col}`' for col in columns])
        insert_sql = f"INSERT INTO `{table_name}` ({column_names}) VALUES\n" + ',\n'.join(values_list) + ";"
        statements.append(insert_sql)

    statements.append(f"/*!40000 ALTER TABLE `{table_name}` ENABLE KEYS */;")
    statements.append(f"UNLOCK TABLES;")
    statements.append("")

    return statements

def create_migration_script():
    """Create complete migration script"""
    print("Connecting to main database...")

    try:
        conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        cursor = conn.cursor()

        print(f"Connected to {MAIN_DB_CONFIG['database']} successfully!")

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Found {len(tables)} tables")

        migration_script = []

        # Header
        migration_script.extend([
            "-- ===================================================================",
            "-- XIAOZHI ESP32 SERVER - COMPLETE SCHEMA MIGRATION SCRIPT",
            "-- ===================================================================",
            "-- This script creates the complete database schema with essential",
            "-- configuration data only (NO user accounts, agents, or devices)",
            "-- Compatible with MySQL 8.0+",
            f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "--",
            "-- FEATURES:",
            "-- - Complete database schema (all tables and indexes)",
            "-- - Essential system configuration data only",
            "-- - Cheeko agent template included",
            "-- - Default TTS voices included",
            "-- - All API keys replaced with placeholders",
            "-- - NO user accounts, agents, devices, or personal data",
            "-- ===================================================================",
            "",
            "-- MySQL compatibility settings",
            "/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;",
            "/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;",
            "/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;",
            "/*!50503 SET NAMES utf8mb4 */;",
            "/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;",
            "/*!40103 SET TIME_ZONE='+00:00' */;",
            "/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;",
            "/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;",
            "/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;",
            "/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;",
            "",
            "-- Create database if not exists",
            "-- CREATE DATABASE IF NOT EXISTS `manager_api_fresh` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            "-- USE `manager_api_fresh`;",
            ""
        ])

        # Generate schema for all tables
        for table in sorted(tables):
            print(f"Processing table: {table}")

            migration_script.append(f"--")
            migration_script.append(f"-- Table structure for table `{table}`")
            migration_script.append(f"--")
            migration_script.append("")

            # Get table schema
            schema = get_table_schema(cursor, table)
            if schema:
                migration_script.append(f"DROP TABLE IF EXISTS `{table}`;")
                migration_script.append("/*!40101 SET @saved_cs_client     = @@character_set_client */;")
                migration_script.append("/*!50503 SET character_set_client = utf8mb4 */;")
                migration_script.append(schema + ";")
                migration_script.append("/*!40101 SET character_set_client = @saved_cs_client */;")
                migration_script.append("")

        # Add essential data for configuration tables
        config_tables = ['sys_dict_type', 'sys_dict_data', 'sys_params', 'ai_model_provider', 'ai_model_config', 'ai_tts_voice', 'ai_agent_template']

        for table in config_tables:
            if table in tables:
                print(f"Adding essential data for: {table}")
                data = get_essential_data(cursor, table)
                if data:
                    migration_script.append(f"--")
                    migration_script.append(f"-- Dumping data for table `{table}`")
                    migration_script.append(f"--")
                    migration_script.append("")

                    insert_statements = generate_insert_statements(cursor, table, data)
                    migration_script.extend(insert_statements)

        # Footer
        migration_script.extend([
            "-- Restore MySQL settings",
            "/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;",
            "/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;",
            "/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;",
            "/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;",
            "/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;",
            "/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;",
            "/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;",
            "/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;",
            "",
            "-- Migration completed successfully!",
            "-- Next steps:",
            "-- 1. Configure API keys in ai_model_config table",
            "-- 2. Set up SMS parameters in sys_params if needed",
            "-- 3. Create user accounts as needed",
            "-- 4. Create agent instances from templates",
            "-- 5. Register devices"
        ])

        # Write migration script to file
        script_content = '\n'.join(migration_script)

        with open('complete_schema_migration.sql', 'w', encoding='utf-8') as f:
            f.write(script_content)

        print(f"\nMigration script created successfully!")
        print(f"File: complete_schema_migration.sql")
        print(f"Size: {len(script_content)} characters")
        print(f"Tables: {len(tables)}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"Error creating migration script: {e}")
        return False

if __name__ == "__main__":
    create_migration_script()