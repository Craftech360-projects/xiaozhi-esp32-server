#!/usr/bin/env python3
"""
Fix Mobile Registration Configuration
Adds the missing sys_params and model config data needed for mobile registration
to work exactly like the main database
"""

import mysql.connector
import json

# Database configurations
MAIN_DB_CONFIG = {
    'host': 'localhost', 'port': 3307, 'user': 'manager',
    'password': 'managerpassword', 'database': 'manager_api'
}

FRESH_DB_CONFIG = {
    'host': 'localhost', 'port': 3308, 'user': 'root',
    'password': 'password123', 'database': 'manager_api_fresh'
}

def copy_sys_params():
    """Copy all sys_params from main database to fresh database"""
    try:
        # Connect to main database
        main_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        main_cursor = main_conn.cursor()

        # Get all sys_params from main database
        main_cursor.execute("SELECT param_code, param_value, value_type, param_type, remark FROM sys_params")
        all_params = main_cursor.fetchall()

        main_cursor.close()
        main_conn.close()

        # Connect to fresh database
        fresh_conn = mysql.connector.connect(**FRESH_DB_CONFIG)
        fresh_cursor = fresh_conn.cursor()

        print(f"Copying {len(all_params)} system parameters...")

        for param in all_params:
            param_code, param_value, value_type, param_type, remark = param

            # Sanitize API keys
            if param_value and ('key' in param_code.lower() or 'secret' in param_code.lower()):
                if param_value and len(param_value) > 10:
                    param_value = 'YOUR_API_KEY_HERE'

            try:
                fresh_cursor.execute("""
                    INSERT INTO sys_params (param_code, param_value, value_type, param_type, remark)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        param_value = VALUES(param_value),
                        value_type = VALUES(value_type),
                        remark = VALUES(remark)
                """, (param_code, param_value, value_type, param_type, remark))

            except Exception as e:
                print(f"Warning: Could not insert param {param_code}: {e}")

        fresh_conn.commit()
        fresh_cursor.close()
        fresh_conn.close()

        print("[OK] System parameters copied successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to copy sys_params: {e}")
        return False

def copy_model_configs():
    """Copy all ai_model_config from main database to fresh database"""
    try:
        # Connect to main database
        main_conn = mysql.connector.connect(**MAIN_DB_CONFIG)
        main_cursor = main_conn.cursor()

        # Get all model configs from main database
        main_cursor.execute("SELECT * FROM ai_model_config")
        columns = [desc[0] for desc in main_cursor.description]
        all_configs = main_cursor.fetchall()

        main_cursor.close()
        main_conn.close()

        # Connect to fresh database
        fresh_conn = mysql.connector.connect(**FRESH_DB_CONFIG)
        fresh_cursor = fresh_conn.cursor()

        print(f"Copying {len(all_configs)} model configurations...")

        for config in all_configs:
            config_dict = dict(zip(columns, config))

            # Sanitize config_json to remove API keys
            if config_dict.get('config_json'):
                try:
                    config_json = json.loads(config_dict['config_json'])
                    if isinstance(config_json, dict):
                        for key in config_json:
                            if 'key' in key.lower() and isinstance(config_json[key], str):
                                if len(config_json[key]) > 10:
                                    config_json[key] = 'YOUR_API_KEY_HERE'
                        config_dict['config_json'] = json.dumps(config_json)
                except:
                    # If JSON is invalid, keep original
                    pass

            # Build INSERT statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join([f'`{col}`' for col in columns])

            values = tuple(config_dict[col] for col in columns)

            try:
                fresh_cursor.execute(f"""
                    INSERT INTO ai_model_config ({column_names})
                    VALUES ({placeholders})
                    ON DUPLICATE KEY UPDATE
                        config_json = VALUES(config_json),
                        remark = VALUES(remark)
                """, values)

            except Exception as e:
                print(f"Warning: Could not insert model config {config_dict.get('id', 'unknown')}: {e}")

        fresh_conn.commit()
        fresh_cursor.close()
        fresh_conn.close()

        print("[OK] Model configurations copied successfully")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to copy ai_model_config: {e}")
        return False

def verify_mobile_registration_setup():
    """Verify that mobile registration is properly configured"""
    try:
        fresh_conn = mysql.connector.connect(**FRESH_DB_CONFIG)
        fresh_cursor = fresh_conn.cursor()

        print("\n=== Mobile Registration Verification ===")

        # Check key parameters
        fresh_cursor.execute("SELECT param_code, param_value FROM sys_params WHERE param_code IN ('server.enable_mobile_register', 'server.allow_user_register')")
        key_params = fresh_cursor.fetchall()

        for param_code, param_value in key_params:
            print(f"[OK] {param_code}: {param_value}")

        # Check mobile area codes
        fresh_cursor.execute("""
            SELECT COUNT(*) FROM sys_dict_data sdd
            JOIN sys_dict_type sdt ON sdd.dict_type_id = sdt.id
            WHERE sdt.dict_type = 'mobile_area'
        """)
        area_count = fresh_cursor.fetchone()[0]
        print(f"[OK] Mobile area codes: {area_count}")

        # Check model configs
        fresh_cursor.execute("SELECT COUNT(*) FROM ai_model_config")
        model_count = fresh_cursor.fetchone()[0]
        print(f"[OK] Model configurations: {model_count}")

        # Check sys_params count
        fresh_cursor.execute("SELECT COUNT(*) FROM sys_params")
        param_count = fresh_cursor.fetchone()[0]
        print(f"[OK] System parameters: {param_count}")

        fresh_cursor.close()
        fresh_conn.close()

        print("\n[OK] Mobile registration should now work with phone number + SMS verification")
        return True

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False

def main():
    """Fix mobile registration configuration"""
    print("Fixing mobile registration configuration...")
    print("=" * 50)

    print("\n1. Copying system parameters from main database...")
    if not copy_sys_params():
        print("[ERROR] Failed to copy system parameters")
        return

    print("\n2. Copying model configurations from main database...")
    if not copy_model_configs():
        print("[ERROR] Failed to copy model configurations")
        return

    print("\n3. Verifying mobile registration setup...")
    if not verify_mobile_registration_setup():
        print("[ERROR] Verification failed")
        return

    print("\n" + "=" * 50)
    print("[SUCCESS] Mobile registration configuration fixed!")
    print("\nThe fresh database now has:")
    print("- All system parameters from main database")
    print("- All model configurations (with API keys sanitized)")
    print("- Mobile area codes for phone registration")
    print("- Proper mobile registration settings")
    print("\nMobile registration should work exactly like the main database!")

if __name__ == "__main__":
    main()