#!/usr/bin/env python3
"""
Script to fix the ai_agent_template table structure
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

def get_existing_columns(connection, table_name):
    """Get existing columns in a table"""
    cursor = connection.cursor()
    try:
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = '{table_name}'
        """)
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()

def fix_agent_template_table(connection):
    """Fix the ai_agent_template table structure"""
    cursor = connection.cursor()
    
    try:
        existing_columns = get_existing_columns(connection, 'ai_agent_template')
        print(f"Existing columns: {', '.join(existing_columns)}")
        
        # Define the expected structure based on the migration file
        expected_columns = {
            'agent_code': "VARCHAR(36) COMMENT '智能体编码'",
            'agent_name': "VARCHAR(64) NOT NULL COMMENT '智能体名称'",
            'asr_model_id': "BIGINT COMMENT 'ASR模型ID'",
            'vad_model_id': "BIGINT COMMENT 'VAD模型ID'",
            'llm_model_id': "BIGINT COMMENT 'LLM模型ID'",
            'vllm_model_id': "BIGINT COMMENT 'VLLM模型ID'",
            'tts_model_id': "BIGINT COMMENT 'TTS模型ID'",
            'tts_voice_id': "VARCHAR(255) COMMENT 'TTS音色ID'",
            'mem_model_id': "BIGINT COMMENT '记忆模型ID'",
            'intent_model_id': "BIGINT COMMENT '意图识别模型ID'",
            'chat_history_conf': "INT DEFAULT 6 COMMENT '聊天历史配置'",
            'summary_memory': "TEXT COMMENT '总结记忆'",
            'lang_code': "VARCHAR(10) DEFAULT 'zh-CN' COMMENT '语言代码'",
            'language': "VARCHAR(50) DEFAULT '中文' COMMENT '语言名称'",
            'sort': "INT DEFAULT 0 COMMENT '排序'",
            'created_at': "DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'",
            'updated_at': "DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'",
            'updater': "BIGINT COMMENT '更新者'"
        }
        
        # Check if we need to rename template_name to agent_name
        if 'template_name' in existing_columns and 'agent_name' not in existing_columns:
            print("\nRenaming template_name to agent_name...")
            cursor.execute("ALTER TABLE ai_agent_template CHANGE COLUMN template_name agent_name VARCHAR(64) NOT NULL COMMENT '智能体名称'")
            print("✓ Renamed template_name to agent_name")
        
        # Add missing columns
        columns_added = 0
        for col_name, col_def in expected_columns.items():
            if col_name not in existing_columns and col_name != 'agent_name':  # Skip agent_name as we handled it above
                print(f"\nAdding column: {col_name}")
                try:
                    # Handle columns that should be added after specific columns
                    if col_name == 'agent_code':
                        cursor.execute(f"ALTER TABLE ai_agent_template ADD COLUMN {col_name} {col_def} AFTER id")
                    else:
                        cursor.execute(f"ALTER TABLE ai_agent_template ADD COLUMN {col_name} {col_def}")
                    columns_added += 1
                    print(f"✓ Added column: {col_name}")
                except mysql.connector.Error as e:
                    if "Duplicate column" in str(e):
                        print(f"⚠️  Column {col_name} already exists")
                    else:
                        print(f"✗ Error adding column {col_name}: {e}")
        
        # Update creator column if it exists but has wrong type
        if 'creator' in existing_columns:
            print("\nChecking creator column type...")
            cursor.execute("""
                SELECT DATA_TYPE 
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'ai_agent_template'
                AND column_name = 'creator'
            """)
            data_type = cursor.fetchone()[0]
            if data_type != 'bigint':
                print(f"Updating creator column from {data_type} to BIGINT...")
                cursor.execute("ALTER TABLE ai_agent_template MODIFY COLUMN creator BIGINT COMMENT '创建者'")
                print("✓ Updated creator column type")
        
        connection.commit()
        print(f"\n✓ Successfully updated table structure. Added {columns_added} columns.")
        
        # Now insert default data if table is empty
        cursor.execute("SELECT COUNT(*) FROM ai_agent_template")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\nInserting default template data...")
            try:
                # Insert a simple default template
                cursor.execute("""
                    INSERT INTO ai_agent_template 
                    (id, agent_code, agent_name, system_prompt, sort, creator)
                    VALUES 
                    ('default001', 'xiaozhi', '小智', '你是小智，一个友好的AI助手。', 0, 1)
                """)
                connection.commit()
                print("✓ Inserted default template")
            except mysql.connector.Error as e:
                print(f"✗ Error inserting default data: {e}")
                connection.rollback()
        
        return True
        
    except Exception as e:
        print(f"✗ Error fixing table: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def main():
    print("=== Agent Template Table Fix Tool ===\n")
    
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
        
        print("Analyzing ai_agent_template table structure...")
        
        if fix_agent_template_table(connection):
            print("\n✓ Table structure fixed successfully!")
            print("\nYou should now be able to access the Java backend without SQL errors.")
            print("The admin panel should work properly.")
        else:
            print("\n✗ Failed to fix table structure")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()