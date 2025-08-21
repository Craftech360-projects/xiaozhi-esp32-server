#!/usr/bin/env python3
"""
Script to fetch the server secret from MySQL database and update the config file
"""
import mysql.connector
import yaml
import os
import sys

def get_db_config():
    """Extract database configuration from Java application.yml"""
    manager_api_path = os.path.join(os.path.dirname(__file__), '..', 'manager-api')
    app_yml_path = os.path.join(manager_api_path, 'src', 'main', 'resources', 'application.yml')
    
    with open(app_yml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    datasource = config['spring']['datasource']
    
    # Parse the JDBC URL
    url = datasource['url']
    # Extract host, port, and database from jdbc:mysql://host:port/database?params
    import re
    match = re.match(r'jdbc:mysql://([^:]+):(\d+)/([^?]+)', url)
    if not match:
        raise ValueError(f"Cannot parse database URL: {url}")
    
    return {
        'host': match.group(1),
        'port': int(match.group(2)),
        'database': match.group(3),
        'user': datasource['username'],
        'password': datasource['password']
    }

def get_server_secret(db_config):
    """Fetch the server secret from the database"""
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cursor = connection.cursor()
        
        # Query for the server secret
        query = "SELECT param_value FROM sys_params WHERE param_code = 'server.secret'"
        cursor.execute(query)
        
        result = cursor.fetchone()
        if result and result[0] and result[0] != 'null':
            return result[0]
        else:
            print("Warning: Server secret not found or is 'null' in database")
            return None
            
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def update_config_file(secret):
    """Update the .config.yaml file with the new secret"""
    config_path = os.path.join(os.path.dirname(__file__), 'data', '.config.yaml')
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        return False
    
    # Read the current config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Update the secret
    if 'manager-api' not in config:
        config['manager-api'] = {}
    
    old_secret = config['manager-api'].get('secret', 'not set')
    config['manager-api']['secret'] = secret
    
    # Write back the updated config
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"Config file updated successfully!")
    print(f"Old secret: {old_secret}")
    print(f"New secret: {secret}")
    return True

def main():
    print("=== Server Secret Update Script ===\n")
    
    try:
        # Step 1: Get database configuration
        print("1. Reading database configuration from application.yml...")
        db_config = get_db_config()
        print(f"   Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # Step 2: Fetch server secret from database
        print("\n2. Fetching server secret from database...")
        secret = get_server_secret(db_config)
        
        if not secret:
            print("\nERROR: Could not fetch server secret from database.")
            print("\nPossible solutions:")
            print("1. Ensure the Java backend has been started at least once")
            print("2. Check database connectivity")
            print("3. Manually check the sys_params table in the database")
            sys.exit(1)
        
        print(f"   Found secret: {secret}")
        
        # Step 3: Update config file
        print("\n3. Updating config file...")
        if update_config_file(secret):
            print("\n✓ Success! The server secret has been updated.")
            print("\nYou can now run: python app.py")
        else:
            print("\n✗ Failed to update config file")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()