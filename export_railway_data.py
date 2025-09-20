import mysql.connector
import json
import sys

def export_railway_users():
    """Export all user data from Railway database"""

    # Railway database connection
    railway_config = {
        'host': 'crossover.proxy.rlwy.net',
        'port': 56145,
        'user': 'root',
        'password': 'XjOWQwtGNcoMIELTjoMoaaBTfKiBjVcA',
        'database': 'railway',
        'charset': 'utf8mb4',
        'connect_timeout': 60,
        'read_timeout': 60,
        'ssl_disabled': False,
        'autocommit': True
    }

    try:
        print("Connecting to Railway database...")
        railway_conn = mysql.connector.connect(**railway_config)
        railway_cursor = railway_conn.cursor()

        print("Connected successfully! Exporting user data...")

        # Export sys_user table
        railway_cursor.execute("SELECT * FROM sys_user")
        users = railway_cursor.fetchall()

        # Get column names
        railway_cursor.execute("DESCRIBE sys_user")
        columns = [row[0] for row in railway_cursor.fetchall()]

        print(f"Found {len(users)} users in Railway database")

        # Create SQL insert statements
        insert_statements = []

        if users:
            # Clear existing users
            insert_statements.append("DELETE FROM sys_user;")

            for user in users:
                # Create INSERT statement
                values = []
                for value in user:
                    if value is None:
                        values.append('NULL')
                    elif isinstance(value, str):
                        # Escape single quotes
                        escaped = value.replace("'", "\\'")
                        values.append(f"'{escaped}'")
                    elif isinstance(value, int):
                        values.append(str(value))
                    else:
                        values.append(f"'{str(value)}'")

                insert_sql = f"INSERT INTO sys_user ({', '.join(columns)}) VALUES ({', '.join(values)});"
                insert_statements.append(insert_sql)

        # Export other important tables
        important_tables = ['sys_params', 'sys_dict_type', 'sys_dict_data',
                          'ai_model_provider', 'ai_model_config', 'ai_tts_voice', 'ai_agent_template']

        for table_name in important_tables:
            try:
                print(f"Exporting {table_name}...")
                railway_cursor.execute(f"SELECT * FROM {table_name}")
                rows = railway_cursor.fetchall()

                if rows:
                    # Get column names
                    railway_cursor.execute(f"DESCRIBE {table_name}")
                    table_columns = [row[0] for row in railway_cursor.fetchall()]

                    insert_statements.append(f"DELETE FROM {table_name};")

                    for row in rows:
                        values = []
                        for value in row:
                            if value is None:
                                values.append('NULL')
                            elif isinstance(value, str):
                                escaped = value.replace("'", "\\'").replace("\\", "\\\\")
                                values.append(f"'{escaped}'")
                            elif isinstance(value, (int, float)):
                                values.append(str(value))
                            else:
                                values.append(f"'{str(value)}'")

                        insert_sql = f"INSERT INTO {table_name} ({', '.join(table_columns)}) VALUES ({', '.join(values)});"
                        insert_statements.append(insert_sql)

                    print(f"  - Exported {len(rows)} records from {table_name}")
            except Exception as e:
                print(f"  - Could not export {table_name}: {e}")

        # Write to file
        with open('railway_data_export.sql', 'w', encoding='utf-8') as f:
            f.write("-- Railway Database Export\n")
            f.write("-- Generated automatically\n\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

            for statement in insert_statements:
                f.write(statement + "\n")

            f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")

        print(f"\nExport completed successfully!")
        print(f"Total SQL statements: {len(insert_statements)}")
        print(f"Export saved to: railway_data_export.sql")

        railway_cursor.close()
        railway_conn.close()

        return True

    except mysql.connector.Error as err:
        print(f"Railway database connection failed: {err}")
        print("\nFallback: Creating Railway data export script...")

        # Create a manual export script since automatic connection failed
        with open('manual_railway_export.sql', 'w', encoding='utf-8') as f:
            f.write("""-- Manual Railway Data Export Template
-- Please run these commands on your Railway database and save the results

-- Export users
SELECT CONCAT(
    'INSERT INTO sys_user (id, username, password, super_admin, status, create_date, updater, creator, update_date) VALUES (',
    IFNULL(id, 'NULL'), ', ',
    IFNULL(CONCAT('"', username, '"'), 'NULL'), ', ',
    IFNULL(CONCAT('"', password, '"'), 'NULL'), ', ',
    IFNULL(super_admin, 'NULL'), ', ',
    IFNULL(status, 'NULL'), ', ',
    IFNULL(CONCAT('"', create_date, '"'), 'NULL'), ', ',
    IFNULL(updater, 'NULL'), ', ',
    IFNULL(creator, 'NULL'), ', ',
    IFNULL(CONCAT('"', update_date, '"'), 'NULL'),
    ');'
) AS insert_statement
FROM sys_user;

-- Check user count
SELECT COUNT(*) as user_count FROM sys_user;

-- Show user details
SELECT id, username, super_admin, status FROM sys_user;
""")

        print("Created manual export template: manual_railway_export.sql")
        print("Please run this on your Railway database to get the exact user data.")

        return False

    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    export_railway_users()