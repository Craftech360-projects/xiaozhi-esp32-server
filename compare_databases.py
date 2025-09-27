import mysql.connector
import json
from collections import defaultdict

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
            'use_unicode': True,
            'autocommit': True
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
            print(f"Processing table: {table_name}")
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

            # Get CREATE TABLE statement
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_statement = cursor.fetchone()[1]
            table_info['create_statement'] = create_statement

            # Get some sample data (first 5 rows)
            try:
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 5")
                sample_data = cursor.fetchall()

                # Convert to JSON serializable format
                serializable_data = []
                for row in sample_data:
                    serializable_row = []
                    for item in row:
                        if item is None:
                            serializable_row.append(None)
                        elif isinstance(item, (bytes, bytearray)):
                            serializable_row.append(item.decode('utf-8', errors='ignore'))
                        else:
                            serializable_row.append(str(item))
                    serializable_data.append(serializable_row)

                table_info['sample_data'] = serializable_data
            except Exception as e:
                table_info['sample_data'] = f"Error getting sample data: {e}"

            db_info['tables'][table_name] = table_info

        cursor.close()
        connection.close()

        return db_info

    except Exception as e:
        print(f"[ERROR] Error connecting to {name} database: {e}")
        return None

def compare_databases():
    print("=== Database Comparison Tool ===\n")

    # Get Original database info (manager_api on port 3307)
    original_info = get_database_info(
        host='localhost',
        port=3307,
        user='manager',
        password='managerpassword',
        database='manager_api',
        name='Original'
    )

    # Get Fresh database info (manager_api_fresh on port 3308)
    fresh_info = get_database_info(
        host='localhost',
        port=3308,
        user='root',
        password='password123',
        database='manager_api_fresh',
        name='Fresh'
    )

    if not original_info or not fresh_info:
        print("[ERROR] Could not connect to one or both databases")
        return

    print("\n" + "="*60)
    print("DATABASE MIGRATION VERIFICATION")
    print("="*60)

    # Basic comparison
    print(f"\n[INFO] Table Count:")
    print(f"   Original: {original_info['table_count']} tables")
    print(f"   Fresh:    {fresh_info['table_count']} tables")

    print(f"\n[INFO] Total Records:")
    print(f"   Original: {original_info['total_records']} records")
    print(f"   Fresh:    {fresh_info['total_records']} records")

    # Table comparison
    original_tables = set(original_info['tables'].keys())
    fresh_tables = set(fresh_info['tables'].keys())

    missing_in_fresh = original_tables - fresh_tables
    missing_in_original = fresh_tables - original_tables
    common_tables = original_tables & fresh_tables

    print(f"\n[INFO] Table Analysis:")
    print(f"   Common tables: {len(common_tables)}")
    print(f"   Missing in Fresh: {len(missing_in_fresh)}")
    print(f"   Missing in Original: {len(missing_in_original)}")

    if missing_in_fresh:
        print(f"\n[ERROR] Tables missing in Fresh database:")
        for table in sorted(missing_in_fresh):
            print(f"   - {table}")

    if missing_in_original:
        print(f"\n[WARNING] Tables only in Fresh database:")
        for table in sorted(missing_in_original):
            print(f"   - {table}")

    # Detailed comparison for common tables
    print(f"\n[INFO] Detailed Table Comparison:")
    schema_matches = 0
    data_matches = 0

    for table_name in sorted(common_tables):
        original_table = original_info['tables'][table_name]
        fresh_table = fresh_info['tables'][table_name]

        # Compare column count
        original_cols = len(original_table['columns'])
        fresh_cols = len(fresh_table['columns'])

        # Compare record count
        original_records = original_table['record_count']
        fresh_records = fresh_table['record_count']

        schema_match = original_cols == fresh_cols
        data_match = original_records == fresh_records

        if schema_match:
            schema_matches += 1
        if data_match:
            data_matches += 1

        status = "[OK]" if schema_match and data_match else "[DIFF]"
        print(f"   {status} {table_name}:")
        print(f"      Columns: Original={original_cols}, Fresh={fresh_cols}")
        print(f"      Records: Original={original_records}, Fresh={fresh_records}")

        # Check for column differences
        original_col_names = set(original_table['columns'].keys())
        fresh_col_names = set(fresh_table['columns'].keys())

        if original_col_names != fresh_col_names:
            missing_cols = original_col_names - fresh_col_names
            extra_cols = fresh_col_names - original_col_names
            if missing_cols:
                print(f"      Missing columns in Fresh: {missing_cols}")
            if extra_cols:
                print(f"      Extra columns in Fresh: {extra_cols}")

    print(f"\n[INFO] Summary:")
    print(f"   Schema matches: {schema_matches}/{len(common_tables)} tables")
    print(f"   Data matches: {data_matches}/{len(common_tables)} tables")

    # Overall assessment
    if (len(missing_in_fresh) == 0 and
        schema_matches == len(common_tables) and
        data_matches == len(common_tables)):
        print(f"\n[SUCCESS] PERFECT MATCH! Fresh database is identical to Original database.")
    elif len(missing_in_fresh) == 0 and schema_matches == len(common_tables):
        print(f"\n[OK] SCHEMA MATCH! All table structures are identical. Only data counts differ.")
    else:
        print(f"\n[WARNING] DIFFERENCES FOUND! See details above.")

    # Save detailed comparison to file
    comparison_data = {
        'original': original_info,
        'fresh': fresh_info,
        'analysis': {
            'common_tables': list(common_tables),
            'missing_in_fresh': list(missing_in_fresh),
            'missing_in_original': list(missing_in_original),
            'schema_matches': schema_matches,
            'data_matches': data_matches
        }
    }

    with open('database_comparison_report.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[INFO] Detailed report saved to: database_comparison_report.json")

    # Special check for Cheeko template
    print(f"\n[INFO] Cheeko Template Analysis:")
    if 'ai_agent_template' in common_tables:
        try:
            # Check original database for Cheeko
            orig_cheeko = None
            for table_name, table_info in original_info['tables'].items():
                if table_name == 'ai_agent_template' and 'sample_data' in table_info:
                    for row in table_info['sample_data']:
                        if isinstance(row, list) and len(row) > 1 and 'Cheeko' in str(row):
                            orig_cheeko = row
                            break

            # Check fresh database for Cheeko
            fresh_cheeko = None
            for table_name, table_info in fresh_info['tables'].items():
                if table_name == 'ai_agent_template' and 'sample_data' in table_info:
                    for row in table_info['sample_data']:
                        if isinstance(row, list) and len(row) > 1 and 'Cheeko' in str(row):
                            fresh_cheeko = row
                            break

            if orig_cheeko and fresh_cheeko:
                print(f"   [OK] Cheeko template found in both databases")
            elif fresh_cheeko:
                print(f"   [OK] Cheeko template found in Fresh database")
                print(f"   [WARNING] Cheeko template not found in Original database")
            else:
                print(f"   [ERROR] Cheeko template not found in either database")
        except Exception as e:
            print(f"   [WARNING] Error checking Cheeko template: {e}")
    else:
        print(f"   [ERROR] ai_agent_template table not found in common tables")

if __name__ == "__main__":
    compare_databases()