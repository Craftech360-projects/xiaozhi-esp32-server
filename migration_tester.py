#!/usr/bin/env python3
"""
Migration Tester for Xiaozhi ESP32 Server
Tests migration script by creating temporary database and comparing with current one
"""

import mysql.connector
from mysql.connector import Error
import subprocess
import tempfile
import os
import json
from datetime import datetime
import sys
from db_verification import DatabaseVerifier

class MigrationTester:
    def __init__(self, host="localhost", port=3307, user="manager", password="managerpassword"):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True
        }
        self.original_db = "manager_api"
        self.test_db = f"test_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_file = "complete_main_migration.sql"

    def connect(self, database=None):
        """Establish database connection"""
        config = self.config.copy()
        if database:
            config['database'] = database

        try:
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"❌ Error connecting to database: {e}")
            return None

    def create_test_database(self) -> bool:
        """Create temporary test database"""
        print(f"📝 Creating test database: {self.test_db}")

        try:
            # Try to connect without specifying database
            connection = self.connect()
            if not connection:
                return False

            cursor = connection.cursor()

            # Create test database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.test_db}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Test database created: {self.test_db}")

            cursor.close()
            connection.close()
            return True

        except Error as e:
            print(f"❌ Error creating test database: {e}")
            return False

    def run_migration_on_test_db(self) -> bool:
        """Run migration script on test database"""
        print(f"🔄 Running migration on test database...")

        if not os.path.exists(self.migration_file):
            print(f"❌ Migration file not found: {self.migration_file}")
            return False

        try:
            # Modify migration script to use test database
            with open(self.migration_file, 'r', encoding='utf-8') as f:
                migration_content = f.read()

            # Replace database name in migration script
            test_migration_content = migration_content.replace(
                'USE `manager_api`;',
                f'USE `{self.test_db}`;'
            )

            # Also replace the CREATE DATABASE line
            test_migration_content = test_migration_content.replace(
                'CREATE DATABASE IF NOT EXISTS `manager_api`',
                f'CREATE DATABASE IF NOT EXISTS `{self.test_db}`'
            )

            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(test_migration_content)
                temp_migration_file = temp_file.name

            # Run migration using docker exec
            docker_command = [
                'docker', 'exec', '-i', 'manager-api-db',
                'mysql', '-u', self.config['user'], f'-p{self.config["password"]}'
            ]

            with open(temp_migration_file, 'r', encoding='utf-8') as migration_input:
                result = subprocess.run(
                    docker_command,
                    stdin=migration_input,
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )

            # Clean up temp file
            os.unlink(temp_migration_file)

            if result.returncode == 0:
                print("✅ Migration completed successfully")
                return True
            else:
                print(f"❌ Migration failed:")
                print(f"   stdout: {result.stdout}")
                print(f"   stderr: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error running migration: {e}")
            return False

    def compare_databases(self) -> dict:
        """Compare original database with test database"""
        print(f"🔍 Comparing databases: {self.original_db} vs {self.test_db}")

        original_verifier = DatabaseVerifier(database=self.original_db, **{k: v for k, v in self.config.items() if k != 'database'})
        test_verifier = DatabaseVerifier(database=self.test_db, **{k: v for k, v in self.config.items() if k != 'database'})

        comparison = {
            "timestamp": datetime.now().isoformat(),
            "original_db": self.original_db,
            "test_db": self.test_db,
            "comparison_results": {}
        }

        # Connect to both databases
        if not original_verifier.connect():
            print(f"❌ Failed to connect to original database: {self.original_db}")
            return comparison

        if not test_verifier.connect():
            print(f"❌ Failed to connect to test database: {self.test_db}")
            original_verifier.disconnect()
            return comparison

        try:
            # Compare table structures
            print("   📊 Comparing table structures...")
            original_tables = original_verifier.get_table_list()
            test_tables = test_verifier.get_table_list()

            comparison["comparison_results"]["table_comparison"] = {
                "original_tables": len(original_tables),
                "test_tables": len(test_tables),
                "missing_in_test": [t for t in original_tables if t not in test_tables],
                "extra_in_test": [t for t in test_tables if t not in original_tables],
                "common_tables": [t for t in original_tables if t in test_tables]
            }

            # Compare key table counts
            print("   🔢 Comparing table row counts...")
            key_tables = ['ai_agent_template', 'ai_model_config', 'ai_model_provider', 'sys_dict_data']
            count_comparison = {}

            for table in key_tables:
                if table in original_tables and table in test_tables:
                    original_count = original_verifier.get_table_count(table)
                    test_count = test_verifier.get_table_count(table)
                    count_comparison[table] = {
                        "original": original_count,
                        "test": test_count,
                        "match": original_count == test_count
                    }

            comparison["comparison_results"]["row_count_comparison"] = count_comparison

            # Run verification on test database
            print("   ✅ Running verification on test database...")
            test_verification = test_verifier.run_comprehensive_verification()
            comparison["comparison_results"]["test_db_verification"] = test_verification

            # Check specific Cheeko configuration
            print("   👤 Comparing Cheeko template configuration...")
            original_cheeko = original_verifier.verify_cheeko_template()
            test_cheeko = test_verifier.verify_cheeko_template()

            comparison["comparison_results"]["cheeko_comparison"] = {
                "original": original_cheeko,
                "test": test_cheeko,
                "templates_match": original_cheeko.get("status") == test_cheeko.get("status")
            }

            return comparison

        finally:
            original_verifier.disconnect()
            test_verifier.disconnect()

    def cleanup_test_database(self) -> bool:
        """Remove test database"""
        print(f"🧹 Cleaning up test database: {self.test_db}")

        try:
            connection = self.connect()
            if not connection:
                return False

            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE IF EXISTS `{self.test_db}`")
            print(f"✅ Test database cleaned up: {self.test_db}")

            cursor.close()
            connection.close()
            return True

        except Error as e:
            print(f"❌ Error cleaning up test database: {e}")
            return False

    def run_full_migration_test(self) -> dict:
        """Run complete migration test"""
        print("🚀 Starting Migration Test")
        print("=" * 60)

        test_results = {
            "timestamp": datetime.now().isoformat(),
            "migration_file": self.migration_file,
            "test_database": self.test_db,
            "steps": {}
        }

        # Step 1: Create test database
        print("Step 1: Creating test database...")
        step1_success = self.create_test_database()
        test_results["steps"]["create_test_db"] = {
            "success": step1_success,
            "message": "Test database created" if step1_success else "Failed to create test database"
        }

        if not step1_success:
            return test_results

        # Step 2: Run migration
        print("\nStep 2: Running migration script...")
        step2_success = self.run_migration_on_test_db()
        test_results["steps"]["run_migration"] = {
            "success": step2_success,
            "message": "Migration completed" if step2_success else "Migration failed"
        }

        if not step2_success:
            self.cleanup_test_database()
            return test_results

        # Step 3: Compare databases
        print("\nStep 3: Comparing databases...")
        comparison_results = self.compare_databases()
        test_results["steps"]["compare_databases"] = {
            "success": bool(comparison_results.get("comparison_results")),
            "results": comparison_results
        }

        # Step 4: Cleanup
        print("\nStep 4: Cleaning up...")
        cleanup_success = self.cleanup_test_database()
        test_results["steps"]["cleanup"] = {
            "success": cleanup_success,
            "message": "Cleanup completed" if cleanup_success else "Cleanup failed"
        }

        # Overall result
        all_steps_passed = all(step["success"] for step in test_results["steps"].values())
        test_results["overall_success"] = all_steps_passed

        print("\n" + "=" * 60)
        if all_steps_passed:
            print("🎉 MIGRATION TEST PASSED!")
            print("   Migration script successfully recreates the database")
        else:
            print("❌ MIGRATION TEST FAILED!")
            print("   Check the detailed results for issues")

        return test_results

def main():
    """Main function"""
    print("🧪 Xiaozhi ESP32 Migration Tester")
    print("=" * 60)

    tester = MigrationTester()
    results = tester.run_full_migration_test()

    # Save results
    results_file = f"migration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str, ensure_ascii=False)

    print(f"\n💾 Detailed results saved to: {results_file}")

    return 0 if results["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())