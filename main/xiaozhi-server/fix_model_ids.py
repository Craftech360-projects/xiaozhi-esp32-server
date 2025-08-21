#!/usr/bin/env python3
"""
Script to fix model IDs - use numeric IDs instead of UUIDs
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

def recreate_models_with_numeric_ids(connection):
    """Recreate model configurations with numeric IDs"""
    cursor = connection.cursor()
    
    try:
        # First, clear existing data
        print("Clearing existing model configurations...")
        cursor.execute("DELETE FROM ai_model_config")
        connection.commit()
        
        # Create models with numeric IDs
        configs = [
            # VAD Configuration
            {
                'id': 1,
                'model_type': 'VAD',
                'model_code': 'VAD_SileroVAD',
                'model_name': 'SileroVAD',
                'is_default': 1,
                'config_json': {
                    'type': 'silero',
                    'model_dir': 'models/snakers4_silero-vad',
                    'threshold': 0.5,
                    'min_silence_duration_ms': 700
                }
            },
            # ASR Configuration
            {
                'id': 2,
                'model_type': 'ASR',
                'model_code': 'ASR_FunASR',
                'model_name': 'FunASR',
                'is_default': 1,
                'config_json': {
                    'type': 'fun_local',
                    'model_dir': 'models/SenseVoiceSmall',
                    'output_dir': 'tmp/'
                }
            },
            # LLM Configuration
            {
                'id': 3,
                'model_type': 'LLM',
                'model_code': 'ChatGLMLLM',
                'model_name': 'ChatGLM',
                'is_default': 1,
                'config_json': {
                    'type': 'openai',
                    'model_name': 'glm-4-flash',
                    'url': 'https://open.bigmodel.cn/api/paas/v4/',
                    'api_key': 'your-chat-glm-web-key'
                }
            },
            # TTS Configuration
            {
                'id': 4,
                'model_type': 'TTS',
                'model_code': 'EdgeTTS',
                'model_name': 'EdgeTTS',
                'is_default': 1,
                'config_json': {
                    'type': 'edge',
                    'voice': 'zh-CN-XiaoxiaoNeural',
                    'output_dir': 'tmp/'
                }
            },
            # Memory Configuration
            {
                'id': 5,
                'model_type': 'Memory',
                'model_code': 'nomem',
                'model_name': 'NoMemory',
                'is_default': 1,
                'config_json': {
                    'type': 'nomem'
                }
            },
            # Intent Configuration
            {
                'id': 6,
                'model_type': 'Intent',
                'model_code': 'function_call',
                'model_name': 'FunctionCall',
                'is_default': 1,
                'config_json': {
                    'type': 'function_call',
                    'functions': ['get_weather', 'play_music']
                }
            }
        ]
        
        model_ids = {}
        
        for i, config in enumerate(configs):
            cursor.execute("""
                INSERT INTO ai_model_config 
                (id, model_type, model_code, model_name, is_default, is_enabled, 
                 config_json, sort, creator, create_date)
                VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 1, NOW())
            """, (
                str(config['id']),  # Convert to string since id column is varchar
                config['model_type'],
                config['model_code'],
                config['model_name'],
                config['is_default'],
                json.dumps(config['config_json']),
                i
            ))
            model_ids[config['model_type']] = config['id']
        
        connection.commit()
        print(f"✓ Created {len(configs)} model configurations with numeric IDs")
        
        # Now update agent templates
        print("\nUpdating agent templates...")
        cursor.execute("""
            UPDATE ai_agent_template
            SET 
                vad_model_id = %s,
                asr_model_id = %s,
                llm_model_id = %s,
                tts_model_id = %s,
                mem_model_id = %s,
                intent_model_id = %s,
                agent_code = CASE 
                    WHEN agent_code IS NULL THEN CONCAT('agent_', id)
                    ELSE agent_code 
                END,
                updated_at = NOW()
            WHERE 
                vad_model_id IS NULL OR
                asr_model_id IS NULL OR
                llm_model_id IS NULL OR
                tts_model_id IS NULL OR
                mem_model_id IS NULL OR
                intent_model_id IS NULL
        """, (
            model_ids.get('VAD'),      # 1
            model_ids.get('ASR'),      # 2
            model_ids.get('LLM'),      # 3
            model_ids.get('TTS'),      # 4
            model_ids.get('Memory'),   # 5
            model_ids.get('Intent')    # 6
        ))
        
        connection.commit()
        print(f"✓ Updated {cursor.rowcount} agent templates")
        
        # Verify the update
        cursor.execute("""
            SELECT id, agent_name, agent_code, vad_model_id, asr_model_id, 
                   llm_model_id, tts_model_id, mem_model_id, intent_model_id
            FROM ai_agent_template
            ORDER BY sort ASC
            LIMIT 3
        """)
        
        templates = cursor.fetchall()
        print("\n✓ Agent Templates Updated:")
        for template in templates:
            print(f"\n  Template ID: {template[0]}")
            print(f"  Name: {template[1]}")
            print(f"  Code: {template[2]}")
            print(f"  VAD Model ID: {template[3]}")
            print(f"  ASR Model ID: {template[4]}")
            print(f"  LLM Model ID: {template[5]}")
            print(f"  TTS Model ID: {template[6]}")
            print(f"  Memory Model ID: {template[7]}")
            print(f"  Intent Model ID: {template[8]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    print("=== Fix Model IDs Tool ===\n")
    
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
        
        if recreate_models_with_numeric_ids(connection):
            print("\n✓ Successfully fixed model IDs!")
            print("\nNext steps:")
            print("1. Restart the Java backend")
            print("2. Test the Python server again")
        else:
            print("\n✗ Failed to fix model IDs")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()