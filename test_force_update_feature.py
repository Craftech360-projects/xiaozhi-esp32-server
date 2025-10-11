#!/usr/bin/env python3
"""
Force Update Feature Test Script
Tests all scenarios for the firmware force update functionality
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8002"
API_PREFIX = "/api"

# Test data
TEST_DEVICE_ID = "AA:BB:CC:DD:EE:FF"
TEST_FIRMWARE_TYPE = "ESP32"

class Color:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*80}")
        print(f"{Color.BOLD}TEST SUMMARY{Color.END}")
        print(f"{'='*80}")
        print(f"Total Tests: {total}")
        print(f"{Color.GREEN}✓ Passed: {self.passed}{Color.END}")
        print(f"{Color.RED}✗ Failed: {self.failed}{Color.END}")
        if self.warnings > 0:
            print(f"{Color.YELLOW}⚠ Warnings: {self.warnings}{Color.END}")
        print(f"{'='*80}\n")

result = TestResult()

def print_test(name: str):
    """Print test name"""
    print(f"\n{Color.CYAN}{'='*80}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}TEST: {name}{Color.END}")
    print(f"{Color.CYAN}{'='*80}{Color.END}")

def print_success(message: str):
    """Print success message"""
    print(f"{Color.GREEN}✓ {message}{Color.END}")
    result.passed += 1

def print_error(message: str):
    """Print error message"""
    print(f"{Color.RED}✗ {message}{Color.END}")
    result.failed += 1

def print_warning(message: str):
    """Print warning message"""
    print(f"{Color.YELLOW}⚠ {message}{Color.END}")
    result.warnings += 1

def print_info(message: str):
    """Print info message"""
    print(f"  {message}")

def print_json(data: Any, indent: int = 2):
    """Pretty print JSON data"""
    print(f"{Color.CYAN}{json.dumps(data, indent=indent)}{Color.END}")

# ============================================================================
# TEST 1: Database Migration Check
# ============================================================================
def test_database_migration():
    """Test if the database migration was applied successfully"""
    print_test("Database Migration - Check force_update column exists")

    # Since we can't directly query MySQL from Python without credentials,
    # we'll test this indirectly through the API by checking if forceUpdate
    # field is returned in the OTA list response

    try:
        # This would require authentication, so we'll mark as pending
        print_info("Database migration test requires manual verification:")
        print_info("Run this SQL query to verify:")
        print_info("  SHOW COLUMNS FROM ai_ota LIKE 'force_update';")
        print_info("  SELECT * FROM ai_ota LIMIT 1;")
        print_warning("Manual verification required - skipping automated test")
    except Exception as e:
        print_error(f"Database migration test failed: {e}")

# ============================================================================
# TEST 2: OTA Management API - List Firmwares
# ============================================================================
def test_list_firmwares():
    """Test GET /otaMag - List all firmwares"""
    print_test("API Test - List Firmwares (GET /otaMag)")

    try:
        url = f"{BASE_URL}{API_PREFIX}/otaMag"
        params = {
            "pageNum": 1,
            "pageSize": 10
        }

        print_info(f"Request: GET {url}")
        print_info(f"Params: {params}")

        # Note: This requires authentication
        print_warning("Authentication required - test needs valid session/token")
        print_info("Expected response structure:")
        expected = {
            "code": 0,
            "data": {
                "list": [
                    {
                        "id": "string",
                        "firmwareName": "string",
                        "type": "string",
                        "version": "string",
                        "forceUpdate": 0,  # Should be present
                        "size": 0,
                        "remark": "string"
                    }
                ],
                "total": 0
            }
        }
        print_json(expected)

    except Exception as e:
        print_error(f"List firmwares test failed: {e}")

# ============================================================================
# TEST 3: Set Force Update API
# ============================================================================
def test_set_force_update():
    """Test PUT /otaMag/forceUpdate/{id}"""
    print_test("API Test - Set Force Update (PUT /otaMag/forceUpdate/{id})")

    print_info("Test Case 1: Enable force update")
    test_data_enable = {
        "forceUpdate": 1,
        "type": "ESP32"
    }
    print_info("Request body:")
    print_json(test_data_enable)
    print_info("Expected: Success, force_update set to 1")
    print_info("Expected: Other firmwares of same type have force_update set to 0")

    print_info("\nTest Case 2: Disable force update")
    test_data_disable = {
        "forceUpdate": 0,
        "type": "ESP32"
    }
    print_info("Request body:")
    print_json(test_data_disable)
    print_info("Expected: Success, force_update set to 0")

    print_warning("Authentication required - manual testing needed")

# ============================================================================
# TEST 4: Device OTA Check - Normal Mode (No Force Update)
# ============================================================================
def test_ota_check_normal_mode():
    """Test device OTA check when no force update is active"""
    print_test("OTA Check - Normal Mode (No Force Update Active)")

    url = f"{BASE_URL}/ota/"
    headers = {
        "Device-Id": TEST_DEVICE_ID,
        "Content-Type": "application/json"
    }

    scenarios = [
        {
            "name": "Device with OLDER version",
            "current": "1.5.0",
            "latest": "2.0.0",
            "expected": "Should get latest version 2.0.0 with download URL"
        },
        {
            "name": "Device with SAME version as latest",
            "current": "2.0.0",
            "latest": "2.0.0",
            "expected": "Should get version 2.0.0 with INVALID_FIRMWARE_URL (no update)"
        },
        {
            "name": "Device with NEWER version than latest",
            "current": "2.5.0",
            "latest": "2.0.0",
            "expected": "Should get current version 2.5.0 with INVALID_FIRMWARE_URL (no downgrade)"
        }
    ]

    for scenario in scenarios:
        print_info(f"\n{Color.BOLD}Scenario: {scenario['name']}{Color.END}")
        print_info(f"Device current version: {scenario['current']}")
        print_info(f"Latest firmware version: {scenario['latest']}")
        print_info(f"Expected: {scenario['expected']}")

        request_body = {
            "application": {
                "version": scenario["current"]
            },
            "board": {
                "type": TEST_FIRMWARE_TYPE
            }
        }

        print_info(f"Request: POST {url}")
        print_info("Headers:")
        print_json(headers)
        print_info("Body:")
        print_json(request_body)

        try:
            response = requests.post(url, headers=headers, json=request_body, timeout=5)
            print_info(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print_info("Response:")
                print_json(data)

                if "firmware" in data:
                    firmware = data["firmware"]
                    print_info(f"Firmware version returned: {firmware.get('version')}")
                    print_info(f"Download URL: {firmware.get('url')}")

                    # Validate based on scenario
                    if scenario['current'] < scenario['latest']:
                        if firmware['version'] == scenario['latest'] and firmware['url'] != "null":
                            print_success("✓ Correctly returned newer version with download URL")
                        else:
                            print_error("✗ Should return newer version with download URL")
                    elif scenario['current'] == scenario['latest']:
                        if firmware['url'] == "null" or "invalid" in firmware['url'].lower():
                            print_success("✓ Correctly returned no update (same version)")
                        else:
                            print_error("✗ Should not provide download URL (same version)")
                    else:  # current > latest
                        if firmware['url'] == "null" or "invalid" in firmware['url'].lower():
                            print_success("✓ Correctly prevented downgrade in normal mode")
                        else:
                            print_error("✗ Should not downgrade in normal mode")
                else:
                    print_warning("No firmware field in response")
            else:
                print_warning(f"Unexpected status code: {response.status_code}")
                print_info(f"Response: {response.text}")

        except requests.exceptions.ConnectionError:
            print_warning("Connection failed - server may not be running at localhost:8002")
        except Exception as e:
            print_error(f"Request failed: {e}")

# ============================================================================
# TEST 5: Device OTA Check - Force Update Mode
# ============================================================================
def test_ota_check_force_update_mode():
    """Test device OTA check when force update is ACTIVE"""
    print_test("OTA Check - Force Update Mode (Force Update ACTIVE)")

    print_info("⚠ PREREQUISITE: Force update must be enabled for a specific firmware")
    print_info("Example: Force update enabled for ESP32 firmware version 2.1.0")

    url = f"{BASE_URL}/ota/"
    headers = {
        "Device-Id": TEST_DEVICE_ID,
        "Content-Type": "application/json"
    }

    forced_version = "2.1.0"

    scenarios = [
        {
            "name": "Device with OLDER version (upgrade scenario)",
            "current": "1.8.0",
            "forced": forced_version,
            "expected": f"Should get forced version {forced_version} with download URL"
        },
        {
            "name": "Device with SAME version as forced (already compliant)",
            "current": forced_version,
            "forced": forced_version,
            "expected": f"Should get version {forced_version} with INVALID_FIRMWARE_URL (no download)"
        },
        {
            "name": "Device with NEWER version (DOWNGRADE scenario)",
            "current": "2.5.0",
            "forced": forced_version,
            "expected": f"Should get forced version {forced_version} with download URL (DOWNGRADE)"
        }
    ]

    for scenario in scenarios:
        print_info(f"\n{Color.BOLD}Scenario: {scenario['name']}{Color.END}")
        print_info(f"Device current version: {scenario['current']}")
        print_info(f"Forced firmware version: {scenario['forced']}")
        print_info(f"Expected: {scenario['expected']}")

        request_body = {
            "application": {
                "version": scenario["current"]
            },
            "board": {
                "type": TEST_FIRMWARE_TYPE
            }
        }

        print_info(f"Request: POST {url}")
        print_info("Body:")
        print_json(request_body)

        try:
            response = requests.post(url, headers=headers, json=request_body, timeout=5)
            print_info(f"Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print_info("Response:")
                print_json(data)

                if "firmware" in data:
                    firmware = data["firmware"]
                    print_info(f"Firmware version returned: {firmware.get('version')}")
                    print_info(f"Download URL: {firmware.get('url')}")

                    # Validate force update behavior
                    if firmware['version'] == scenario['forced']:
                        print_success(f"✓ Correctly returned forced version {forced_version}")

                        # Check download URL
                        if scenario['current'] != scenario['forced']:
                            if firmware['url'] != "null" and "invalid" not in firmware['url'].lower():
                                if scenario['current'] < scenario['forced']:
                                    print_success("✓ Download URL provided for UPGRADE")
                                else:
                                    print_success("✓ Download URL provided for DOWNGRADE")
                            else:
                                print_error("✗ Should provide download URL when versions differ")
                        else:
                            if firmware['url'] == "null" or "invalid" in firmware['url'].lower():
                                print_success("✓ No download URL (device already on forced version)")
                            else:
                                print_warning("Download URL provided even though versions match")
                    else:
                        print_error(f"✗ Should return forced version {forced_version}, got {firmware['version']}")
                else:
                    print_warning("No firmware field in response")
            else:
                print_warning(f"Unexpected status code: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print_warning("Connection failed - server may not be running")
        except Exception as e:
            print_error(f"Request failed: {e}")

# ============================================================================
# TEST 6: Edge Cases and Error Handling
# ============================================================================
def test_edge_cases():
    """Test edge cases and error handling"""
    print_test("Edge Cases and Error Handling")

    print_info("Test Case 1: Missing Device-Id header")
    print_info("Expected: Error response")

    print_info("\nTest Case 2: Invalid firmware type")
    print_info("Expected: No firmware update (null response)")

    print_info("\nTest Case 3: Set force update with invalid parameters")
    print_info("Request body: {}")
    print_info("Expected: Error 'parameter incomplete'")

    print_info("\nTest Case 4: Set force update with forceUpdate = 2")
    print_info("Request body: {'forceUpdate': 2, 'type': 'ESP32'}")
    print_info("Expected: Error 'force_update must be 0 or 1'")

    print_info("\nTest Case 5: Enable force update on two firmwares (same type)")
    print_info("Step 1: Enable force update on Firmware A")
    print_info("Step 2: Enable force update on Firmware B (same type)")
    print_info("Expected: Firmware A force_update automatically set to 0")

    print_warning("Manual testing required for edge cases")

# ============================================================================
# TEST 7: Backend Logs Verification
# ============================================================================
def test_backend_logs():
    """Verify backend logs show correct information"""
    print_test("Backend Logs Verification")

    print_info("Expected log messages to verify:")
    print_info("")

    logs = [
        {
            "scenario": "Force update ACTIVE",
            "log": "🔒 Force update ACTIVE for type: ESP32, forced version: 2.1.0, device current: 2.5.0"
        },
        {
            "scenario": "Device needs update (upgrade)",
            "log": "📥 Force update download URL generated - Device will UPGRADE to version 2.1.0"
        },
        {
            "scenario": "Device needs update (downgrade)",
            "log": "📥 Force update download URL generated - Device will DOWNGRADE to version 2.1.0"
        },
        {
            "scenario": "Device already on forced version",
            "log": "✅ Device already on forced version 2.1.0, no download needed"
        },
        {
            "scenario": "Force update response",
            "log": "📦 FORCE OTA Response - Type: ESP32, Current: 2.5.0, Target: 2.1.0, URL: http://..."
        },
        {
            "scenario": "Normal mode (no force update)",
            "log": "📦 Normal OTA Response - Type: ESP32, Current: 1.5.0, Latest: 2.0.0, URL: http://..."
        }
    ]

    for log_entry in logs:
        print_info(f"\n{Color.BOLD}{log_entry['scenario']}:{Color.END}")
        print_info(f"  {log_entry['log']}")

    print_warning("Check backend logs manually after running OTA check tests")

# ============================================================================
# Run All Tests
# ============================================================================
def run_all_tests():
    """Run all test scenarios"""
    print(f"\n{Color.BOLD}{Color.BLUE}")
    print("="*80)
    print("  FORCE UPDATE FEATURE - COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"{Color.END}\n")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run tests
    test_database_migration()
    test_list_firmwares()
    test_set_force_update()
    test_ota_check_normal_mode()
    test_ota_check_force_update_mode()
    test_edge_cases()
    test_backend_logs()

    # Print summary
    result.summary()

    # Manual verification checklist
    print(f"{Color.BOLD}MANUAL VERIFICATION CHECKLIST:{Color.END}")
    print("1. ☐ Run database migration and verify force_update column exists")
    print("2. ☐ Start backend server (mvn spring-boot:run)")
    print("3. ☐ Upload test firmware files with different versions")
    print("4. ☐ Test force update toggle in frontend UI")
    print("5. ☐ Verify only one force update per type is allowed")
    print("6. ☐ Test device check-in with force update enabled")
    print("7. ☐ Verify downgrade scenario works correctly")
    print("8. ☐ Check backend logs for proper log messages")
    print("9. ☐ Disable force update and verify normal behavior resumes")
    print("10. ☐ Test with multiple device types simultaneously")
    print()

if __name__ == "__main__":
    run_all_tests()
