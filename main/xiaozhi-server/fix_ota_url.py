#!/usr/bin/env python3
"""
Script to fix OTA URL in database parameters
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
    print("=== Fix OTA URL Tool ===\n")
    
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
        
        # Check if server.ota.url parameter exists
        cursor.execute("""
            SELECT id, param_code, param_value 
            FROM sys_params 
            WHERE param_code = 'server.ota.url'
        """)
        
        result = cursor.fetchone()
        
        if result:
            # Update existing parameter
            param_id, param_code, current_value = result
            print(f"Found existing OTA URL: {current_value}")
            
            if '192.168.1.239' in current_value:
                new_value = current_value.replace('192.168.1.239', '192.168.1.105')
                cursor.execute("""
                    UPDATE sys_params 
                    SET param_value = %s, update_date = NOW()
                    WHERE id = %s
                """, (new_value, param_id))
                print(f"✓ Updated OTA URL to: {new_value}")
            else:
                print("OTA URL doesn't contain 192.168.1.239")
        else:
            # Create new parameter
            print("OTA URL parameter not found, creating new one...")
            cursor.execute("""
                INSERT INTO sys_params (param_code, param_value, param_type, value_type, remark, creator, create_date)
                VALUES ('server.ota.url', 'http://192.168.1.105:8003/xiaozhi/ota/', 1, 'string', 'OTA服务器地址', 1, NOW())
            """)
            print("✓ Created OTA URL parameter")
        
        connection.commit()
        cursor.close()
        
        print("\n✓ OTA URL fixed successfully!")
        print("\nNext step: Restart the Java backend to apply changes")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()