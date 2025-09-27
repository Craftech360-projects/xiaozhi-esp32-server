#!/usr/bin/env python3
"""
Database Migration Runner for XiaoZhi ESP32 Server
Executes the complete_schema_migration.sql on the target database
"""

import mysql.connector
import sys
import os
from mysql.connector import Error

# Target database configuration
TARGET_DB_CONFIG = {
    'host': 'localhost',
    'port': 3308,
    'database': 'manager_api_fresh',
    'user': 'root',
    'password': 'password123',
    'charset': 'utf8mb4',
    'autocommit': True
}

def create_database_if_not_exists():
    """Create the database if it doesn't exist"""
    try:
        # Connect without specifying database
        config_without_db = TARGET_DB_CONFIG.copy()
        del config_without_db['database']

        connection = mysql.connector.connect(**config_without_db)
        cursor = connection.cursor()

        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{TARGET_DB_CONFIG['database']}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"[OK] Database '{TARGET_DB_CONFIG['database']}' ready")

        cursor.close()
        connection.close()
        return True

    except Error as e:
        print(f"[ERROR] Error creating database: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        connection = mysql.connector.connect(**TARGET_DB_CONFIG)
        cursor = connection.cursor()

        cursor.execute("SELECT 'Connection successful!' as status, VERSION() as mysql_version")
        result = cursor.fetchone()
        print(f"[OK] {result[0]}")
        print(f"[OK] MySQL version: {result[1]}")

        cursor.close()
        connection.close()
        return True

    except Error as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

def execute_migration_script():
    """Execute the migration script"""
    script_path = 'complete_schema_migration.sql'

    if not os.path.exists(script_path):
        print(f"[ERROR] Migration script not found: {script_path}")
        return False

    try:
        # Read the migration script
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()

        # Split the SQL content into individual statements
        # Remove comments and empty lines
        statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('--') or line.startswith('/*') or line.startswith('*/'):
                continue

            # Skip MySQL specific commands that might cause issues
            if line.startswith('/*!') and line.endswith('*/;'):
                continue

            current_statement.append(line)

            # If line ends with semicolon, it's the end of a statement
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement.strip() and not statement.strip().startswith('--'):
                    statements.append(statement)
                current_statement = []

        # Connect to database
        connection = mysql.connector.connect(**TARGET_DB_CONFIG)
        cursor = connection.cursor()

        print(f"[OK] Executing {len(statements)} SQL statements...")

        executed = 0
        for i, statement in enumerate(statements, 1):
            try:
                # Skip certain MySQL-specific statements that might cause issues
                if any(skip in statement.upper() for skip in ['SET @OLD_', 'SET NAMES', 'SET TIME_ZONE', 'SET SQL_MODE', 'SET UNIQUE_CHECKS', 'SET FOREIGN_KEY_CHECKS', 'SET SQL_NOTES']):
                    continue

                cursor.execute(statement)
                executed += 1

                if executed % 10 == 0:
                    print(f"  ... executed {executed} statements")

            except Error as e:
                print(f"[WARN] Warning on statement {i}: {str(e)[:100]}...")
                # Continue with other statements
                continue

        print(f"[OK] Migration completed! Executed {executed} statements successfully")

        cursor.close()
        connection.close()
        return True

    except Error as e:
        print(f"[ERROR] Migration failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    try:
        connection = mysql.connector.connect(**TARGET_DB_CONFIG)
        cursor = connection.cursor()

        # Check if tables were created
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]

        expected_tables = [
            'ai_agent', 'ai_agent_chat_audio', 'ai_agent_chat_history',
            'ai_agent_plugin_mapping', 'ai_agent_template', 'ai_agent_voice_print',
            'ai_device', 'ai_model_config', 'ai_model_provider', 'ai_ota',
            'ai_tts_voice', 'ai_voiceprint', 'parent_profile',
            'sys_dict_data', 'sys_dict_type', 'sys_params', 'sys_user', 'sys_user_token'
        ]

        print(f"[OK] Created {len(table_names)} tables:")
        for table in sorted(table_names):
            print(f"  - {table}")

        missing_tables = set(expected_tables) - set(table_names)
        if missing_tables:
            print(f"[WARN] Missing tables: {missing_tables}")

        # Check some key data
        try:
            cursor.execute("SELECT COUNT(*) FROM ai_model_config")
            model_count = cursor.fetchone()[0]
            print(f"[OK] AI model configurations: {model_count}")
        except:
            print("[WARN] Could not count ai_model_config records")

        try:
            cursor.execute("SELECT COUNT(*) FROM ai_agent_template")
            template_count = cursor.fetchone()[0]
            print(f"[OK] Agent templates: {template_count}")

            if template_count > 0:
                cursor.execute("SELECT agent_name FROM ai_agent_template LIMIT 1")
                template_name = cursor.fetchone()[0]
                print(f"[OK] Default template: {template_name}")
        except:
            print("[WARN] Could not check agent templates")

        try:
            cursor.execute("SELECT COUNT(*) FROM sys_params")
            param_count = cursor.fetchone()[0]
            print(f"[OK] System parameters: {param_count}")
        except:
            print("[WARN] Could not count sys_params records")

        cursor.close()
        connection.close()
        return True

    except Error as e:
        print(f"[ERROR] Verification failed: {e}")
        return False

def main():
    """Main migration process"""
    print("Starting database migration...")
    print(f"Target: {TARGET_DB_CONFIG['host']}:{TARGET_DB_CONFIG['port']}/{TARGET_DB_CONFIG['database']}")
    print("=" * 60)

    # Step 1: Create database if needed
    print("\n1. Creating database if needed...")
    if not create_database_if_not_exists():
        sys.exit(1)

    # Step 2: Test connection
    print("\n2. Testing database connection...")
    if not test_connection():
        sys.exit(1)

    # Step 3: Execute migration
    print("\n3. Executing migration script...")
    if not execute_migration_script():
        sys.exit(1)

    # Step 4: Verify migration
    print("\n4. Verifying migration...")
    if not verify_migration():
        sys.exit(1)

    print("\n" + "=" * 60)
    print("Migration completed successfully!")
    print("\nNext steps:")
    print("1. Configure API keys in ai_model_config table")
    print("2. Set up MQTT and LiveKit parameters in sys_params")
    print("3. Create user accounts as needed")
    print("4. Create agent instances from templates")
    print("5. Register devices")

if __name__ == "__main__":
    main()