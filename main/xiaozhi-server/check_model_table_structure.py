#!/usr/bin/env python3
"""
Script to check the actual structure of model-related tables
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

def check_table_structure(connection, table_name):
    """Check the structure of a table"""
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
        for col in columns:
            print(f"  - {col[0]} ({col[1]}) {col[4] if col[4] else ''}")
        
        return True
        
    finally:
        cursor.close()

def check_sample_data(connection, table_name, limit=3):
    """Check sample data from a table"""
    cursor = connection.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        if rows:
            # Get column names
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = [row[0] for row in cursor.fetchall()]
            
            print(f"\nSample data from {table_name}:")
            for i, row in enumerate(rows):
                print(f"\nRow {i+1}:")
                for j, col in enumerate(columns):
                    value = row[j]
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    print(f"  {col}: {value}")
        else:
            print(f"\nNo data found in {table_name}")
            
    except Exception as e:
        print(f"Error reading data: {e}")
    finally:
        cursor.close()

def main():
    print("=== Database Structure Check ===\n")
    
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
        
        # Check model-related tables
        tables_to_check = [
            'ai_model_config',
            'ai_model_provider',
            'ai_agent_template',
            'ai_agent'
        ]
        
        for table in tables_to_check:
            if check_table_structure(connection, table):
                check_sample_data(connection, table)
        
        # Check if there are VAD/ASR models in the model provider table
        print("\n\nChecking model providers...")
        cursor = connection.cursor()
        cursor.execute("""
            SELECT model_type, COUNT(*) as count 
            FROM ai_model_provider 
            GROUP BY model_type
        """)
        
        print("\nModel counts by type:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        cursor.close()
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()