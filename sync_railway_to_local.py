import mysql.connector
import time

def sync_railway_to_local():
    """Extract exact data from Railway and import to local database"""

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
        'ssl_disabled': True,
        'autocommit': True
    }

    # Local database connection
    local_config = {
        'host': 'localhost',
        'port': 3307,
        'user': 'manager',
        'password': 'managerpassword',
        'database': 'manager_api',
        'charset': 'utf8mb4',
        'autocommit': True
    }

    # Tables to sync (in order to avoid foreign key issues)
    tables_to_sync = [
        'sys_user',
        'sys_dict_type',
        'sys_dict_data',
        'sys_params',
        'ai_model_provider',
        'ai_model_config',
        'ai_tts_voice',
        'ai_agent_template',
        'ai_agent',
        'ai_device',
        'ai_voiceprint',
        'ai_chat_history',
        'ai_chat_message'
    ]

    try:
        print("Connecting to Railway database...")

        # Try multiple connection attempts
        railway_conn = None
        for attempt in range(3):
            try:
                railway_conn = mysql.connector.connect(**railway_config)
                print(f"Successfully connected to Railway on attempt {attempt + 1}")
                break
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(2)
                else:
                    raise

        railway_cursor = railway_conn.cursor()

        print("Connecting to local database...")
        local_conn = mysql.connector.connect(**local_config)
        local_cursor = local_conn.cursor()

        print("Databases connected successfully!\n")

        # Disable foreign key checks
        local_cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

        total_synced = 0

        for table_name in tables_to_sync:
            try:
                print(f"Syncing table: {table_name}")

                # Get table structure from Railway
                railway_cursor.execute(f"DESCRIBE {table_name}")
                columns_info = railway_cursor.fetchall()
                column_names = [col[0] for col in columns_info]

                # Get all data from Railway
                railway_cursor.execute(f"SELECT * FROM {table_name}")
                railway_data = railway_cursor.fetchall()

                if railway_data:
                    # Clear local table first
                    local_cursor.execute(f"DELETE FROM {table_name}")

                    # Prepare insert statement
                    placeholders = ', '.join(['%s'] * len(column_names))
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({placeholders})"

                    # Insert Railway data into local database
                    local_cursor.executemany(insert_sql, railway_data)
                    local_conn.commit()

                    print(f"  ✓ Synced {len(railway_data)} records")
                    total_synced += len(railway_data)
                else:
                    print(f"  - No data in {table_name}")

            except mysql.connector.Error as e:
                print(f"  ✗ Error syncing {table_name}: {e}")
            except Exception as e:
                print(f"  ✗ Unexpected error with {table_name}: {e}")

        # Re-enable foreign key checks
        local_cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        local_conn.commit()

        print(f"\n=== SYNC COMPLETED ===")
        print(f"Total records synced: {total_synced}")

        # Verify users were synced
        local_cursor.execute("SELECT id, username, super_admin, status FROM sys_user")
        users = local_cursor.fetchall()

        print(f"\nUsers in local database after sync:")
        for user in users:
            print(f"  - ID: {user[0]}, Username: {user[1]}, Super Admin: {user[2]}, Status: {user[3]}")

        # Close connections
        railway_cursor.close()
        railway_conn.close()
        local_cursor.close()
        local_conn.close()

        print("\n🎉 Railway data successfully synced to local database!")
        print("You can now use the same login credentials as Railway.")

        return True

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    sync_railway_to_local()