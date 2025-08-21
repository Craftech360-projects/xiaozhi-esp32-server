#!/usr/bin/env python3
"""
Script to fix authentication issues by clearing Redis cache
"""
import redis
import yaml
import os
import sys
import mysql.connector
import re

def get_redis_config():
    """Extract Redis configuration from Java application.yml"""
    manager_api_path = os.path.join(os.path.dirname(__file__), '..', 'manager-api')
    app_yml_path = os.path.join(manager_api_path, 'src', 'main', 'resources', 'application.yml')
    
    with open(app_yml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    redis_config = config['spring']['redis']
    
    return {
        'host': redis_config['host'],
        'port': redis_config.get('port', 6379),
        'password': redis_config.get('password', None)
    }

def clear_redis_cache():
    """Clear the Redis cache for sys_params"""
    redis_config = get_redis_config()
    
    try:
        # Connect to Redis
        r = redis.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            password=redis_config['password'],
            decode_responses=True
        )
        
        # Test connection
        r.ping()
        print(f"Connected to Redis at {redis_config['host']}:{redis_config['port']}")
        
        # Clear the sys_params cache
        # Based on RedisKeys.getSysParamsKey() which likely returns "sys:params"
        keys_to_clear = ["sys:params", "xiaozhi:sys:params"]
        
        for key in keys_to_clear:
            if r.exists(key):
                # Get current value before deleting
                if r.type(key) == 'hash':
                    current_secret = r.hget(key, "server.secret")
                    if current_secret:
                        print(f"Current cached secret in {key}: {current_secret}")
                
                # Delete the key
                r.delete(key)
                print(f"Cleared Redis cache key: {key}")
            else:
                print(f"Redis key not found: {key}")
        
        return True
        
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        return False
    except Exception as e:
        print(f"Redis error: {e}")
        return False

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

def reset_server_secret():
    """Reset the server secret to a known value"""
    db_config = get_db_config()
    new_secret = "xiaozhi-server-2025"
    
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cursor = connection.cursor()
        
        # Update the server secret
        query = """
        UPDATE sys_params 
        SET param_value = %s, update_date = NOW() 
        WHERE param_code = 'server.secret'
        """
        cursor.execute(query, (new_secret,))
        connection.commit()
        
        print(f"Updated database server.secret to: {new_secret}")
        
        # Update the config file
        config_path = os.path.join(os.path.dirname(__file__), 'data', '.config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        config['manager-api']['secret'] = new_secret
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"Updated config file with new secret: {new_secret}")
        
        return True
        
    except Exception as e:
        print(f"Error updating secret: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    print("=== Authentication Fix Script ===\n")
    
    print("This script will:")
    print("1. Clear Redis cache for system parameters")
    print("2. Reset the server secret to a known value")
    print("3. Update your config file")
    print()
    
    choice = input("Continue? (y/n): ").lower()
    if choice != 'y':
        print("Aborted.")
        return
    
    # Try to clear Redis cache
    print("\n1. Attempting to clear Redis cache...")
    redis_cleared = clear_redis_cache()
    
    if not redis_cleared:
        print("\nWarning: Could not clear Redis cache. The Java backend might still use cached values.")
        print("You may need to restart the Java backend after running this script.")
    
    # Reset the server secret
    print("\n2. Resetting server secret...")
    if reset_server_secret():
        print("\n✓ Success! The server secret has been reset.")
        print("\nIMPORTANT: You must restart the Java backend for changes to take effect!")
        print("\nSteps to complete:")
        print("1. Stop the Java backend (Ctrl+C)")
        print("2. Start it again: mvn spring-boot:run")
        print("3. Run: python app.py")
    else:
        print("\n✗ Failed to reset server secret")

if __name__ == "__main__":
    main()