#!/usr/bin/env python3
"""
Script to populate the database with model configurations and providers
"""
import mysql.connector
import yaml
import json
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

def populate_model_providers(connection):
    """Populate model providers table"""
    cursor = connection.cursor()
    
    providers = [
        # VAD Providers
        {
            'model_type': 'VAD',
            'provider_code': 'silero',
            'name': 'SileroVAD',
            'fields': json.dumps([
                {'name': 'type', 'type': 'string', 'required': True, 'default': 'silero'},
                {'name': 'model_dir', 'type': 'string', 'required': True},
                {'name': 'threshold', 'type': 'number', 'required': False, 'default': 0.5},
                {'name': 'min_silence_duration_ms', 'type': 'number', 'required': False, 'default': 700}
            ])
        },
        # ASR Providers
        {
            'model_type': 'ASR',
            'provider_code': 'fun_local',
            'name': 'FunASR',
            'fields': json.dumps([
                {'name': 'type', 'type': 'string', 'required': True, 'default': 'fun_local'},
                {'name': 'model_dir', 'type': 'string', 'required': True},
                {'name': 'output_dir', 'type': 'string', 'required': True}
            ])
        },
        # LLM Providers
        {
            'model_type': 'LLM',
            'provider_code': 'openai',
            'name': 'OpenAI Compatible',
            'fields': json.dumps([
                {'name': 'type', 'type': 'string', 'required': True, 'default': 'openai'},
                {'name': 'model_name', 'type': 'string', 'required': True},
                {'name': 'api_key', 'type': 'string', 'required': True},
                {'name': 'base_url', 'type': 'string', 'required': False},
                {'name': 'url', 'type': 'string', 'required': False}
            ])
        },
        # TTS Providers
        {
            'model_type': 'TTS',
            'provider_code': 'edge',
            'name': 'EdgeTTS',
            'fields': json.dumps([
                {'name': 'type', 'type': 'string', 'required': True, 'default': 'edge'},
                {'name': 'voice', 'type': 'string', 'required': True},
                {'name': 'output_dir', 'type': 'string', 'required': True}
            ])
        },
        # Memory Providers
        {
            'model_type': 'Memory',
            'provider_code': 'nomem',
            'name': 'NoMemory',
            'fields': json.dumps([
                {'name': 'type', 'type': 'string', 'required': True, 'default': 'nomem'}
            ])
        },
        # Intent Providers
        {
            'model_type': 'Intent',
            'provider_code': 'function_call',
            'name': 'FunctionCall',
            'fields': json.dumps([
                {'name': 'type', 'type': 'string', 'required': True, 'default': 'function_call'},
                {'name': 'functions', 'type': 'array', 'required': False}
            ])
        }
    ]
    
    for i, provider in enumerate(providers):
        try:
            cursor.execute("""
                INSERT INTO ai_model_provider 
                (id, model_type, provider_code, name, fields, sort, creator, create_date)
                VALUES (%s, %s, %s, %s, %s, %s, 1, NOW())
            """, (
                str(uuid.uuid4()).replace('-', ''),
                provider['model_type'],
                provider['provider_code'],
                provider['name'],
                provider['fields'],
                i
            ))
        except mysql.connector.IntegrityError:
            print(f"Provider {provider['name']} already exists, skipping...")
    
    connection.commit()
    return cursor.rowcount

def populate_model_configs(connection):
    """Populate model configurations table"""
    cursor = connection.cursor()
    
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
        model_id = str(config['id'])  # Convert numeric ID to string for varchar column
        model_ids[config['model_type']] = config['id']  # Store numeric ID for bigint foreign keys
        
        try:
            cursor.execute("""
                INSERT INTO ai_model_config 
                (id, model_type, model_code, model_name, is_default, is_enabled, 
                 config_json, sort, creator, create_date)
                VALUES (%s, %s, %s, %s, %s, 1, %s, %s, 1, NOW())
            """, (
                model_id,
                config['model_type'],
                config['model_code'],
                config['model_name'],
                config['is_default'],
                json.dumps(config['config_json']),
                i
            ))
        except mysql.connector.IntegrityError:
            print(f"Config {config['model_name']} already exists, skipping...")
            # Get existing ID
            cursor.execute("""
                SELECT id FROM ai_model_config 
                WHERE model_code = %s
            """, (config['model_code'],))
            result = cursor.fetchone()
            if result:
                # Convert string ID to int for bigint compatibility
                try:
                    model_ids[config['model_type']] = int(result[0])
                except ValueError:
                    model_ids[config['model_type']] = config['id']
    
    connection.commit()
    return model_ids

def update_agent_templates(connection, model_ids):
    """Update agent templates with model IDs"""
    cursor = connection.cursor()
    
    # Update all templates that have NULL model IDs
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
        model_ids.get('VAD'),
        model_ids.get('ASR'),
        model_ids.get('LLM'),
        model_ids.get('TTS'),
        model_ids.get('Memory'),
        model_ids.get('Intent')
    ))
    
    connection.commit()
    return cursor.rowcount

def main():
    print("=== Database Population Tool ===\n")
    
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
        
        # Step 1: Populate model providers
        print("1. Populating model providers...")
        providers_added = populate_model_providers(connection)
        print(f"   ✓ Model providers populated")
        
        # Step 2: Populate model configurations
        print("\n2. Populating model configurations...")
        model_ids = populate_model_configs(connection)
        print(f"   ✓ Model configurations populated")
        print(f"   Model IDs: {model_ids}")
        
        # Step 3: Update agent templates
        print("\n3. Updating agent templates with model IDs...")
        templates_updated = update_agent_templates(connection, model_ids)
        print(f"   ✓ Updated {templates_updated} agent templates")
        
        # Verify the update
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, agent_name, vad_model_id, asr_model_id, 
                   llm_model_id, tts_model_id, mem_model_id, intent_model_id
            FROM ai_agent_template
            ORDER BY sort ASC
            LIMIT 1
        """)
        
        template = cursor.fetchone()
        if template:
            print(f"\n✓ Default Agent Template Updated:")
            print(f"  ID: {template[0]}")
            print(f"  Name: {template[1]}")
            print(f"  VAD Model: {template[2]}")
            print(f"  ASR Model: {template[3]}")
            print(f"  LLM Model: {template[4]}")
            print(f"  TTS Model: {template[5]}")
            print(f"  Memory Model: {template[6]}")
            print(f"  Intent Model: {template[7]}")
        
        cursor.close()
        
        print("\n✓ Database population completed!")
        print("\nNext steps:")
        print("1. Restart the Java backend to clear any caches")
        print("2. Test the Python server again")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()