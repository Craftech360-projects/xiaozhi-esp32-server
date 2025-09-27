#!/usr/bin/env python3
"""
Database Migration Verification Script
Compares main database with migrated fresh database
"""

import mysql.connector
import json

def get_database_info(host, port, user, password, database, name):
    """Extract schema and data information from a database"""
    try:
        print(f"Connecting to {name} database...")

        # Connection config
        config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': 'utf8mb4',
            'connect_timeout': 60
        }

        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print(f"[OK] Connected to {name} database successfully!")

        db_info = {
            'name': name,
            'tables': {},
            'table_count': 0,
            'total_records': 0
        }

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        db_info['table_count'] = len(tables)

        print(f"Found {len(tables)} tables in {name}")

        for table_name in tables:
            table_info = {}

            # Get table structure
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            table_info['columns'] = {
                col[0]: {
                    'type': col[1],
                    'null': col[2],
                    'key': col[3],
                    'default': col[4],
                    'extra': col[5]
                } for col in columns
            }

            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            record_count = cursor.fetchone()[0]
            table_info['record_count'] = record_count
            db_info['total_records'] += record_count

            db_info['tables'][table_name] = table_info

        cursor.close()
        connection.close()

        return db_info

    except Exception as e:
        print(f"[ERROR] Error connecting to {name} database: {e}")
        return None

def compare_databases():
    print("=== Database Migration Verification ===\n")

    # Get main DB info
    main_db_info = get_database_info(
        host='localhost',
        port=3307,
        user='manager',
        password='managerpassword',
        database='manager_api',
        name='Main DB'
    )

    # Get fresh DB info
    fresh_db_info = get_database_info(
        host='localhost',
        port=3308,
        user='root',
        password='password123',
        database='manager_api_fresh',
        name='Fresh DB'
    )

    if not main_db_info or not fresh_db_info:
        print("[ERROR] Could not connect to one or both databases")
        return

    print("\n" + "="*60)
    print(f"DATABASE COMPARISON: Main vs Fresh")
    print("="*60)

    # Basic comparison
    print(f"\n[INFO] Table Count:")
    print(f"   Main DB: {main_db_info['table_count']} tables")
    print(f"   Fresh DB: {fresh_db_info['table_count']} tables")

    print(f"\n[INFO] Total Records:")
    print(f"   Main DB: {main_db_info['total_records']} records")
    print(f"   Fresh DB: {fresh_db_info['total_records']} records")

    # Table comparison
    main_tables = set(main_db_info['tables'].keys())
    fresh_tables = set(fresh_db_info['tables'].keys())

    missing_in_fresh = main_tables - fresh_tables
    extra_in_fresh = fresh_tables - main_tables
    common_tables = main_tables & fresh_tables

    print(f"\n[INFO] Table Analysis:")
    print(f"   Common tables: {len(common_tables)}")
    print(f"   Tables missing in Fresh DB: {len(missing_in_fresh)}")
    print(f"   Extra tables in Fresh DB: {len(extra_in_fresh)}")

    if missing_in_fresh:
        print(f"\n[ERROR] Tables missing in Fresh DB:")
        for table in sorted(missing_in_fresh):
            print(f"   - {table}")

    if extra_in_fresh:
        print(f"\n[WARN] Extra tables in Fresh DB:")
        for table in sorted(extra_in_fresh):
            print(f"   - {table}")

    # Check critical tables for mobile registration
    critical_tables = ['sys_params', 'sys_dict_data', 'ai_model_config']
    print(f"\n[INFO] Critical Tables for Mobile Registration:")

    for table in critical_tables:
        if table in common_tables:
            main_count = main_db_info['tables'][table]['record_count']
            fresh_count = fresh_db_info['tables'][table]['record_count']
            status = "[OK]" if fresh_count > 0 else "[WARN]"
            print(f"   {status} {table}: Main={main_count}, Fresh={fresh_count}")
        else:
            print(f"   [ERROR] {table}: Missing in fresh database")

    # Check if mobile registration parameters exist
    print(f"\n[INFO] Mobile Registration Check:")
    try:
        config = {
            'host': 'localhost', 'port': 3308, 'user': 'root',
            'password': 'password123', 'database': 'manager_api_fresh'
        }
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        cursor.execute("SELECT param_code, param_value FROM sys_params WHERE param_code LIKE '%register%'")
        register_params = cursor.fetchall()

        if register_params:
            print("   Registration parameters found:")
            for param in register_params:
                print(f"   - {param[0]}: {param[1]}")
        else:
            print("   [WARN] No registration parameters found")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"   [ERROR] Could not check registration parameters: {e}")

    print(f"\n[INFO] Summary:")
    schema_match = len(missing_in_fresh) == 0
    print(f"   Schema complete: {'Yes' if schema_match else 'No'}")
    print(f"   Ready for mobile registration: {'Check parameters above' if fresh_db_info['tables'].get('sys_params', {}).get('record_count', 0) > 0 else 'Missing configuration'}")

if __name__ == "__main__":
    compare_databases()