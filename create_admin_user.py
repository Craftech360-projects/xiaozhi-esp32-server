import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Database connection parameters from your connection URL
DB_CONFIG = {
    'host': 'caboose.proxy.rlwy.net',
    'port': 41629,
    'user': 'root',
    'password': 'IVIwxOEAWLTsPRfbhNKOmeCqVXdphTVV',
    'database': 'railway'
}

def create_admin_user():
    connection = None
    cursor = None
    
    try:
        # Connect to the database
        print("Connecting to Railway MySQL database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Check if admin user already exists
        check_query = "SELECT id, username, super_admin, status FROM sys_user WHERE username = 'admin'"
        cursor.execute(check_query)
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"\n❗ Admin user already exists!")
            print(f"   ID: {existing_user[0]}")
            print(f"   Username: {existing_user[1]}")
            print(f"   Super Admin: {'Yes' if existing_user[2] == 1 else 'No'}")
            print(f"   Status: {'Active' if existing_user[3] == 1 else 'Inactive'}")
            
            # Ask if user wants to update the password
            response = input("\nDo you want to reset the password to 'admin123'? (y/n): ")
            if response.lower() == 'y':
                update_query = """
                    UPDATE sys_user 
                    SET password = %s, 
                        super_admin = 1, 
                        status = 1,
                        update_date = %s
                    WHERE username = 'admin'
                """
                # BCrypt hash for 'admin123'
                bcrypt_password = '$2a$10$mG.gBdNuCBzJLMZ7LYaiiOoqL1V7rFJFgPcHKxrPKGZxK19lJ5/q6'
                cursor.execute(update_query, (bcrypt_password, datetime.now()))
                connection.commit()
                print("✅ Admin password has been reset to 'admin123'")
        else:
            # Create new admin user
            print("\n📝 Creating new admin user...")
            
            # First, check what's the next available ID
            cursor.execute("SELECT MAX(id) FROM sys_user")
            max_id = cursor.fetchone()[0]
            next_id = 1 if max_id is None else max_id + 1
            
            insert_query = """
                INSERT INTO sys_user (id, username, password, super_admin, status, create_date, creator)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # BCrypt hash for 'admin123'
            bcrypt_password = '$2a$10$mG.gBdNuCBzJLMZ7LYaiiOoqL1V7rFJFgPcHKxrPKGZxK19lJ5/q6'
            
            values = (
                next_id,
                'admin',
                bcrypt_password,
                1,  # super_admin = 1 (Yes)
                1,  # status = 1 (Active)
                datetime.now(),
                1   # creator = 1
            )
            
            cursor.execute(insert_query, values)
            connection.commit()
            
            print("✅ Admin user created successfully!")
        
        # Show all users
        print("\n📋 Current users in the system:")
        cursor.execute("SELECT id, username, super_admin, status, create_date FROM sys_user ORDER BY id")
        users = cursor.fetchall()
        
        if users:
            print(f"\n{'ID':<5} {'Username':<20} {'Super Admin':<12} {'Status':<10} {'Created':<20}")
            print("-" * 70)
            for user in users:
                super_admin = 'Yes' if user[2] == 1 else 'No'
                status = 'Active' if user[3] == 1 else 'Inactive'
                created = user[4].strftime('%Y-%m-%d %H:%M:%S') if user[4] else 'N/A'
                print(f"{user[0]:<5} {user[1]:<20} {super_admin:<12} {status:<10} {created:<20}")
        
        print("\n✅ You can now login with:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   URL: http://localhost:8001/")
        
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
    print("🚀 Admin User Creation Script for Xiaozhi ESP32 Server")
    print("=" * 50)
    create_admin_user()