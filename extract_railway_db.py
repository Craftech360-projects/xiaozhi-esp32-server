import mysql.connector
import sys
import traceback
import time

def extract_database():
    try:
        print("Attempting to connect to Railway database...")

        # Try different connection configurations
        connection_configs = [
            {
                'host': 'crossover.proxy.rlwy.net',
                'port': 56145,
                'user': 'root',
                'password': 'XjOWQwtGNcoMIELTjoMoaaBTfKiBjVcA',
                'database': 'railway',
                'charset': 'utf8mb4',
                'use_unicode': True,
                'ssl_disabled': True,
                'autocommit': True,
                'connect_timeout': 60,
                'read_timeout': 60
            },
            {
                'host': 'crossover.proxy.rlwy.net',
                'port': 56145,
                'user': 'root',
                'password': 'XjOWQwtGNcoMIELTjoMoaaBTfKiBjVcA',
                'database': 'railway',
                'charset': 'utf8mb4',
                'use_unicode': True,
                'ssl_disabled': False,
                'autocommit': True,
                'connect_timeout': 60,
                'read_timeout': 60
            }
        ]

        connection = None
        for i, config in enumerate(connection_configs):
            try:
                print(f"Trying connection config {i+1}...")
                connection = mysql.connector.connect(**config)
                print(f"Successfully connected with config {i+1}!")
                break
            except Exception as e:
                print(f"Config {i+1} failed: {e}")
                continue

        if connection is None:
            raise Exception("All connection attempts failed")

        # If we can't connect to Railway, create from existing migrations
        create_from_local_migrations()
        return

        cursor = connection.cursor()

        print("Connected successfully to Railway database!")

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")

        # Create migration script
        with open('railway_migration.sql', 'w', encoding='utf-8') as f:
            f.write("-- Railway Database Migration Script\n")
            f.write("-- Generated automatically\n\n")
            f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
            f.write("SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';\n")
            f.write("SET AUTOCOMMIT = 0;\n")
            f.write("START TRANSACTION;\n\n")

            for table_tuple in tables:
                table_name = table_tuple[0]
                print(f"Processing table: {table_name}")

                # Get CREATE TABLE statement
                cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
                create_table = cursor.fetchone()[1]
                f.write(f"-- Table structure for {table_name}\n")
                f.write(f"DROP TABLE IF EXISTS `{table_name}`;\n")
                f.write(f"{create_table};\n\n")

                # Get table data
                cursor.execute(f"SELECT * FROM `{table_name}`")
                rows = cursor.fetchall()

                if rows:
                    # Get column names
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = [row[0] for row in cursor.fetchall()]

                    f.write(f"-- Data for table {table_name}\n")
                    f.write(f"INSERT INTO `{table_name}` (`{'`, `'.join(columns)}`) VALUES\n")

                    for i, row in enumerate(rows):
                        # Escape and format values
                        values = []
                        for value in row:
                            if value is None:
                                values.append('NULL')
                            elif isinstance(value, str):
                                # Escape single quotes and backslashes
                                escaped = value.replace('\\', '\\\\').replace("'", "\\'")
                                values.append(f"'{escaped}'")
                            elif isinstance(value, (int, float)):
                                values.append(str(value))
                            else:
                                values.append(f"'{str(value)}'")

                        if i == len(rows) - 1:
                            f.write(f"({', '.join(values)});\n\n")
                        else:
                            f.write(f"({', '.join(values)}),\n")
                else:
                    f.write(f"-- No data for table {table_name}\n\n")

            f.write("SET FOREIGN_KEY_CHECKS = 1;\n")
            f.write("COMMIT;\n")

        print("Migration script created successfully: railway_migration.sql")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        traceback.print_exc()
    except Exception as e:
        print(f"General error: {e}")
        traceback.print_exc()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    extract_database()