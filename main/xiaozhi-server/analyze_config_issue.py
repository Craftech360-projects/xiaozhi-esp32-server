#!/usr/bin/env python3
"""
Script to analyze configuration issue and find proper fix
"""
import mysql.connector
import yaml
import json
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
    print("=== Analyzing Configuration Issue ===\n")
    
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
        
        # 1. Check sys_params table structure
        print("1. Checking sys_params table structure:")
        cursor.execute("""
            DESCRIBE sys_params
        """)
        columns = cursor.fetchall()
        print("   Columns in sys_params:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]})")
        
        # 2. Check all parameters
        print("\n2. All parameters in sys_params:")
        cursor.execute("""
            SELECT param_code, param_value, param_type, value_type
            FROM sys_params
            ORDER BY param_code
        """)
        
        params = cursor.fetchall()
        for code, value, ptype, vtype in params:
            value_preview = value[:60] + '...' if len(value) > 60 else value
            print(f"   {code}: {value_preview} (type={ptype}, vtype={vtype})")
        
        # 3. Check if there's a cache table
        print("\n3. Checking for cache-related tables:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND (table_name LIKE '%cache%' OR table_name LIKE '%redis%')
        """)
        cache_tables = cursor.fetchall()
        if cache_tables:
            for table in cache_tables:
                print(f"   Found cache table: {table[0]}")
        else:
            print("   No cache tables found")
        
        # 4. Check agent template configuration
        print("\n4. Checking agent template configuration:")
        cursor.execute("""
            SELECT id, agent_name, system_prompt, 
                   vad_model_id, asr_model_id, llm_model_id, 
                   tts_model_id, mem_model_id, intent_model_id
            FROM ai_agent_template
            WHERE is_default = 1
            LIMIT 1
        """)
        
        template = cursor.fetchone()
        if template:
            print(f"   Default template: {template[1]}")
            print(f"   System prompt: {template[2][:50]}..." if template[2] else "   System prompt: None")
            print(f"   Model IDs: VAD={template[3]}, ASR={template[4]}, LLM={template[5]}, TTS={template[6]}, Memory={template[7]}, Intent={template[8]}")
        
        # 5. Check model configurations
        print("\n5. Checking model configurations:")
        cursor.execute("""
            SELECT id, model_type, model_code, config_json
            FROM ai_model_config
            WHERE id IN (1,2,3,4,5,6)
            ORDER BY id
        """)
        
        models = cursor.fetchall()
        for model_id, model_type, model_code, config_json in models:
            print(f"   ID {model_id} ({model_type}): {model_code}")
            if config_json:
                try:
                    config = json.loads(config_json)
                    print(f"     Config: {json.dumps(config, indent=6)[:100]}...")
                except:
                    print(f"     Config: Invalid JSON")
        
        # 6. Check for OTA URL with wrong IP
        print("\n6. Checking for wrong IP in parameters:")
        cursor.execute("""
            SELECT param_code, param_value
            FROM sys_params
            WHERE param_value LIKE '%192.168.1.239%'
        """)
        
        wrong_ip_params = cursor.fetchall()
        if wrong_ip_params:
            print("   ❌ Found parameters with wrong IP:")
            for code, value in wrong_ip_params:
                print(f"      {code}: {value}")
        else:
            print("   ✓ No parameters with wrong IP found")
        
        # 7. Update wrong IP if found
        cursor.execute("""
            UPDATE sys_params
            SET param_value = REPLACE(param_value, '192.168.1.239', '192.168.1.105')
            WHERE param_value LIKE '%192.168.1.239%'
        """)
        if cursor.rowcount > 0:
            print(f"\n   ✓ Fixed {cursor.rowcount} parameters with wrong IP")
            connection.commit()
        
        print("\n7. Checking if Java backend reads these parameters:")
        print("   The Java backend should be reading from sys_params table")
        print("   but it seems to be returning cached or hardcoded values.")
        
        print("\n8. Suggested fixes:")
        print("   a) Clear Redis cache if enabled")
        print("   b) Check if Java backend has @Cacheable annotations")
        print("   c) Restart Java backend with cache disabled")
        print("   d) Check ConfigServiceImpl.buildConfigFromParams() method")
        
        cursor.close()
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()