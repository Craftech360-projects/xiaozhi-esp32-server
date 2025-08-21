#!/usr/bin/env python3
"""
Script to check and fix configuration parameters in database
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
    print("=== Check and Fix Configuration Parameters ===\n")
    
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
        
        # List all parameters
        print("Current parameters in database:")
        cursor.execute("""
            SELECT param_code, param_value, value_type, remark
            FROM sys_params 
            ORDER BY param_code
        """)
        
        params = cursor.fetchall()
        for code, value, vtype, remark in params:
            # Map value_type integer to string for display
            vtype_str = {1: 'string', 2: 'number', 3: 'boolean'}.get(vtype, str(vtype))
            print(f"  {code}: {value[:50]}... ({vtype_str})")
            if '192.168.1.239' in value:
                print(f"    ^ Contains wrong IP!")
        
        # Check for missing required parameters
        print("\n\nChecking for required parameters...")
        
        # value_type mapping: 1=string, 2=number, 3=boolean, etc.
        required_params = [
            ('log.log_level', 'DEBUG', 1, '日志级别'),
            ('server.ota.url', 'http://192.168.1.105:8003/xiaozhi/ota/', 1, 'OTA服务器地址'),
            ('xiaozhi.prompt', 'You are a helpful AI assistant', 1, '默认提示词'),
            ('xiaozhi.llm_model_id', '3', 1, '默认LLM模型ID'),
            ('xiaozhi.tts_model_id', '4', 1, '默认TTS模型ID'),
            ('xiaozhi.vad_model_id', '1', 1, '默认VAD模型ID'),
            ('xiaozhi.asr_model_id', '2', 1, '默认ASR模型ID'),
            ('xiaozhi.memory_model_id', '5', 1, '默认内存模型ID'),
            ('xiaozhi.intent_model_id', '6', 1, '默认意图模型ID')
        ]
        
        for param_code, default_value, value_type, remark in required_params:
            cursor.execute("""
                SELECT id, param_value FROM sys_params WHERE param_code = %s
            """, (param_code,))
            
            result = cursor.fetchone()
            
            if result:
                param_id, current_value = result
                # Fix wrong IP if found
                if '192.168.1.239' in current_value:
                    new_value = current_value.replace('192.168.1.239', '192.168.1.105')
                    cursor.execute("""
                        UPDATE sys_params 
                        SET param_value = %s, update_date = NOW()
                        WHERE id = %s
                    """, (new_value, param_id))
                    print(f"✓ Fixed IP in {param_code}")
            else:
                # Create missing parameter
                cursor.execute("""
                    INSERT INTO sys_params (param_code, param_value, param_type, value_type, remark, creator, create_date)
                    VALUES (%s, %s, 1, %s, %s, 1, NOW())
                """, (param_code, default_value, value_type, remark))
                print(f"✓ Created missing parameter: {param_code}")
        
        connection.commit()
        
        print("\n✓ Configuration parameters fixed!")
        print("\nVerifying all parameters...")
        
        # Show updated parameters
        cursor.execute("""
            SELECT param_code, param_value 
            FROM sys_params 
            WHERE param_code LIKE 'log.%' 
               OR param_code LIKE 'server.%'
               OR param_code LIKE 'xiaozhi.%'
            ORDER BY param_code
        """)
        
        print("\nUpdated configuration parameters:")
        for code, value in cursor.fetchall():
            print(f"  {code}: {value}")
        
        cursor.close()
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()