import mysql.connector

def run_clean_migration():
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
        print("Connected to local database!")

        # Read and execute clean migration script
        with open('clean_migration.sql', 'r', encoding='utf-8') as f:
            migration_script = f.read()

        # Split and execute statements
        statements = [stmt.strip() for stmt in migration_script.split(';') if stmt.strip() and not stmt.strip().startswith('--')]

        for i, statement in enumerate(statements):
            try:
                cursor.execute(statement)
                connection.commit()
                print(f"Executed statement {i+1}/{len(statements)}")
            except Exception as e:
                print(f"Error in statement {i+1}: {e}")
                break
        print("Migration completed successfully!")

        # Verify tables were created
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Check admin user
        cursor.execute("SELECT id, username, super_admin, status FROM sys_user WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        if admin_user:
            print(f"\nAdmin user created: ID={admin_user[0]}, Username={admin_user[1]}, Super Admin={admin_user[2]}, Status={admin_user[3]}")

        cursor.close()
        connection.close()

        print("\nDatabase is ready! You can now run your manager-api server with:")
        print("  --spring.profiles.active=local")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_clean_migration()