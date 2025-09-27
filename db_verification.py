#!/usr/bin/env python3
"""
Database Verification Script for Xiaozhi ESP32 Server
Compares current database with migration script expectations
"""

import mysql.connector
from mysql.connector import Error
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
import sys
import os

class DatabaseVerifier:
    def __init__(self, host="localhost", port=3307, user="manager", password="managerpassword", database="manager_api"):
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
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
                print(f"✅ Connected to MySQL database: {self.config['database']}")
                return True
        except Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Database connection closed")

    def execute_query(self, query: str) -> List[Tuple]:
        """Execute SELECT query and return results"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"❌ Error executing query: {e}")
            return []

    def get_table_list(self) -> List[str]:
        """Get list of all tables in database"""
        query = "SHOW TABLES"
        results = self.execute_query(query)
        return [table[0] for table in results if not table[0].startswith('DATABASECHANGE')]

    def get_table_schema(self, table_name: str) -> Dict:
        """Get detailed schema information for a table"""
        query = f"DESCRIBE `{table_name}`"
        results = self.execute_query(query)

        schema = {}
        for field, type_, null, key, default, extra in results:
            schema[field] = {
                'type': type_,
                'null': null == 'YES',
                'key': key,
                'default': default,
                'extra': extra
            }
        return schema

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        query = f"SELECT COUNT(*) FROM `{table_name}`"
        result = self.execute_query(query)
        return result[0][0] if result else 0

    def verify_cheeko_template(self) -> Dict[str, Any]:
        """Verify Cheeko template configuration"""
        query = """
        SELECT id, agent_name, mem_model_id, chat_history_conf, sort, is_visible, lang_code, language,
               LEFT(system_prompt, 100) as prompt_preview
        FROM ai_agent_template
        WHERE agent_name = 'Cheeko'
        """
        result = self.execute_query(query)

        if not result:
            return {"status": "❌ FAIL", "error": "Cheeko template not found"}

        cheeko = result[0]
        expected = {
            'mem_model_id': 'Memory_mem_local_short',
            'chat_history_conf': 1,
            'sort': 0,
            'is_visible': 1,
            'lang_code': 'en',
            'language': 'English'
        }

        verification = {
            "status": "✅ PASS",
            "template_found": True,
            "checks": {}
        }

        # Check each expected value
        for i, (field, expected_value) in enumerate(expected.items(), 1):
            actual_value = cheeko[i + 1]  # Offset for id and agent_name
            if field == 'chat_history_conf':
                actual_value = int(actual_value)

            if actual_value == expected_value:
                verification["checks"][field] = f"✅ {actual_value}"
            else:
                verification["checks"][field] = f"❌ Expected: {expected_value}, Got: {actual_value}"
                verification["status"] = "❌ FAIL"

        # Check prompt contains Cheeko identity
        prompt_preview = cheeko[8]
        if "Cheeko" in prompt_preview and "playful AI companion" in prompt_preview:
            verification["checks"]["system_prompt"] = "✅ Contains Cheeko identity"
        else:
            verification["checks"]["system_prompt"] = "❌ Missing Cheeko identity"
            verification["status"] = "❌ FAIL"

        return verification

    def verify_template_count(self) -> Dict[str, Any]:
        """Verify only one template exists (Cheeko)"""
        query = "SELECT COUNT(*) as total, GROUP_CONCAT(agent_name) as names FROM ai_agent_template"
        result = self.execute_query(query)

        if not result:
            return {"status": "❌ FAIL", "error": "Cannot query templates"}

        total, names = result[0]

        if total == 1 and names == "Cheeko":
            return {
                "status": "✅ PASS",
                "total_templates": total,
                "template_names": names,
                "message": "Only Cheeko template exists as expected"
            }
        else:
            return {
                "status": "❌ FAIL",
                "total_templates": total,
                "template_names": names,
                "message": f"Expected 1 Cheeko template, found {total}: {names}"
            }

    def verify_agents_use_cheeko(self) -> Dict[str, Any]:
        """Verify agents are using Cheeko personality"""
        queries = {
            "total_agents": "SELECT COUNT(*) FROM ai_agent",
            "cheeko_agents": "SELECT COUNT(*) FROM ai_agent WHERE system_prompt LIKE '%Cheeko%'",
            "memory_config": "SELECT COUNT(*) FROM ai_agent WHERE mem_model_id = 'Memory_mem_local_short'",
            "chat_history": "SELECT COUNT(*) FROM ai_agent WHERE chat_history_conf = 1"
        }

        results = {}
        for key, query in queries.items():
            result = self.execute_query(query)
            results[key] = result[0][0] if result else 0

        verification = {
            "status": "✅ PASS",
            "checks": {}
        }

        # Verify configurations
        if results["cheeko_agents"] == results["total_agents"] and results["total_agents"] > 0:
            verification["checks"]["cheeko_personality"] = f"✅ All {results['total_agents']} agents use Cheeko"
        else:
            verification["checks"]["cheeko_personality"] = f"❌ {results['cheeko_agents']}/{results['total_agents']} agents use Cheeko"
            verification["status"] = "❌ FAIL"

        if results["memory_config"] == results["total_agents"] and results["total_agents"] > 0:
            verification["checks"]["memory_model"] = f"✅ All agents use Memory_mem_local_short"
        else:
            verification["checks"]["memory_model"] = f"❌ {results['memory_config']}/{results['total_agents']} agents use correct memory"
            verification["status"] = "❌ FAIL"

        if results["chat_history"] == results["total_agents"] and results["total_agents"] > 0:
            verification["checks"]["chat_history_conf"] = f"✅ All agents have Report Text enabled"
        else:
            verification["checks"]["chat_history_conf"] = f"❌ {results['chat_history']}/{results['total_agents']} agents have Report Text enabled"
            verification["status"] = "❌ FAIL"

        return verification

    def verify_database_structure(self) -> Dict[str, Any]:
        """Verify database has expected structure"""
        expected_tables = [
            'ai_agent', 'ai_agent_template', 'ai_agent_chat_history', 'ai_agent_chat_audio',
            'ai_device', 'ai_model_config', 'ai_model_provider', 'ai_tts_voice',
            'sys_dict_data', 'sys_dict_type', 'sys_params', 'sys_user', 'parent_profile'
        ]

        actual_tables = self.get_table_list()

        verification = {
            "status": "✅ PASS",
            "expected_tables": len(expected_tables),
            "actual_tables": len(actual_tables),
            "missing_tables": [],
            "extra_tables": [],
            "table_counts": {}
        }

        # Check for missing tables
        for table in expected_tables:
            if table not in actual_tables:
                verification["missing_tables"].append(table)
                verification["status"] = "❌ FAIL"
            else:
                verification["table_counts"][table] = self.get_table_count(table)

        # Check for extra tables (excluding system tables)
        for table in actual_tables:
            if table not in expected_tables and not table.startswith(('DATABASECHANGE', 'sys_')):
                verification["extra_tables"].append(table)

        return verification

    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run all verification checks"""
        print("🔍 Starting Comprehensive Database Verification...")
        print("=" * 60)

        verifications = {
            "timestamp": datetime.now().isoformat(),
            "database": self.config['database'],
            "tests": {}
        }

        # Test 1: Database Structure
        print("1. Verifying Database Structure...")
        verifications["tests"]["database_structure"] = self.verify_database_structure()
        self._print_verification_result("Database Structure", verifications["tests"]["database_structure"])

        # Test 2: Template Configuration
        print("\n2. Verifying Template Configuration...")
        verifications["tests"]["template_count"] = self.verify_template_count()
        self._print_verification_result("Template Count", verifications["tests"]["template_count"])

        # Test 3: Cheeko Template Details
        print("\n3. Verifying Cheeko Template Details...")
        verifications["tests"]["cheeko_template"] = self.verify_cheeko_template()
        self._print_verification_result("Cheeko Template", verifications["tests"]["cheeko_template"])

        # Test 4: Agent Configuration
        print("\n4. Verifying Agent Configuration...")
        verifications["tests"]["agent_configuration"] = self.verify_agents_use_cheeko()
        self._print_verification_result("Agent Configuration", verifications["tests"]["agent_configuration"])

        # Overall Result
        all_passed = all(test["status"].startswith("✅") for test in verifications["tests"].values())
        verifications["overall_status"] = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"

        print("\n" + "=" * 60)
        print(f"📊 OVERALL RESULT: {verifications['overall_status']}")
        print("=" * 60)

        return verifications

    def _print_verification_result(self, test_name: str, result: Dict[str, Any]):
        """Print formatted verification result"""
        print(f"   {result['status']} {test_name}")

        if "checks" in result:
            for check, status in result["checks"].items():
                print(f"      └─ {check}: {status}")

        if "message" in result:
            print(f"      └─ {result['message']}")

        if "missing_tables" in result and result["missing_tables"]:
            print(f"      └─ Missing tables: {', '.join(result['missing_tables'])}")

        if "table_counts" in result:
            print(f"      └─ Key table counts:")
            for table, count in result["table_counts"].items():
                if table in ['ai_agent_template', 'ai_agent', 'ai_model_config']:
                    print(f"         • {table}: {count} rows")

def main():
    """Main verification function"""
    # Set UTF-8 encoding for Windows console
    if sys.platform.startswith('win'):
        os.system('chcp 65001 >nul')

    print("🚀 Xiaozhi ESP32 Database Verification Tool")
    print("=" * 60)

    verifier = DatabaseVerifier()

    if not verifier.connect():
        sys.exit(1)

    try:
        results = verifier.run_comprehensive_verification()

        # Save results to file
        results_file = f"verification_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Detailed results saved to: {results_file}")

        # Return appropriate exit code
        if results["overall_status"].startswith("✅"):
            print("✅ Verification completed successfully!")
            return 0
        else:
            print("❌ Verification found issues!")
            return 1

    finally:
        verifier.disconnect()

if __name__ == "__main__":
    sys.exit(main())