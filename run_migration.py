import mysql.connector

def run_migration():
    try:
        # Connect to local Docker database
        connection = mysql.connector.connect(
            host='localhost',
            port=3307,
            user='manager',
            password='managerpassword',
            database='manager_api',
            charset='utf8mb4',
            autocommit=True
        )

        cursor = connection.cursor()
        print("Connected to local database!")

        # Read and execute migration script
        with open('railway_to_local_migration.sql', 'r', encoding='utf-8') as f:
            migration_script = f.read()

        # Split by semicolons and execute each statement
        statements = [stmt.strip() for stmt in migration_script.split(';') if stmt.strip()]

        for i, statement in enumerate(statements):
            try:
                if statement and not statement.startswith('--'):
                    cursor.execute(statement)
                    print(f"Executed statement {i+1}/{len(statements)}")
            except Exception as e:
                print(f"Error executing statement {i+1}: {e}")
                print(f"Statement: {statement[:100]}...")

        print("Migration completed!")

        # Verify tables were created
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Created {len(tables)} tables")

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_migration()