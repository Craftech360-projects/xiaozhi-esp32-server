#!/usr/bin/env python3
"""
Simple Kid Profile API Test Script
Focuses on testing the child-profile-by-mac endpoint (no login required)
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "http://localhost:8002/toy"
SECRET = "da11d988-f105-4e71-b095-da62ada82189"  # Server secret from sys_params
MAC_ADDRESS = "68:25:dd:bb:f3:a0"
KID_NAME = "Rahul"
KID_AGE = 10
KID_GENDER = "male"
KID_DOB = (datetime.now() - timedelta(days=365*KID_AGE)).strftime("%Y-%m-%d")

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login_user(username, password):
    """Login to get user authentication token (like Flutter app does)"""
    print(f"\n{BLUE}🔐 Logging in as: {username}{RESET}")

    try:
        # Generate captcha ID (like Flutter app - using bypass for mobile)
        captcha_id = str(uuid.uuid4())

        # Login request (same as Flutter app)
        response = requests.post(
            f"{BASE_URL}/user/login",
            headers={'Content-Type': 'application/json'},
            json={
                'username': username,
                'mobile': username,  # Some endpoints expect mobile field
                'password': password,
                'captcha': 'MOBILE_APP_BYPASS',  # Special bypass token for mobile apps
                'captchaId': captcha_id
            },
            timeout=10
        )

        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Check for success (code: 0 means success)
            if data.get('code') == 0 and data.get('data', {}).get('token'):
                token = data['data']['token']
                print(f"  {GREEN}✅ Login successful!{RESET}")
                print(f"  {GREEN}Token: {token[:20]}...{RESET}")
                return token
            else:
                error_msg = data.get('msg', 'Login failed')
                print(f"  {RED}❌ Login failed: {error_msg}{RESET}")
                return None
        else:
            print(f"  {RED}❌ HTTP Error {response.status_code}{RESET}")
            return None

    except Exception as e:
        print(f"  {RED}❌ Login error: {e}{RESET}")
        return None

print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Kid Profile API Test - Simple Version{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

# Step 1: Manual SQL setup instructions
print(f"{YELLOW}Step 1: Create Kid Profile in MySQL{RESET}")
print(f"{BLUE}Run this SQL:{RESET}\n")
print(f"""
-- Create kid profile (id will auto-increment)
INSERT INTO kid_profile (
    user_id, name, date_of_birth, gender, interests, avatar_url,
    creator, create_date, updater, update_date
) VALUES (
    1, '{KID_NAME}', '{KID_DOB}', '{KID_GENDER}',
    '[\"games\", \"sports\", \"science\"]', 'https://example.com/avatar.jpg',
    1, NOW(), 1, NOW()
);

-- Get the auto-generated kid_id (id is the unique primary key)
SELECT id, name, date_of_birth FROM kid_profile ORDER BY id DESC LIMIT 1;
""")

kid_id_input = input(f"\n{YELLOW}Enter the kid_id from the query above: {RESET}")
kid_id = int(kid_id_input) if kid_id_input.strip() else 1

# Step 2: Link kid to device
print(f"\n{YELLOW}Step 2: Link Kid to Device{RESET}")
print(f"{BLUE}Run this SQL:{RESET}\n")
print(f"""
-- Create device if it doesn't exist
INSERT INTO ai_device (id, user_id, mac_address, agent_id, creator, create_date)
SELECT UUID(), 1, '{MAC_ADDRESS}', (SELECT id FROM ai_agent LIMIT 1), 1, NOW()
WHERE NOT EXISTS (SELECT 1 FROM ai_device WHERE mac_address = '{MAC_ADDRESS}');

-- Link kid to device
UPDATE ai_device SET kid_id = {kid_id} WHERE mac_address = '{MAC_ADDRESS}';

