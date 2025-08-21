import mysql.connector
from mysql.connector import Error
from datetime import datetime
import bcrypt

# Database connection parameters
DB_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 41629,
    'user': 'root',
    'password': 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
    'database': 'railway'
}

def generate_bcrypt_hash(password):
    """Generate a BCrypt hash for the given password"""
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=10)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    hashed_str = hashed.decode('utf-8')
    
    # Convert $2b$ to $2a$ for Java compatibility
    if hashed_str.startswith('$2b$'):
        hashed_str = '$2a$' + hashed_str[4:]
        print(f"   Converted $2b$ to $2a$ for Java compatibility")
    
    return hashed_str

def update_admin_password():
    connection = None
    cursor = None
    
    try:
        # Connect to the database
        print("Connecting to Railway MySQL database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Generate new BCrypt hash for 'admin123'
        new_password = 'admin123'
        new_hash = generate_bcrypt_hash(new_password)
        
        print(f"\n📝 Generated new BCrypt hash for '{new_password}':")
        print(f"   Hash: {new_hash}")
        
        # Update admin password
        update_query = """
            UPDATE sys_user 
            SET password = %s,
                update_date = %s
            WHERE username = 'admin'
        """
        
        cursor.execute(update_query, (new_hash, datetime.now()))
        rows_affected = cursor.rowcount
        
        if rows_affected > 0:
            connection.commit()
            print(f"\n✅ Successfully updated password for admin user")
            print(f"   Rows affected: {rows_affected}")
        else:
            print(f"\n❌ No admin user found to update")
        
        # Verify the update
        cursor.execute("SELECT id, username, password FROM sys_user WHERE username = 'admin'")
        result = cursor.fetchone()
        
        if result:
            print(f"\n📋 Admin user details after update:")
            print(f"   ID: {result[0]}")
            print(f"   Username: {result[1]}")
            print(f"   Password Hash: {result[2][:20]}... (truncated)")
        
        print(f"\n✅ You can now login with:")
        print(f"   Username: admin")
        print(f"   Password: {new_password}")
        
    except Error as e:
        print(f"\n❌ Error: {e}")
        if connection and connection.is_connected():
            connection.rollback()
    
    finally:
        # Close connections
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("\n🔌 Database connection closed.")

if __name__ == "__main__":
    print("🚀 Admin Password Update Script")
    print("=" * 50)
    
    # Check if bcrypt is installed
    try:
        import bcrypt
    except ImportError:
        print("❌ bcrypt module not found. Please install it:")
        print("   pip install bcrypt")
        exit(1)
    
    update_admin_password()