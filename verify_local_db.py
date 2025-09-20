import mysql.connector

def verify_database():
    try:
        # Connect to local Docker database
        connection = mysql.connector.connect(
            host='localhost',
            port=3307,
            user='manager',
            password='managerpassword',
            database='manager_api',
            charset='utf8mb4'
        )

        cursor = connection.cursor()

        print("Successfully connected to local database!")

        # Show all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"\nFound {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Check admin user
        cursor.execute("SELECT id, username, super_admin, status FROM sys_user WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if admin_user:
            print(f"\nAdmin user found: ID={admin_user[0]}, Username={admin_user[1]}, Super Admin={admin_user[2]}, Status={admin_user[3]}")
        else:
            print("\nAdmin user not found")

        # Show some sample data from key tables
        sample_tables = ['ai_model_provider', 'ai_model_config', 'sys_params']
        for table_name in sample_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"{table_name}: {count} records")
            except Exception as e:
                print(f"{table_name}: Table not found or error - {e}")

        cursor.close()
        connection.close()

        print("\nDatabase verification completed successfully!")
        print("\nYou can now run your manager-api server with the local profile:")
        print("   java -jar manager-api.jar --spring.profiles.active=local")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_database()