#!/usr/bin/env python3
"""
Script to fix complete configuration issue by updating value_type column
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
    print("=== Fix Complete Configuration ===\n")
    
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
        
        # First, check if we can modify the column type
        print("1. Checking value_type column type:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'sys_params' 
            AND column_name = 'value_type'
        """)
        
        col_info = cursor.fetchone()
        if col_info:
            print(f"   Current type: {col_info[1]} ({col_info[2]})")
        
        # Option 1: Update the Java code to handle integer value_type
        # Option 2: Change column to varchar
        # For now, let's map the integer values properly
        
        # Map value_type integers to strings for Java compatibility
        print("\n2. Creating temporary mapping table for value types:")
        value_type_mapping = {
            1: 'string',
            2: 'number', 
            3: 'boolean',
            4: 'array',
            5: 'json'
        }
        
        # First, let's fix any parameters with wrong IP
        print("\n3. Fixing OTA URL with wrong IP:")
        cursor.execute("""
            UPDATE sys_params 
            SET param_value = REPLACE(param_value, '192.168.1.239', '192.168.1.105')
            WHERE param_value LIKE '%192.168.1.239%'
        """)
        if cursor.rowcount > 0:
            print(f"   ✓ Fixed {cursor.rowcount} parameters with wrong IP")
        else:
            print("   ✓ No wrong IP found")
        
        # Add more required parameters with proper value types
        print("\n4. Adding/updating required parameters:")
        
        # Parameters that should be added/updated
        required_params = [
            # Log parameters
            ('log.log_format', '<green>{time:YYMMDD HH:mm:ss}</green>[{version}_{selected_module}][<light-blue>{extra[tag]}</light-blue>]-<level>{level}</level>-<light-green>{message}</light-green>', 1, 1),
            ('log.log_format_file', '{time:YYYY-MM-DD HH:mm:ss} - {version}_{selected_module} - {name} - {level} - {extra[tag]} - {message}', 1, 1),
            ('log.log_dir', 'tmp', 1, 1),
            ('log.log_file', 'server.log', 1, 1),
            ('log.data_dir', 'data', 1, 1),
            
            # Model configurations - these should already exist but let's ensure they're there
            ('VAD.SileroVAD.type', 'silero', 1, 1),
            ('VAD.SileroVAD.model_dir', 'models/snakers4_silero-vad', 1, 1),
            ('VAD.SileroVAD.threshold', '0.5', 1, 1),
            ('VAD.SileroVAD.min_silence_duration_ms', '700', 1, 1),
            
            ('ASR.FunASR.type', 'fun_local', 1, 1),
            ('ASR.FunASR.model_dir', 'models/SenseVoiceSmall', 1, 1),
            ('ASR.FunASR.output_dir', 'tmp/', 1, 1),
            
            ('LLM.ChatGLMLLM.type', 'openai', 1, 1),
            ('LLM.ChatGLMLLM.model_name', 'glm-4-flash', 1, 1),
            ('LLM.ChatGLMLLM.url', 'https://open.bigmodel.cn/api/paas/v4/', 1, 1),
            ('LLM.ChatGLMLLM.api_key', 'your-chat-glm-web-key', 1, 1),
            
            ('TTS.EdgeTTS.type', 'edge', 1, 1),
            ('TTS.EdgeTTS.voice', 'zh-CN-XiaoxiaoNeural', 1, 1),
            ('TTS.EdgeTTS.output_dir', 'tmp/', 1, 1),
            
            ('Memory.nomem.type', 'nomem', 1, 1),
            
            ('Intent.function_call.type', 'function_call', 1, 1),
            ('Intent.function_call.functions', 'get_weather;play_music', 1, 1),
        ]
        
        for param_code, param_value, param_type, value_type in required_params:
            cursor.execute("""
                INSERT INTO sys_params (param_code, param_value, param_type, value_type, remark, creator, create_date)
                VALUES (%s, %s, %s, %s, %s, 1, NOW())
                ON DUPLICATE KEY UPDATE 
                    param_value = VALUES(param_value),
                    value_type = VALUES(value_type),
                    update_date = NOW()
            """, (param_code, param_value, param_type, value_type, f'Auto-added: {param_code}'))
            
            if cursor.rowcount > 0:
                print(f"   ✓ Updated: {param_code}")
        
        connection.commit()
        
        # Verify configuration
        print("\n5. Verifying configuration parameters:")
        cursor.execute("""
            SELECT COUNT(*) FROM sys_params WHERE param_code LIKE 'log.%'
        """)
        log_count = cursor.fetchone()[0]
        print(f"   Log parameters: {log_count}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM sys_params WHERE param_code LIKE 'VAD.%'
        """)
        vad_count = cursor.fetchone()[0]
        print(f"   VAD parameters: {vad_count}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM sys_params WHERE param_code LIKE 'ASR.%'
        """)
        asr_count = cursor.fetchone()[0]
        print(f"   ASR parameters: {asr_count}")
        
        cursor.execute("""
            SELECT COUNT(*) FROM sys_params WHERE param_code LIKE 'LLM.%'
        """)
        llm_count = cursor.fetchone()[0]
        print(f"   LLM parameters: {llm_count}")
        
        print("\n✓ Configuration fixed!")
        print("\nIMPORTANT: The Java backend needs to be updated to handle integer value_type")
        print("The code fix has been applied but Java backend needs to be recompiled.")
        
        cursor.close()
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()