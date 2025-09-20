import mysql.connector
import json

def analyze_local_database():
    try:
        print("Analyzing local database...")

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

        analysis = {
            'tables': {},
            'summary': {}
        }

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]

        print(f"\nFound {len(tables)} tables:")
        total_records = 0

        for table_name in tables:
            print(f"  Analyzing: {table_name}")

            table_info = {}

            # Get table structure
            cursor.execute(f"DESCRIBE `{table_name}`")
            columns = cursor.fetchall()
            table_info['columns'] = []

            for col in columns:
                table_info['columns'].append({
                    'name': col[0],
                    'type': col[1],
                    'null': col[2],
                    'key': col[3],
                    'default': str(col[4]) if col[4] is not None else None,
                    'extra': col[5]
                })

            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            record_count = cursor.fetchone()[0]
            table_info['record_count'] = record_count
            total_records += record_count

            # Get CREATE TABLE statement for exact schema
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            create_statement = cursor.fetchone()[1]
            table_info['create_statement'] = create_statement

            # Get table comment
            cursor.execute(f"""
                SELECT TABLE_COMMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = 'manager_api' AND TABLE_NAME = '{table_name}'
            """)
            comment_result = cursor.fetchone()
            table_info['table_comment'] = comment_result[0] if comment_result else ''

            # Get sample data if any records exist
            if record_count > 0:
                cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                sample_data = cursor.fetchall()

                # Get column names for reference
                column_names = [col['name'] for col in table_info['columns']]

                table_info['sample_data'] = []
                for row in sample_data:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if value is not None:
                            row_dict[column_names[i]] = str(value)
                        else:
                            row_dict[column_names[i]] = None
                    table_info['sample_data'].append(row_dict)

            analysis['tables'][table_name] = table_info

        analysis['summary'] = {
            'total_tables': len(tables),
            'total_records': total_records,
            'table_list': sorted(tables)
        }

        cursor.close()
        connection.close()

        # Display summary
        print(f"\n" + "="*60)
        print("LOCAL DATABASE ANALYSIS")
        print("="*60)
        print(f"Total Tables: {analysis['summary']['total_tables']}")
        print(f"Total Records: {analysis['summary']['total_records']}")

        print(f"\nTable Details:")
        for table_name in sorted(tables):
            table_info = analysis['tables'][table_name]
            print(f"  {table_name}:")
            print(f"    Columns: {len(table_info['columns'])}")
            print(f"    Records: {table_info['record_count']}")
            print(f"    Comment: {table_info['table_comment']}")

        # Show tables with data
        tables_with_data = [t for t in tables if analysis['tables'][t]['record_count'] > 0]
        print(f"\nTables with data ({len(tables_with_data)}):")
        for table_name in sorted(tables_with_data):
            count = analysis['tables'][table_name]['record_count']
            print(f"  {table_name}: {count} records")

        # Show empty tables
        empty_tables = [t for t in tables if analysis['tables'][t]['record_count'] == 0]
        if empty_tables:
            print(f"\nEmpty tables ({len(empty_tables)}):")
            for table_name in sorted(empty_tables):
                print(f"  {table_name}")

        # Check for expected core data
        print(f"\nCore Data Check:")

        # Check admin user
        if 'sys_user' in tables:
            cursor = connection = mysql.connector.connect(
                host='localhost', port=3307, user='manager',
                password='managerpassword', database='manager_api', charset='utf8mb4'
            ).cursor()
            cursor.execute("SELECT username, super_admin, status FROM sys_user")
            users = cursor.fetchall()
            print(f"  Users found: {len(users)}")
            for user in users:
                print(f"    - {user[0]} (super_admin: {user[1]}, status: {user[2]})")
            cursor.close()

        # Save analysis to file
        with open('local_database_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nDetailed analysis saved to: local_database_analysis.json")

        return analysis

    except Exception as e:
        print(f"Error analyzing local database: {e}")
        return None

if __name__ == "__main__":
    analyze_local_database()