#!/usr/bin/env python3
"""
Script to clean up and repopulate model configurations with proper numeric IDs
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

def clean_existing_data(connection):
    """Clean up existing model configurations"""
    cursor = connection.cursor()
    
    try:
        # Clear model configurations
        cursor.execute("DELETE FROM ai_model_config")
        print(f"✓ Cleared {cursor.rowcount} existing model configurations")
        
        connection.commit()
    except Exception as e:
        print(f"Error cleaning data: {e}")
        connection.rollback()
    finally:
        cursor.close()

def main():
    print("=== Clean and Populate Models ===\n")
    
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
        
        # Step 1: Clean existing data
        print("1. Cleaning existing data...")
        clean_existing_data(connection)
        
        # Step 2: Run the populate script
        print("\n2. Running populate_models_database.py...")
        print("Please run: python populate_models_database.py")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\n✓ Database connection closed")

if __name__ == "__main__":
    main()