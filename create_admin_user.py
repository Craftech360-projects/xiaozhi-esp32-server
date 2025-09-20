import mysql.connector
import bcrypt

def create_admin_user():
    """Create admin user with correct credentials: admin / Admin@123"""

    # Generate BCrypt hash for "Admin@123"
    password = "Admin@123"
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    password_hash = hashed.decode('utf-8')

    print(f"Generated password hash for 'Admin@123': {password_hash}")

    # Connect to local database
    try:
        connection = mysql.connector.connect(
            host='localhost',
            port=3307,
            user='manager',
            password='managerpassword',
            database='manager_api',
            charset='utf8mb4'
        )

        cursor = connection.cursor()
        print("Connected to local database successfully!")

        # Delete existing admin user if exists
        cursor.execute("DELETE FROM sys_user WHERE username = 'admin'")

        # Insert new admin user with correct credentials
        insert_sql = """
        INSERT INTO sys_user (id, username, password, super_admin, status, create_date, creator)
        VALUES (%s, %s, %s, %s, %s, NOW(), %s)
        """

        cursor.execute(insert_sql, (1, 'admin', password_hash, 1, 1, 1))
        connection.commit()

        print("Admin user created successfully!")

        # Verify the user was created
        cursor.execute("SELECT id, username, super_admin, status FROM sys_user WHERE username = 'admin'")
        result = cursor.fetchone()

        if result:
            print(f"Verification: ID={result[0]}, Username={result[1]}, Super Admin={result[2]}, Status={result[3]}")

        cursor.close()
        connection.close()

        print("\nAdmin login credentials:")
        print("Username: admin")
        print("Password: Admin@123")

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_admin_user()