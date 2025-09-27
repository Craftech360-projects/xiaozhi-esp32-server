
import mysql.connector
import json
import argparse

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
            'connect_timeout': 60,
            'read_timeout': 60
        }

        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        print(f"✅ Connected to {name} database successfully!")

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
            # print(f"Processing table: {table_name}")
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
        print(f"❌ Error connecting to {name} database: {e}")
        return None

def compare_local_databases(db1_name, db2_name):
    print("=== Local Database Comparison Tool ===\n")

    # Get DB1 info
    db1_info = get_database_info(
        host='localhost',
        port=3307,
        user='manager',
        password='managerpassword',
        database=db1_name,
        name=db1_name
    )

    # Get DB2 info
    db2_info = get_database_info(
        host='localhost',
        port=3307,
        user='manager',
        password='managerpassword',
        database=db2_name,
        name=db2_name
    )

    if not db1_info or not db2_info:
        print("❌ Could not connect to one or both databases")
        return

    print("\n" + "="*60)
    print(f"DATABASE COMPARISON: {db1_name} vs {db2_name}")
    print("="*60)

    # Basic comparison
    print(f"\n📊 Table Count:")
    print(f"   {db1_name}: {db1_info['table_count']} tables")
    print(f"   {db2_name}:   {db2_info['table_count']} tables")

    print(f"\n📈 Total Records:")
    print(f"   {db1_name}: {db1_info['total_records']} records")
    print(f"   {db2_name}:   {db2_info['total_records']} records")

    # Table comparison
    db1_tables = set(db1_info['tables'].keys())
    db2_tables = set(db2_info['tables'].keys())

    missing_in_db2 = db1_tables - db2_tables
    missing_in_db1 = db2_tables - db1_tables
    common_tables = db1_tables & db2_tables

    print(f"\n🔍 Table Analysis:")
    print(f"   Common tables: {len(common_tables)}")
    print(f"   Tables missing in {db2_name}: {len(missing_in_db2)}")
    print(f"   Tables only in {db2_name}: {len(missing_in_db1)}")

    if missing_in_db2:
        print(f"\n❌ Tables missing in {db2_name}:")
        for table in sorted(missing_in_db2):
            print(f"   - {table}")

    if missing_in_db1:
        print(f"\n⚠️  Tables only in {db2_name}:")
        for table in sorted(missing_in_db1):
            print(f"   - {table}")

    # Detailed comparison for common tables
    print(f"\n📋 Detailed Table Comparison:")
    schema_matches = 0
    data_matches = 0

    for table_name in sorted(common_tables):
        db1_table = db1_info['tables'][table_name]
        db2_table = db2_info['tables'][table_name]

        # Compare column count
        db1_cols = len(db1_table['columns'])
        db2_cols = len(db2_table['columns'])

        # Compare record count
        db1_records = db1_table['record_count']
        db2_records = db2_table['record_count']

        schema_match = db1_cols == db2_cols
        data_match = db1_records == db2_records

        if schema_match:
            schema_matches += 1
        if data_match:
            data_matches += 1

        status = "✅" if schema_match and data_match else "❌"
        print(f"   {status} {table_name}:")
        print(f"      Columns: {db1_name}={db1_cols}, {db2_name}={db2_cols}")
        print(f"      Records: {db1_name}={db1_records}, {db2_name}={db2_records}")

        # Check for column differences
        db1_col_names = set(db1_table['columns'].keys())
        db2_col_names = set(db2_table['columns'].keys())

        if db1_col_names != db2_col_names:
            missing_cols = db1_col_names - db2_col_names
            extra_cols = db2_col_names - db1_col_names
            if missing_cols:
                print(f"      Missing columns in {db2_name}: {missing_cols}")
            if extra_cols:
                print(f"      Extra columns in {db2_name}: {extra_cols}")

    print(f"\n📊 Summary:")
    print(f"   Schema matches: {schema_matches}/{len(common_tables)} tables")
    print(f"   Data matches (record count): {data_matches}/{len(common_tables)} tables")

    # Overall assessment
    if (len(missing_in_db2) == 0 and
        len(missing_in_db1) == 0 and
        schema_matches == len(common_tables)):
        print(f"\n🎉 SCHEMA MATCH! Both databases have identical table structures.")
        if data_matches == len(common_tables):
            print(f"\n🎉 PERFECT MATCH! Data counts are also identical.")
        else:
            print(f"\n⚠️  DATA MISMATCH! Record counts differ in some tables.")
    else:
        print(f"\n⚠️  SCHEMA MISMATCH! See details above.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two local MySQL databases.")
    parser.add_argument("db1", help="Name of the first database (e.g., the reference database)")
    parser.add_argument("db2", help="Name of the second database (e.g., the test database)")
    args = parser.parse_args()

    compare_local_databases(args.db1, args.db2)
