#!/usr/bin/env python3
"""
Verification script for the new manager_api database
"""

import mysql.connector
from mysql.connector import Error
import sys

class NewDatabaseVerifier:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'port': 3307,
            'user': 'manager',  # Using the user that worked for database creation
            'password': 'managerpassword',  # Original password
            'database': 'manager_api',  # Your new database
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

    def check_database_tables(self):
        """Check what tables exist in the database"""
        print("\n--- Checking Database Tables ---")

        query = "SHOW TABLES"
        result = self.execute_query(query)

        if not result:
            print("[INFO] Database appears to be empty (no tables found)")
            print("       This is normal if migration hasn't been run yet")
            return False

        tables = [table[0] for table in result]
        print(f"[INFO] Found {len(tables)} tables:")
        for table in tables[:10]:  # Show first 10 tables
            print(f"  - {table}")
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more")

        expected_tables = [
            'ai_agent', 'ai_agent_template', 'ai_model_config',
            'ai_model_provider', 'ai_tts_voice'
        ]

        missing = [t for t in expected_tables if t not in tables]
        if missing:
            print(f"[INFO] Missing key tables: {', '.join(missing)}")
            print("       Run the migration script first")
            return False
        else:
            print("[OK] All key tables present")
            return True

    def verify_cheeko_template(self):
        """Check if Cheeko template exists"""
        print("\n--- Checking Cheeko Template ---")

        query = """
        SELECT id, agent_name, mem_model_id, chat_history_conf, sort, is_visible,
               lang_code, language, LEFT(system_prompt, 100) as prompt_preview
        FROM ai_agent_template
        WHERE agent_name = 'Cheeko'
        """
        result = self.execute_query(query)

        if not result:
            print("[INFO] Cheeko template not found")
            print("       This is expected if migration hasn't been run yet")
            return False

        cheeko = result[0]
        print(f"[OK] Cheeko template found:")
        print(f"  - ID: {cheeko[0]}")
        print(f"  - Memory Model: {cheeko[2]}")
        print(f"  - Chat History: {cheeko[3]} (Report Text enabled)")
        print(f"  - Default (sort=0): {cheeko[4] == 0}")
        print(f"  - Visible: {cheeko[5]}")
        print(f"  - Language: {cheeko[6]} {cheeko[7]}")

        return True

    def run_verification(self):
        """Run verification checks"""
        print("=" * 60)
        print("NEW DATABASE VERIFICATION")
        print(f"Database: {self.config['database']}")
        print(f"Host: {self.config['host']}:{self.config['port']}")
        print("=" * 60)

        # Check if tables exist
        has_tables = self.check_database_tables()

        if has_tables:
            # If tables exist, check Cheeko template
            has_cheeko = self.verify_cheeko_template()

            print("\n" + "=" * 60)
            if has_cheeko:
                print("RESULT: DATABASE IS READY!")
                print("Your database has been successfully migrated with Cheeko configuration.")
            else:
                print("RESULT: MIGRATION INCOMPLETE")
                print("Database has tables but missing Cheeko template.")
        else:
            print("\n" + "=" * 60)
            print("RESULT: MIGRATION NEEDED")
            print("Database is empty. Please run the migration script:")
            print("1. Open MySQL Workbench")
            print("2. File → Open SQL Script → migration_for_manager_api.sql")
            print("3. Execute the script")
            print("4. Run this verification again")

        print("=" * 60)
        return has_tables and (not has_tables or self.verify_cheeko_template())

def main():
    """Main function"""
    verifier = NewDatabaseVerifier()

    if not verifier.connect():
        return 1

    try:
        verifier.run_verification()
        return 0
    finally:
        verifier.disconnect()

if __name__ == "__main__":
    sys.exit(main())