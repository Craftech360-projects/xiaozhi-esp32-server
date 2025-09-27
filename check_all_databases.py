#!/usr/bin/env python3
"""
Check all databases accessible to the manager user
"""

import mysql.connector
from mysql.connector import Error

def check_databases():
    config = {
        'host': 'localhost',
        'port': 3307,
        'user': 'manager',
        'password': 'managerpassword',
        'charset': 'utf8mb4',
        'use_unicode': True,
        'autocommit': True
    }

    try:
        # Connect without specifying a database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print("=" * 60)
        print("CHECKING ALL DATABASES")
        print("=" * 60)

        # Get all databases
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]

        print(f"Found {len(databases)} databases:")
        for db in databases:
            print(f"  - {db}")

        print("\n" + "=" * 60)
        print("TABLE COUNT PER DATABASE")
        print("=" * 60)

        # Check table count for each accessible database
        for db in databases:
            if db not in ['information_schema', 'performance_schema', 'mysql', 'sys']:
                try:
                    cursor.execute(f"USE `{db}`")
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    table_count = len(tables)

                    print(f"\nDatabase: {db}")
                    print(f"  Tables: {table_count}")

                    if table_count > 0:
                        print("  Sample tables:")
                        for table in tables[:5]:  # Show first 5 tables
                            print(f"    - {table[0]}")
                        if table_count > 5:
                            print(f"    ... and {table_count - 5} more")

                    # Check for Cheeko template specifically
                    try:
                        cursor.execute("SELECT COUNT(*) FROM ai_agent_template WHERE agent_name = 'Cheeko'")
                        cheeko_count = cursor.fetchone()[0]
                        if cheeko_count > 0:
                            print(f"  ✅ HAS CHEEKO TEMPLATE")
                        else:
                            print(f"  ❌ No Cheeko template")
                    except:
                        print(f"  ℹ️  No ai_agent_template table")

                except Error as e:
                    print(f"\nDatabase: {db}")
                    print(f"  Error accessing: {e}")

        cursor.close()
        connection.close()

    except Error as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    check_databases()