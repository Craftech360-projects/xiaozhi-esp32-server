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
            'connect_timeout': 60,
            'read_timeout': 60
        }

        # Add SSL settings for Railway
        if 'proxy.rlwy.net' in host:
            config['ssl_disabled'] = False
            config['autocommit'] = True

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
        print(f"❌ Error connecting to {name} database: {e}")
        return None

def compare_databases():
    print("=== Database Comparison Tool ===\n")

    # Get Railway database info
    railway_info = get_database_info(
        host='crossover.proxy.rlwy.net',
        port=56145,
        user='root',
        password='XjOWQwtGNcoMIELTjoMoaaBTfKiBjVcA',
        database='railway',
        name='Railway'
    )

    # Get Local database info
    local_info = get_database_info(
        host='localhost',
        port=3307,
        user='manager',
        password='managerpassword',
        database='manager_api',
        name='Local'
    )

    if not railway_info or not local_info:
        print("❌ Could not connect to one or both databases")
        return

    print("\n" + "="*60)
    print("DATABASE COMPARISON RESULTS")
    print("="*60)

    # Basic comparison
    print(f"\n📊 Table Count:")
    print(f"   Railway: {railway_info['table_count']} tables")
    print(f"   Local:   {local_info['table_count']} tables")

    print(f"\n📈 Total Records:")
    print(f"   Railway: {railway_info['total_records']} records")
    print(f"   Local:   {local_info['total_records']} records")

    # Table comparison
    railway_tables = set(railway_info['tables'].keys())
    local_tables = set(local_info['tables'].keys())

    missing_in_local = railway_tables - local_tables
    missing_in_railway = local_tables - railway_tables
    common_tables = railway_tables & local_tables

    print(f"\n🔍 Table Analysis:")
    print(f"   Common tables: {len(common_tables)}")
    print(f"   Missing in Local: {len(missing_in_local)}")
    print(f"   Missing in Railway: {len(missing_in_railway)}")

    if missing_in_local:
        print(f"\n❌ Tables missing in Local database:")
        for table in sorted(missing_in_local):
            print(f"   - {table}")

    if missing_in_railway:
        print(f"\n⚠️  Tables only in Local database:")
        for table in sorted(missing_in_railway):
            print(f"   - {table}")

    # Detailed comparison for common tables
    print(f"\n📋 Detailed Table Comparison:")
    schema_matches = 0
    data_matches = 0

    for table_name in sorted(common_tables):
        railway_table = railway_info['tables'][table_name]
        local_table = local_info['tables'][table_name]

        # Compare column count
        railway_cols = len(railway_table['columns'])
        local_cols = len(local_table['columns'])

        # Compare record count
        railway_records = railway_table['record_count']
        local_records = local_table['record_count']

        schema_match = railway_cols == local_cols
        data_match = railway_records == local_records

        if schema_match:
            schema_matches += 1
        if data_match:
            data_matches += 1

        status = "✅" if schema_match and data_match else "❌"
        print(f"   {status} {table_name}:")
        print(f"      Columns: Railway={railway_cols}, Local={local_cols}")
        print(f"      Records: Railway={railway_records}, Local={local_records}")

        # Check for column differences
        railway_col_names = set(railway_table['columns'].keys())
        local_col_names = set(local_table['columns'].keys())

        if railway_col_names != local_col_names:
            missing_cols = railway_col_names - local_col_names
            extra_cols = local_col_names - railway_col_names
            if missing_cols:
                print(f"      Missing columns in Local: {missing_cols}")
            if extra_cols:
                print(f"      Extra columns in Local: {extra_cols}")

    print(f"\n📊 Summary:")
    print(f"   Schema matches: {schema_matches}/{len(common_tables)} tables")
    print(f"   Data matches: {data_matches}/{len(common_tables)} tables")

    # Overall assessment
    if (len(missing_in_local) == 0 and
        schema_matches == len(common_tables) and
        data_matches == len(common_tables)):
        print(f"\n🎉 PERFECT MATCH! Local database is identical to Railway database.")
    elif len(missing_in_local) == 0 and schema_matches == len(common_tables):
        print(f"\n✅ SCHEMA MATCH! All table structures are identical. Only data counts differ.")
    else:
        print(f"\n⚠️  DIFFERENCES FOUND! See details above.")

    # Save detailed comparison to file
    comparison_data = {
        'railway': railway_info,
        'local': local_info,
        'analysis': {
            'common_tables': list(common_tables),
            'missing_in_local': list(missing_in_local),
            'missing_in_railway': list(missing_in_railway),
            'schema_matches': schema_matches,
            'data_matches': data_matches
        }
    }

    with open('database_comparison_report.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Detailed report saved to: database_comparison_report.json")

if __name__ == "__main__":
    compare_databases()