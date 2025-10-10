#!/usr/bin/env python3
"""
Kid Profile API Test - API Only (No SQL)
Complete test using only REST API calls
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "http://localhost:8002/toy"
SECRET = "da11d988-f105-4e71-b095-da62ada82189"
MAC_ADDRESS = "68:25:dd:bb:f3:a0"

# Test data
KID_NAME = "Rahul"
KID_AGE = 10
KID_GENDER = "male"
# Try different date formats - backend might expect specific format
KID_DOB = (datetime.now() - timedelta(days=365*KID_AGE)).strftime("%Y-%m-%d")
KID_INTERESTS = ["games", "sports", "science"]  # Send as array, not string

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login(username, password):
    """Login and get token"""
    print(f"{BLUE}🔐 Logging in...{RESET}")
    try:
        response = requests.post(
            f"{BASE_URL}/user/login",
            json={
                'username': username,
                'password': password,
                'captcha': 'MOBILE_APP_BYPASS',
                'captchaId': str(uuid.uuid4())
            },
            timeout=10
        )
        data = response.json()
        if data.get('code') == 0:
            print(f"{GREEN}✅ Login successful{RESET}")
            return data['data']['token']
        print(f"{RED}❌ Login failed: {data.get('msg')}{RESET}")
        return None
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return None

def create_kid(token):
    """Create kid profile"""
    print(f"{BLUE}👶 Creating kid profile...{RESET}")
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        payload = {
            'name': KID_NAME,
            'dateOfBirth': KID_DOB,
            'gender': KID_GENDER,
            'interests': KID_INTERESTS
        }

        print(f"{YELLOW}   Request: POST {BASE_URL}/api/mobile/kids/create{RESET}")
        print(f"{YELLOW}   Payload: {json.dumps(payload)}{RESET}")

        response = requests.post(
            f"{BASE_URL}/api/mobile/kids/create",
            headers=headers,
            json=payload,
            timeout=10
        )

        print(f"{YELLOW}   Status: {response.status_code}{RESET}")
        print(f"{YELLOW}   Response: {response.text[:500]}{RESET}")

        data = response.json()
        if data.get('code') == 0:
            kid_id = data['data']['kid']['id']
            print(f"{GREEN}✅ Kid created (ID: {kid_id}){RESET}")
            return kid_id
        print(f"{RED}❌ Failed: {data.get('msg')}{RESET}")
        return None
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        return None

def assign_kid(token, kid_id):
    """Assign kid to device"""
    print(f"{BLUE}🔗 Assigning kid to device...{RESET}")
    try:
        response = requests.put(
            f"{BASE_URL}/device/assign-kid-by-mac",
            headers={'Authorization': f'Bearer {token}'},
            json={'macAddress': MAC_ADDRESS, 'kidId': kid_id},
            timeout=10
        )
        data = response.json()
        if data.get('code') == 0:
            print(f"{GREEN}✅ Kid assigned to device{RESET}")
            return True
        print(f"{RED}❌ Failed: {data.get('msg')}{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False

def verify_profile():
    """Verify profile can be retrieved (LiveKit endpoint)"""
    print(f"{BLUE}🎯 Verifying profile retrieval...{RESET}")
    try:
        response = requests.post(
            f"{BASE_URL}/config/child-profile-by-mac",
            headers={'Authorization': f'Bearer {SECRET}'},
            json={'macAddress': MAC_ADDRESS},
            timeout=10
        )
        data = response.json()
        if data.get('code') == 0:
            profile = data['data']
            print(f"{GREEN}✅ Profile retrieved:{RESET}")
            print(f"{GREEN}   Name: {profile['name']}, Age: {profile['age']}, Group: {profile['ageGroup']}{RESET}")
            return True
        print(f"{RED}❌ Failed: {data.get('msg')}{RESET}")
        return False
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")
        return False

# Main
print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Kid Profile API Test (API Only){RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

username = input("Username (email): ")
password = input("Password: ")
print()

token = login(username, password)
if not token:
    exit(1)

kid_id = create_kid(token)
if not kid_id:
    exit(1)

if not assign_kid(token, kid_id):
    exit(1)

if verify_profile():
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}🎉 ALL TESTS PASSED!{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")
else:
    print(f"\n{RED}{'='*60}{RESET}")
    print(f"{RED}❌ TEST FAILED{RESET}")
    print(f"{RED}{'='*60}{RESET}\n")
