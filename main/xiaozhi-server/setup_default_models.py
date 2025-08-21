#!/usr/bin/env python3
"""
Script to set up default models in the database for the Java backend
"""
import mysql.connector
import yaml
import os
import re
import uuid
from datetime import datetime

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

def setup_default_models(connection):
    """Set up default model configurations"""
    cursor = connection.cursor()
    
    try:
        # Check if we have any model configurations
        cursor.execute("SELECT COUNT(*) FROM ai_model_config")
        model_count = cursor.fetchone()[0]
        
        print(f"Current model configurations: {model_count}")
        
        # Insert default models if none exist
        if model_count == 0:
            print("\nInserting default model configurations...")
            
            # Default model configurations
            default_models = [
                # VAD Model
                {
                    'model_name': 'SileroVAD',
                    'model_code': 'VAD_SileroVAD',
                    'model_type': 'VAD',
                    'config_json': {
                        'type': 'silero',
                        'model_dir': 'models/snakers4_silero-vad',
                        'threshold': 0.5,
                        'min_silence_duration_ms': 700
                    }
                },
                # ASR Model
                {
                    'model_name': 'FunASR',
                    'model_code': 'ASR_FunASR',
                    'model_type': 'ASR',
                    'config_json': {
                        'type': 'fun_local',
                        'model_dir': 'models/SenseVoiceSmall',
                        'output_dir': 'tmp/'
                    }
                },
                # LLM Model
                {
                    'model_name': 'ChatGLM',
                    'model_code': 'LLM_ChatGLM',
                    'model_type': 'LLM',
                    'config_json': {
                        'type': 'openai',
                        'model_name': 'glm-4-flash',
                        'url': 'https://open.bigmodel.cn/api/paas/v4/',
                        'api_key': 'your-api-key'
                    }
                },
                # TTS Model
                {
                    'model_name': 'EdgeTTS',
                    'model_code': 'TTS_EdgeTTS',
                    'model_type': 'TTS',
                    'config_json': {
                        'type': 'edge',
                        'voice': 'zh-CN-XiaoxiaoNeural',
                        'output_dir': 'tmp/'
                    }
                },
                # Memory Model
                {
                    'model_name': 'NoMemory',
                    'model_code': 'Memory_nomem',
                    'model_type': 'Memory',
                    'config_json': {
                        'type': 'nomem'
                    }
                },
                # Intent Model
                {
                    'model_name': 'FunctionCall',
                    'model_code': 'Intent_function_call',
                    'model_type': 'Intent',
                    'config_json': {
                        'type': 'function_call',
                        'functions': ['play_music', 'get_weather']
                    }
                }
            ]
            
            for model in default_models:
                cursor.execute("""
                    INSERT INTO ai_model_config 
                    (id, model_name, model_code, model_type, config_json, is_active, creator, create_date)
                    VALUES (%s, %s, %s, %s, %s, 1, 1, NOW())
                """, (
                    str(uuid.uuid4()).replace('-', ''),
                    model['model_name'],
                    model['model_code'],
                    model['model_type'],
                    str(model['config_json'])
                ))
            
            connection.commit()
            print(f"✓ Inserted {len(default_models)} default models")
        
        # Get model IDs
        model_ids = {}
        cursor.execute("""
            SELECT id, model_type FROM ai_model_config 
            WHERE is_active = 1
        """)
        for row in cursor.fetchall():
            model_ids[row[1]] = row[0]
        
        # Check default agent template
        cursor.execute("""
            SELECT id, agent_code, agent_name, vad_model_id, asr_model_id, 
                   llm_model_id, tts_model_id, mem_model_id, intent_model_id
            FROM ai_agent_template
            ORDER BY sort ASC
            LIMIT 1
        """)
        
        template = cursor.fetchone()
        if not template:
            print("\nNo default agent template found. Creating one...")
            
            cursor.execute("""
                INSERT INTO ai_agent_template 
                (id, agent_code, agent_name, system_prompt, 
                 vad_model_id, asr_model_id, llm_model_id, tts_model_id, 
                 mem_model_id, intent_model_id, sort, creator, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 1, NOW())
            """, (
                'default001',
                'xiaozhi',
                '小智',
                '你是小智，一个友好的AI助手。',
                model_ids.get('VAD'),
                model_ids.get('ASR'),
                model_ids.get('LLM'),
                model_ids.get('TTS'),
                model_ids.get('Memory'),
                model_ids.get('Intent')
            ))
            
            connection.commit()
            print("✓ Created default agent template")
        else:
            # Update template if any model IDs are missing
            update_needed = False
            updates = []
            
            if not template[3]:  # vad_model_id
                updates.append(f"vad_model_id = '{model_ids.get('VAD')}'")
                update_needed = True
            if not template[4]:  # asr_model_id
                updates.append(f"asr_model_id = '{model_ids.get('ASR')}'")
                update_needed = True
            if not template[5]:  # llm_model_id
                updates.append(f"llm_model_id = '{model_ids.get('LLM')}'")
                update_needed = True
            if not template[6]:  # tts_model_id
                updates.append(f"tts_model_id = '{model_ids.get('TTS')}'")
                update_needed = True
            if not template[7]:  # mem_model_id
                updates.append(f"mem_model_id = '{model_ids.get('Memory')}'")
                update_needed = True
            if not template[8]:  # intent_model_id
                updates.append(f"intent_model_id = '{model_ids.get('Intent')}'")
                update_needed = True
            
            if update_needed:
                print(f"\nUpdating default agent template with missing model IDs...")
                update_sql = f"UPDATE ai_agent_template SET {', '.join(updates)} WHERE id = '{template[0]}'"
                cursor.execute(update_sql)
                connection.commit()
                print("✓ Updated default agent template")
            else:
                print("\n✓ Default agent template already has all model IDs")
        
        # Display current configuration
        cursor.execute("""
            SELECT agent_name, vad_model_id, asr_model_id, llm_model_id, 
                   tts_model_id, mem_model_id, intent_model_id
            FROM ai_agent_template
            ORDER BY sort ASC
            LIMIT 1
        """)
        
        template = cursor.fetchone()
        if template:
            print(f"\nDefault Agent Template:")
            print(f"  Name: {template[0]}")
            print(f"  VAD Model ID: {template[1]}")
            print(f"  ASR Model ID: {template[2]}")
            print(f"  LLM Model ID: {template[3]}")
            print(f"  TTS Model ID: {template[4]}")
            print(f"  Memory Model ID: {template[5]}")
            print(f"  Intent Model ID: {template[6]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    print("=== Default Models Setup Tool ===\n")
    
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
        
        if setup_default_models(connection):
            print("\n✓ Default models setup completed!")
            print("\nNext steps:")
            print("1. Rebuild the Java backend: mvn clean compile")
            print("2. Restart the Java backend: mvn spring-boot:run")
            print("3. Run the Python server: python app.py")
        else:
            print("\n✗ Setup failed")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()