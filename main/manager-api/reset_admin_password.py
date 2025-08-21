#!/usr/bin/env python3
"""
Script to reset admin password in the database
"""
import mysql.connector
import yaml
import re
import bcrypt
import sys

def get_db_config():
    """Extract database configuration from application.yml"""
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_yml_path = os.path.join(script_dir, 'src', 'main', 'resources', 'application.yml')
    
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

def generate_bcrypt_password(plain_password):
    """Generate BCrypt hash for password"""
    # BCrypt with default rounds (10)
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def reset_admin_password(new_password):
    """Reset the admin password in database"""
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
        
        # Generate BCrypt hash
        hashed_password = generate_bcrypt_password(new_password)
        
        # Update admin password
        update_query = """
        UPDATE sys_user 
        SET password = %s, update_date = NOW() 
        WHERE username = 'admin'
        """
        cursor.execute(update_query, (hashed_password,))
        connection.commit()
        
        if cursor.rowcount > 0:
            print(f"✓ Successfully reset admin password")
            print(f"  Username: admin")
            print(f"  Password: {new_password}")
            print(f"  Hash: {hashed_password[:20]}...")
            return True
        else:
            print("✗ Admin user not found in database")
            return False
            
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def check_existing_admin():
    """Check existing admin user details"""
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
        
        # Check admin user
        query = """
        SELECT username, password, status, super_admin, create_date 
        FROM sys_user 
        WHERE username = 'admin'
        """
        cursor.execute(query)
        
        result = cursor.fetchone()
        if result:
            print("Current admin user details:")
            print(f"  Username: {result[0]}")
            print(f"  Password hash: {result[1][:20]}..." if result[1] else "  Password: NULL")
            print(f"  Status: {'Active' if result[2] == 1 else 'Inactive'}")
            print(f"  Super admin: {'Yes' if result[3] == 1 else 'No'}")
            print(f"  Created: {result[4]}")
            return True
        else:
            print("No admin user found in database")
            return False
            
    except Exception as e:
        print(f"Database error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def main():
    print("=== Admin Password Reset Tool ===\n")
    
    # First check existing admin
    print("Checking existing admin user...")
    if not check_existing_admin():
        print("\nNo admin user found. Please create one through the web interface.")
        return
    
    print("\nThis tool will reset the admin password.")
    print("Make sure you have pip installed: bcrypt")
    print("If not, run: pip install bcrypt mysql-connector-python pyyaml")
    
    # Get new password
    new_password = input("\nEnter new password for admin (or press Enter for 'admin123'): ").strip()
    if not new_password:
        new_password = "admin123"
    
    print(f"\nResetting admin password to: {new_password}")
    confirm = input("Continue? (y/n): ").lower()
    
    if confirm == 'y':
        if reset_admin_password(new_password):
            print("\n✓ Password reset successful!")
            print("\nYou can now login with:")
            print(f"  Username: admin")
            print(f"  Password: {new_password}")
        else:
            print("\n✗ Password reset failed!")
    else:
        print("\nCancelled.")

if __name__ == "__main__":
    main()