#!/usr/bin/env python3
"""
Verification script for manager-api_test database
"""

import mysql.connector
from mysql.connector import Error
import sys

class NewDatabaseVerifier:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'port': 3307,
            'user': 'manager-api',
            'password': 'password',
            'database': 'manager-api_test',
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True
        }
        self.connection = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                print(f"[OK] Connected to database: {self.config['database']}")
                print(f"     Host: {self.config['host']}:{self.config['port']}")
                print(f"     User: {self.config['user']}")
                return True
        except Error as e:
            print(f"[ERROR] Connection failed: {e}")
            print(f"        Trying to connect to: {self.config['host']}:{self.config['port']}")
            print(f"        Database: {self.config['database']}")
            print(f"        User: {self.config['user']}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("[OK] Database connection closed")

    def execute_query(self, query: str):
        """Execute SELECT query and return results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"[ERROR] Query failed: {e}")
            return []

    def verify_cheeko_template(self):
        """Check if Cheeko template exists with correct configuration"""
        print("\n--- Checking Cheeko Template ---")

        query = """
        SELECT id, agent_name, mem_model_id, chat_history_conf, sort, is_visible,
               lang_code, language, LEFT(system_prompt, 100) as prompt_preview
        FROM ai_agent_template
        WHERE agent_name = 'Cheeko'
        """
        result = self.execute_query(query)

        if not result:
            print("[FAIL] Cheeko template not found!")
            return False

        cheeko = result[0]
        print(f"[OK] Cheeko template found:")
        print(f"  - ID: {cheeko[0]}")
        print(f"  - Name: {cheeko[1]}")
        print(f"  - Memory Model: {cheeko[2]} (Expected: Memory_mem_local_short)")
        print(f"  - Chat History: {cheeko[3]} (Expected: 1)")
        print(f"  - Sort: {cheeko[4]} (Expected: 0)")
        print(f"  - Visible: {cheeko[5]} (Expected: 1)")
        print(f"  - Language: {cheeko[6]} {cheeko[7]} (Expected: en English)")
        print(f"  - Prompt Preview: {cheeko[8][:50]}...")

        # Check if configuration matches expectations
        checks = [
            (cheeko[2] == 'Memory_mem_local_short', "Memory Model"),
            (int(cheeko[3]) == 1, "Chat History Config"),
            (int(cheeko[4]) == 0, "Sort Order"),
            (int(cheeko[5]) == 1, "Visibility"),
            (cheeko[6] == 'en', "Language Code"),
            ('Cheeko' in cheeko[8], "Prompt contains Cheeko")
        ]

        all_passed = True
        for check_passed, check_name in checks:
            status = "[OK]" if check_passed else "[FAIL]"
            print(f"  {status} {check_name}")
            if not check_passed:
                all_passed = False

        return all_passed

    def verify_database_structure(self):
        """Check that expected tables exist"""
        print("\n--- Checking Database Structure ---")

        expected_tables = [
            'ai_agent', 'ai_agent_template', 'ai_agent_chat_history',
            'ai_device', 'ai_model_config', 'ai_model_provider', 'ai_tts_voice',
            'sys_dict_data', 'sys_dict_type', 'sys_params'
        ]

        query = "SHOW TABLES"
        result = self.execute_query(query)
        existing_tables = [table[0] for table in result if not table[0].startswith('DATABASECHANGE')]

        print(f"[INFO] Found {len(existing_tables)} tables in database")

        missing_tables = [t for t in expected_tables if t not in existing_tables]
        if missing_tables:
            print(f"[FAIL] Missing tables: {', '.join(missing_tables)}")
            return False
        else:
            print("[OK] All expected tables exist")

        # Show row counts for key tables
        key_tables = ['ai_agent_template', 'ai_agent', 'ai_model_config', 'ai_model_provider', 'ai_tts_voice']
        for table in key_tables:
            if table in existing_tables:
                count_result = self.execute_query(f"SELECT COUNT(*) FROM `{table}`")
                count = count_result[0][0] if count_result else 0
                print(f"  - {table}: {count} rows")

        return True

    def verify_template_count(self):
        """Check that only one template exists (Cheeko)"""
        print("\n--- Checking Template Count ---")

        query = "SELECT COUNT(*) as total, GROUP_CONCAT(agent_name) as names FROM ai_agent_template"
        result = self.execute_query(query)

        if not result:
            print("[FAIL] Cannot query templates")
            return False

        total, names = result[0]
        print(f"[INFO] Found {total} template(s): {names}")

        if total == 1 and names == "Cheeko":
            print("[OK] Exactly one template (Cheeko) exists as expected")
            return True
        else:
            print(f"[FAIL] Expected 1 Cheeko template, found {total}: {names}")
            return False

    def run_verification(self):
        """Run all verification checks"""
        print("=" * 60)
        print("XIAOZHI ESP32 NEW DATABASE VERIFICATION")
        print(f"Database: {self.config['database']}")
        print(f"Host: {self.config['host']}:{self.config['port']}")
        print("=" * 60)

        checks = [
            ("Database Structure", self.verify_database_structure),
            ("Template Count", self.verify_template_count),
            ("Cheeko Template", self.verify_cheeko_template)
        ]

        results = {}
        for check_name, check_function in checks:
            print(f"\n{check_name}...")
            results[check_name] = check_function()

        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY:")
        all_passed = True
        for check_name, passed in results.items():
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False

        print("=" * 60)
        if all_passed:
            print("RESULT: ALL CHECKS PASSED!")
            print("Your new database is ready for use with manager-api!")
        else:
            print("RESULT: SOME CHECKS FAILED!")
            print("Please review the migration and fix issues.")

        return all_passed

def main():
    """Main function"""
    verifier = NewDatabaseVerifier()

    if not verifier.connect():
        return 1

    try:
        success = verifier.run_verification()
        return 0 if success else 1
    finally:
        verifier.disconnect()

if __name__ == "__main__":
    sys.exit(main())