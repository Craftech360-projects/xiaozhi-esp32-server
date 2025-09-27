#!/usr/bin/env python3
import mysql.connector
import sys

def import_migration():
    config = {
        'host': 'localhost',
        'port': 3308,
        'user': 'root',
        'password': 'password123',
        'database': 'manager_api_fresh',
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': True
    }

    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print("Connected to fresh database successfully!")

        # Read and execute the migration file
        with open('complete_main_migration.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Split SQL statements by semicolon and execute each one
        statements = sql_content.split(';')

        print(f"Executing {len(statements)} SQL statements...")

        for i, statement in enumerate(statements):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    if i % 100 == 0:
                        print(f"Executed statement {i}/{len(statements)}")
                except Exception as e:
                    print(f"Error at statement {i}: {e}")
                    print(f"Statement: {statement[:100]}...")

        cursor.close()
        connection.close()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(import_migration())