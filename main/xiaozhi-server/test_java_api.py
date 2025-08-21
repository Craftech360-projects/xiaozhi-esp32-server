#!/usr/bin/env python3
"""
Test script to debug Java API authentication
"""
import requests
import mysql.connector
import yaml
import os

def get_db_config():
    """Extract database configuration from Java application.yml"""
    manager_api_path = os.path.join(os.path.dirname(__file__), '..', 'manager-api')
    app_yml_path = os.path.join(manager_api_path, 'src', 'main', 'resources', 'application.yml')
    
    with open(app_yml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    datasource = config['spring']['datasource']
    
    # Parse the JDBC URL
    url = datasource['url']
    import re
    match = re.match(r'jdbc:mysql://([^:]+):(\d+)/([^?]+)', url)
    
    return {
        'host': match.group(1),
        'port': int(match.group(2)),
        'database': match.group(3),
        'user': datasource['username'],
        'password': datasource['password']
    }

def check_database_secret():
    """Check what's actually in the database"""
    db_config = get_db_config()
    
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        
        cursor = connection.cursor()
        
        # Check the sys_params table
        query = """
        SELECT param_code, param_value, value_type, update_date 
        FROM sys_params 
        WHERE param_code = 'server.secret'
        """
        cursor.execute(query)
        
        result = cursor.fetchone()
        if result:
            print(f"Database Record:")
            print(f"  param_code: {result[0]}")
            print(f"  param_value: {result[1]}")
            print(f"  value_type: {result[2]}")
            print(f"  update_date: {result[3]}")
            return result[1]
        else:
            print("No server.secret found in database!")
            return None
            
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def test_api_with_secret(secret):
    """Test the API with a specific secret"""
    url = "http://localhost:8002/xiaozhi/config/server-base"
    headers = {
        "Authorization": f"Bearer {secret}",
        "Content-Type": "application/json"
    }
    
    print(f"\nTesting API with secret: {secret}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.post(url, headers=headers, json={})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200 and response.json().get('code') == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_without_auth():
    """Test the API without authentication"""
    url = "http://localhost:8002/xiaozhi/config/server-base"
    
    print(f"\nTesting API without authentication")
    print(f"URL: {url}")
    
    try:
        response = requests.post(url, json={})
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("=== Java API Authentication Test ===\n")
    
    # 1. Check database
    print("1. Checking database for server.secret...")
    db_secret = check_database_secret()
    
    # 2. Test without auth
    print("\n2. Testing API without authentication...")
    test_without_auth()
    
    # 3. Test with database secret
    if db_secret:
        print(f"\n3. Testing API with database secret...")
        if test_api_with_secret(db_secret):
            print("\n✓ SUCCESS with database secret!")
        else:
            print("\n✗ FAILED with database secret")
    
    # 4. Test with some common values
    print("\n4. Testing with common values...")
    test_values = [
        "cheeko-secret-key-2025",
        "null",
        "",
        "your-server-secret"
    ]
    
    for test_secret in test_values:
        if test_api_with_secret(test_secret):
            print(f"\n✓ SUCCESS with secret: {test_secret}")
            break
    
    # 5. Check if Java backend has caching issues
    print("\n5. Checking for potential issues...")
    print("- The Java backend might be caching the secret value")
    print("- Try restarting the Java backend if the database secret doesn't work")
    print("- Check if Redis is caching the value")

if __name__ == "__main__":
    main()