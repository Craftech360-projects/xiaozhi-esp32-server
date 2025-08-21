#!/usr/bin/env python3
"""
Script to fix value_type mapping issue
Since the Java code expects strings but database has integers,
we'll update the database to match what Java expects
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

def main():
    print("=== Fix Value Type Mapping ===\n")
    
    db_config = get_db_config()
    
    try:
        print(f"Connecting to database...")
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        print("✓ Connected successfully\n")
        
        cursor = connection.cursor()
        
        # First, let's alter the column to varchar to match Java expectations
        print("1. Checking if we can alter value_type column to varchar:")
        try:
            cursor.execute("""
                ALTER TABLE sys_params 
                MODIFY COLUMN value_type VARCHAR(20) DEFAULT 'string'
            """)
            connection.commit()
            print("   ✓ Column altered to VARCHAR(20)")
        except mysql.connector.Error as e:
            if "Duplicate" in str(e):
                print("   ℹ Column already VARCHAR")
            else:
                print(f"   ✗ Error altering column: {e}")
                # Continue anyway
        
        # Now update all value_type values
        print("\n2. Updating value_type values based on parameter patterns:")
        
        # Update numeric parameters
        numeric_params = [
            'threshold', 'model_id', 'port', 'timeout', 'max_retries',
            'retry_delay', 'min_silence_duration_ms', 'sample_rate',
            'channels', 'frame_duration'
        ]
        
        for param in numeric_params:
            cursor.execute("""
                UPDATE sys_params 
                SET value_type = 'number' 
                WHERE param_code LIKE %s
            """, (f'%{param}%',))
            if cursor.rowcount > 0:
                print(f"   ✓ Updated {cursor.rowcount} '{param}' parameters to number")
        
        # Update boolean parameters
        boolean_params = [
            'allow_user_register', 'enable_mobile_register', 
            'enabled', 'use_speaker_boost'
        ]
        
        for param in boolean_params:
            cursor.execute("""
                UPDATE sys_params 
                SET value_type = 'boolean' 
                WHERE param_code LIKE %s
            """, (f'%{param}%',))
            if cursor.rowcount > 0:
                print(f"   ✓ Updated {cursor.rowcount} '{param}' parameters to boolean")
        
        # Update array parameters
        cursor.execute("""
            UPDATE sys_params 
            SET value_type = 'array' 
            WHERE param_code LIKE '%functions%'
        """)
        if cursor.rowcount > 0:
            print(f"   ✓ Updated {cursor.rowcount} function parameters to array")
        
        # The rest remain as string (default)
        
        connection.commit()
        
        # Verify the updates
        print("\n3. Verifying value_type distribution:")
        cursor.execute("""
            SELECT value_type, COUNT(*) as count 
            FROM sys_params 
            GROUP BY value_type
        """)
        
        for vtype, count in cursor.fetchall():
            print(f"   {vtype}: {count} parameters")
        
        # Show some examples
        print("\n4. Sample parameters with their types:")
        cursor.execute("""
            SELECT param_code, value_type, param_value 
            FROM sys_params 
            WHERE value_type != 'string' 
            LIMIT 10
        """)
        
        for code, vtype, value in cursor.fetchall():
            print(f"   {code} ({vtype}): {value[:50]}...")
        
        print("\n✓ Value types fixed!")
        print("\nNext step: Recompile and restart the Java backend")
        
        cursor.close()
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()