#!/usr/bin/env python3
"""
Script to check and fix database schema issues
"""
import mysql.connector
import yaml
import os
import re

def get_db_config():
    """Extract database configuration from Java application.yml"""
    manager_api_path = os.path.join(os.path.dirname(__file__), '..', 'manager-api')
    app_yml_path = os.path.join(manager_api_path, 'src', 'main', 'resources', 'application.yml')
    
    with open(app_yml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    datasource = config['spring']['datasource']
    url = datasource['url']
    match = re.match(r'jdbc:mysql://([^:]+):(\d+)/([^?]+)', url)
    
    return {
        'host': match.group(1),
        'port': int(match.group(2)),
        'database': match.group(3),
        'user': datasource['username'],
        'password': datasource['password']
    }

def check_liquibase_changelog(connection):
    """Check which migrations have been applied"""
    cursor = connection.cursor()
    
    try:
        # Check if DATABASECHANGELOG table exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'DATABASECHANGELOG'
        """)
        
        if cursor.fetchone()[0] == 0:
            print("✗ DATABASECHANGELOG table not found. Liquibase migrations not initialized.")
            return []
        
        # Get applied migrations
        cursor.execute("""
            SELECT ID, AUTHOR, FILENAME, DATEEXECUTED, EXECTYPE
            FROM DATABASECHANGELOG
            ORDER BY DATEEXECUTED
        """)
        
        applied = cursor.fetchall()
        print(f"\n✓ Found {len(applied)} applied migrations:")
        
        applied_ids = []
        for migration in applied[-10:]:  # Show last 10
            print(f"  - {migration[0]} by {migration[1]} ({migration[3]})")
            applied_ids.append(migration[0])
        
        if len(applied) > 10:
            print(f"  ... and {len(applied) - 10} more")
        
        return applied_ids
        
    finally:
        cursor.close()

def check_table_structure(connection, table_name):
    """Check if a table exists and show its structure"""
    cursor = connection.cursor()
    
    try:
        # Check if table exists
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = '{table_name}'
        """)
        
        if cursor.fetchone()[0] == 0:
            print(f"\n✗ Table {table_name} does not exist")
            return False
        
        # Get column information
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        print(f"\n✓ Table {table_name} structure:")
        
        has_agent_code = False
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) {col[4]}")
            if col[0] == 'agent_code':
                has_agent_code = True
        
        return has_agent_code
        
    finally:
        cursor.close()

def apply_missing_migration(connection, migration_file):
    """Apply a specific migration manually"""
    cursor = connection.cursor()
    
    try:
        manager_api_path = os.path.join(os.path.dirname(__file__), '..', 'manager-api')
        migration_path = os.path.join(manager_api_path, 'src', 'main', 'resources', 'db', 'changelog', migration_file)
        
        if not os.path.exists(migration_path):
            print(f"✗ Migration file not found: {migration_path}")
            return False
        
        print(f"\nApplying migration: {migration_file}")
        
        # Read SQL file
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Split by semicolons but be careful with stored procedures
        statements = []
        current = []
        in_delimiter = False
        
        for line in sql_content.split('\n'):
            if line.strip().upper().startswith('DELIMITER'):
                in_delimiter = not in_delimiter
                continue
            
            current.append(line)
            
            if not in_delimiter and line.strip().endswith(';'):
                statements.append('\n'.join(current))
                current = []
        
        if current:
            statements.append('\n'.join(current))
        
        # Execute each statement
        success_count = 0
        for i, statement in enumerate(statements):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                cursor.execute(statement)
                success_count += 1
            except mysql.connector.Error as e:
                if "already exists" in str(e) or "Duplicate" in str(e):
                    print(f"  ⚠️  Skipping (already exists): {statement[:50]}...")
                else:
                    print(f"  ✗ Error executing statement {i+1}: {e}")
                    print(f"     Statement: {statement[:100]}...")
        
        connection.commit()
        print(f"  ✓ Successfully executed {success_count} statements")
        
        # Record in DATABASECHANGELOG if table exists
        try:
            cursor.execute("""
                INSERT INTO DATABASECHANGELOG 
                (ID, AUTHOR, FILENAME, DATEEXECUTED, ORDEREXECUTED, EXECTYPE, MD5SUM, DESCRIPTION, COMMENTS, TAG, LIQUIBASE, CONTEXTS, LABELS, DEPLOYMENT_ID)
                VALUES (%s, %s, %s, NOW(), 
                    (SELECT COALESCE(MAX(ORDEREXECUTED), 0) + 1 FROM DATABASECHANGELOG AS dc2),
                    'EXECUTED', 'manual', 'manual fix', 'Applied manually to fix schema', NULL, '4.27.0', NULL, NULL, 'manual')
            """, (migration_file.replace('.sql', ''), 'manual', f'classpath:db/changelog/{migration_file}'))
            connection.commit()
            print(f"  ✓ Recorded migration in DATABASECHANGELOG")
        except:
            pass  # Ignore if DATABASECHANGELOG doesn't exist
        
        return True
        
    except Exception as e:
        print(f"✗ Error applying migration: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    print("=== Database Schema Fix Tool ===\n")
    
    db_config = get_db_config()
    
    try:
        print(f"Connecting to database at {db_config['host']}:{db_config['port']}/{db_config['database']}...")
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        print("✓ Connected successfully\n")
        
        # Check Liquibase changelog
        applied_migrations = check_liquibase_changelog(connection)
        
        # Check ai_agent_template table
        print("\nChecking ai_agent_template table...")
        has_agent_code = check_table_structure(connection, 'ai_agent_template')
        
        if not has_agent_code:
            print("\n⚠️  Missing agent_code column in ai_agent_template table")
            
            # Check if the migration that creates the table is applied
            if '202503141346' not in applied_migrations:
                print("\nThe migration that creates ai_agent_template table (202503141346.sql) has not been applied.")
                
                choice = input("\nDo you want to apply this migration manually? (y/n): ").lower()
                if choice == 'y':
                    if apply_missing_migration(connection, '202503141346.sql'):
                        print("\n✓ Migration applied successfully!")
                        
                        # Apply data initialization too
                        if '202504092335' not in applied_migrations:
                            print("\nApplying data initialization migration...")
                            apply_missing_migration(connection, '202504092335.sql')
                    else:
                        print("\n✗ Failed to apply migration")
            else:
                print("\n⚠️  Migration 202503141346 is marked as applied but table structure is wrong.")
                print("This might indicate a partial migration or manual table modification.")
                
                choice = input("\nDo you want to try re-applying the migration? (y/n): ").lower()
                if choice == 'y':
                    apply_missing_migration(connection, '202503141346.sql')
        else:
            print("\n✓ Table structure looks correct!")
        
        # Check other important tables
        print("\nChecking other important tables...")
        check_table_structure(connection, 'ai_agent')
        check_table_structure(connection, 'sys_user')
        check_table_structure(connection, 'sys_params')
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()