-- Verify the link
SELECT d.mac_address, d.kid_id, k.name, k.date_of_birth, k.gender
FROM ai_device d
LEFT JOIN kid_profile k ON d.kid_id = k.id
WHERE d.mac_address = '{MAC_ADDRESS}';
""")

input(f"\n{YELLOW}Press Enter after running the SQL above...{RESET}")

# Step 3: Test the child-profile-by-mac endpoint
print(f"\n{YELLOW}Step 3: 🎯 Testing /config/child-profile-by-mac{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

try:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SECRET}"
    }

    response = requests.post(
        f"{BASE_URL}/config/child-profile-by-mac",
        headers=headers,
        json={"macAddress": MAC_ADDRESS},
        timeout=10
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 0:
            profile = data.get('data', {})
            print(f"{GREEN}✅ SUCCESS! Child Profile Retrieved:{RESET}")
            print(f"{GREEN}   👶 Name: {profile.get('name')}{RESET}")
            print(f"{GREEN}   🎂 Age: {profile.get('age')} years old{RESET}")
            print(f"{GREEN}   📚 Age Group: {profile.get('ageGroup')}{RESET}")
            print(f"{GREEN}   🚻 Gender: {profile.get('gender')}{RESET}")
            print(f"{GREEN}   ⚽ Interests: {profile.get('interests')}{RESET}")
            print(f"\n{GREEN}🎉 TEST PASSED! LiveKit can now personalize prompts!{RESET}")
        else:
            print(f"{RED}❌ API returned error code: {data.get('code')}{RESET}")
            print(f"{RED}   Message: {data.get('msg')}{RESET}")
    else:
        print(f"{RED}❌ HTTP Error {response.status_code}{RESET}")
        print(f"{YELLOW}Possible reasons:{RESET}")
        print(f"{YELLOW}  - Device not found for MAC: {MAC_ADDRESS}{RESET}")
        print(f"{YELLOW}  - Kid not assigned to device (kid_id is NULL){RESET}")
        print(f"{YELLOW}  - Manager API not running{RESET}")

except requests.exceptions.ConnectionError:
    print(f"{RED}❌ Connection Error{RESET}")
    print(f"{YELLOW}Make sure Manager API is running at: {BASE_URL}{RESET}")
except Exception as e:
    print(f"{RED}❌ Error: {e}{RESET}")
    import traceback
    traceback.print_exc()

# Step 4: Optional - Test assign-kid-by-mac API (requires user authentication)
print(f"\n{YELLOW}Step 4 (Optional): Test Assign Kid API{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")
print(f"{YELLOW}This API requires user authentication (username + password){RESET}")
print(f"{YELLOW}You can use this API to link kid to device programmatically{RESET}\n")

test_assign_api = input(f"{YELLOW}Do you want to test the assign-kid-by-mac API? (y/n): {RESET}").lower()

if test_assign_api == 'y':
    # Ask for user credentials
    print(f"\n{BLUE}Please enter your credentials:{RESET}")
    username = input(f"  Username (email): ")
    password = input(f"  Password: ")

    # Login to get token
    user_token = login_user(username, password)

    if user_token:
        try:
            print(f"\n{BLUE}Testing assign-kid-by-mac API...{RESET}")
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_token}"
            }

            response = requests.put(
                f"{BASE_URL}/device/assign-kid-by-mac",
                headers=headers,
                json={"macAddress": MAC_ADDRESS, "kidId": kid_id},
                timeout=10
            )

            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}\n")

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    print(f"{GREEN}✅ SUCCESS! Kid assigned to device via API!{RESET}")
                    print(f"{GREEN}You can now re-run Step 3 to verify the assignment{RESET}")
                else:
                    print(f"{RED}❌ API Error: {data.get('msg')}{RESET}")
            else:
                print(f"{RED}❌ HTTP Error {response.status_code}{RESET}")

        except Exception as e:
            print(f"{RED}❌ Error: {e}{RESET}")
    else:
        print(f"\n{RED}❌ Login failed, cannot test assign-kid-by-mac API{RESET}")
        print(f"{YELLOW}You can still use the SQL UPDATE method from Step 2{RESET}")

# Summary
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Test Complete!{RESET}")
print(f"{BLUE}{'='*60}{RESET}")
print(f"\n{YELLOW}Next Steps:{RESET}")
print(f"1. If test passed, the endpoint is working!")
print(f"2. LiveKit will call this endpoint with device MAC")
print(f"3. Agent prompts will be personalized for {KID_NAME}")
print(f"4. Use /device/assign-kid-by-mac API for future kid-device linking\n")
