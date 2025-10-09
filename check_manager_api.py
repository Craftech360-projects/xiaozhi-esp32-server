#!/usr/bin/env python3
"""
Manager API Health Check
Verifies that the Manager API is running and accessible
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8002/toy"
SECRET = "da11d988-f105-4e71-b095-da62ada82189"  # Server secret from sys_params

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def test_endpoint(name, method, url, headers=None, json_data=None, expect_status=200):
    """Test a single endpoint"""
    print(f"\n{YELLOW}Testing: {name}{RESET}")
    print(f"  URL: {method} {url}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=5)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json_data, timeout=5)

        print(f"  Status: {response.status_code}")

        if response.status_code == expect_status or response.status_code == 200:
            try:
                data = response.json()
                print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
            except:
                print(f"  Response: {response.text[:200]}")
            print(f"  {GREEN}✅ SUCCESS{RESET}")
            return True
        else:
            print(f"  {RED}❌ FAILED - Expected {expect_status}, got {response.status_code}{RESET}")
            print(f"  Response: {response.text[:200]}")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  {RED}❌ CONNECTION ERROR - Manager API not running?{RESET}")
        return False
    except Exception as e:
        print(f"  {RED}❌ ERROR: {e}{RESET}")
        return False

print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Manager API Health Check{RESET}")
print(f"{BLUE}Base URL: {BASE_URL}{RESET}")
print(f"{BLUE}{'='*60}{RESET}")

# Prepare headers with secret
auth_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SECRET}"
}

# Test 1: Basic health check (if exists)
test_endpoint(
    "Health Check",
    "GET",
    f"{BASE_URL}/health",
    headers=auth_headers,
    expect_status=200
)

# Test 2: Config endpoint (should work with secret)
test_endpoint(
    "Server Config",
    "POST",
    f"{BASE_URL}/config/server-base",
    headers=auth_headers
)

# Test 3: Agent prompt endpoint
test_endpoint(
    "Agent Prompt (will fail without device)",
    "POST",
    f"{BASE_URL}/config/agent-prompt",
    headers=auth_headers,
    json_data={"macAddress": "test:mac:address"},
    expect_status=200  # May fail but shows endpoint is working
)

# Test 4: Child profile endpoint (the one we need)
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Main Test: Child Profile by MAC{RESET}")
print(f"{BLUE}{'='*60}{RESET}")

success = test_endpoint(
    "Child Profile by MAC (will fail without setup)",
    "POST",
    f"{BASE_URL}/config/child-profile-by-mac",
    headers=auth_headers,
    json_data={"macAddress": "68:25:dd:bb:f3:a0"},
    expect_status=200
)

# Summary
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Summary{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

if success:
    print(f"{GREEN}✅ Manager API is running and responding!{RESET}")
    print(f"{GREEN}✅ /config/child-profile-by-mac endpoint exists{RESET}")
    print(f"\n{YELLOW}If you see errors above, it's likely because:{RESET}")
    print(f"  1. Device doesn't exist for the MAC address")
    print(f"  2. Kid profile not created yet")
    print(f"  3. Kid not linked to device")
    print(f"\n{YELLOW}Run the SQL setup script to fix this!{RESET}")
else:
    print(f"{RED}❌ Manager API is not responding correctly{RESET}")
    print(f"\n{YELLOW}Troubleshooting:{RESET}")
    print(f"  1. Make sure Manager API is running:")
    print(f"     cd D:\\cheekofinal\\xiaozhi-esp32-server\\main\\manager-api")
    print(f'     mvn spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"')
    print(f"  2. Check if port 8002 is in use")
    print(f"  3. Check application-dev.yml configuration")

print()
