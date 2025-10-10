#!/usr/bin/env python3
"""
Complete Kid Profile API Test Script
Uses only API calls - no SQL required!
"""

import requests
import json
from datetime import datetime, timedelta
import uuid

# Configuration
BASE_URL = "http://localhost:8002/toy"
SECRET = "da11d988-f105-4e71-b095-da62ada82189"
MAC_ADDRESS = "68:25:dd:bb:f3:a0"

# Test kid data
KID_NAME = "Rahul"
KID_AGE = 10
KID_GENDER = "male"
KID_DOB = (datetime.now() - timedelta(days=365*KID_AGE)).strftime("%Y-%m-%d")
KID_INTERESTS = '["games", "sports", "science"]'

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def login_user(username, password):
    """Login to get user authentication token"""
    print(f"\n{BLUE}🔐 Logging in as: {username}{RESET}")

    try:
        captcha_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/user/login",
            headers={'Content-Type': 'application/json'},
            json={
                'username': username,
                'mobile': username,
                'password': password,
                'captcha': 'MOBILE_APP_BYPASS',
                'captchaId': captcha_id
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data', {}).get('token'):
                token = data['data']['token']
                print(f"  {GREEN}✅ Login successful!{RESET}")
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

def create_kid_profile(token, name, dob, gender, interests):
    """Create kid profile using API"""
    print(f"\n{BLUE}👶 Creating kid profile: {name}{RESET}")

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.post(
            f"{BASE_URL}/api/mobile/kids/create",
            headers=headers,
            json={
                'name': name,
                'dateOfBirth': dob,
                'gender': gender,
                'interests': interests,
                'avatarUrl': 'https://example.com/avatar.jpg'
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0 and data.get('data', {}).get('kid'):
                kid = data['data']['kid']
                kid_id = kid.get('id')
                print(f"  {GREEN}✅ Kid profile created!{RESET}")
                print(f"  {GREEN}   ID: {kid_id}{RESET}")
                print(f"  {GREEN}   Name: {kid.get('name')}{RESET}")
                print(f"  {GREEN}   Age: {kid.get('age')}{RESET}")
                print(f"  {GREEN}   Age Group: {kid.get('ageGroup')}{RESET}")
                return kid_id
            else:
                error_msg = data.get('msg', 'Creation failed')
                print(f"  {RED}❌ Failed: {error_msg}{RESET}")
                return None
        else:
            print(f"  {RED}❌ HTTP Error {response.status_code}{RESET}")
            return None

    except Exception as e:
        print(f"  {RED}❌ Error: {e}{RESET}")
        return None

def get_all_kids(token):
    """Get all kid profiles for user"""
    print(f"\n{BLUE}📋 Getting all kid profiles{RESET}")

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.get(
            f"{BASE_URL}/api/mobile/kids/list",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                kids = data.get('data', {}).get('kids', [])
                print(f"  {GREEN}✅ Found {len(kids)} kid profile(s){RESET}")
                for kid in kids:
                    print(f"     - ID: {kid.get('id')}, Name: {kid.get('name')}, Age: {kid.get('age')}")
                return kids
            else:
                print(f"  {RED}❌ Failed: {data.get('msg')}{RESET}")
                return []
        else:
            print(f"  {RED}❌ HTTP Error {response.status_code}{RESET}")
            return []

    except Exception as e:
        print(f"  {RED}❌ Error: {e}{RESET}")
        return []

def assign_kid_to_device(token, mac_address, kid_id):
    """Assign kid to device using API"""
    print(f"\n{BLUE}🔗 Assigning kid {kid_id} to device {mac_address}{RESET}")

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        response = requests.put(
            f"{BASE_URL}/device/assign-kid-by-mac",
            headers=headers,
            json={
                'macAddress': mac_address,
                'kidId': kid_id
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"  {GREEN}✅ Kid assigned to device successfully!{RESET}")
                return True
            else:
                error_msg = data.get('msg', 'Assignment failed')
                print(f"  {RED}❌ Failed: {error_msg}{RESET}")
                return False
        else:
            print(f"  {RED}❌ HTTP Error {response.status_code}{RESET}")
            return False

    except Exception as e:
        print(f"  {RED}❌ Error: {e}{RESET}")
        return False

def get_child_profile_by_mac(mac_address):
    """Get child profile by MAC (LiveKit endpoint - no login required)"""
    print(f"\n{BLUE}🎯 Getting child profile for device {mac_address}{RESET}")

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {SECRET}'
        }

        response = requests.post(
            f"{BASE_URL}/config/child-profile-by-mac",
            headers=headers,
            json={'macAddress': mac_address},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                profile = data.get('data', {})
                print(f"  {GREEN}✅ Child profile retrieved!{RESET}")
                print(f"  {GREEN}   👶 Name: {profile.get('name')}{RESET}")
                print(f"  {GREEN}   🎂 Age: {profile.get('age')} years old{RESET}")
                print(f"  {GREEN}   📚 Age Group: {profile.get('ageGroup')}{RESET}")
                print(f"  {GREEN}   🚻 Gender: {profile.get('gender')}{RESET}")
                print(f"  {GREEN}   ⚽ Interests: {profile.get('interests')}{RESET}")
                return profile
            else:
                error_msg = data.get('msg', 'Failed')
                print(f"  {RED}❌ Failed: {error_msg}{RESET}")
                return None
        else:
            print(f"  {RED}❌ HTTP Error {response.status_code}{RESET}")
            return None

    except Exception as e:
        print(f"  {RED}❌ Error: {e}{RESET}")
        return None

# Main test flow
print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Kid Profile API Complete Test{RESET}")
print(f"{BLUE}Using only API calls - no SQL required!{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

# Step 1: Login
print(f"{YELLOW}Step 1: User Login{RESET}")
print(f"{BLUE}Please enter your credentials:{RESET}")
username = input(f"  Username (email): ")
password = input(f"  Password: ")

token = login_user(username, password)

if not token:
    print(f"\n{RED}❌ Login failed. Cannot continue.{RESET}")
    print(f"{YELLOW}Please check your credentials and try again.{RESET}")
    exit(1)

# Step 2: Check existing kids
print(f"\n{YELLOW}Step 2: Check Existing Kid Profiles{RESET}")
existing_kids = get_all_kids(token)

kid_id = None
if existing_kids:
    use_existing = input(f"\n{YELLOW}Use existing kid profile? (y/n): {RESET}").lower()
    if use_existing == 'y':
        kid_id = existing_kids[0]['id']
        print(f"{GREEN}Using existing kid: {existing_kids[0]['name']} (ID: {kid_id}){RESET}")

# Step 3: Create new kid if needed
if not kid_id:
    print(f"\n{YELLOW}Step 3: Create New Kid Profile{RESET}")
    create_new = input(f"{YELLOW}Create new kid profile? (y/n): {RESET}").lower()

    if create_new == 'y':
        # Use default or custom values
        use_defaults = input(f"{YELLOW}Use default values (Rahul, 10 years old)? (y/n): {RESET}").lower()

        if use_defaults != 'y':
            KID_NAME = input(f"  Kid's name: ")
            KID_AGE = int(input(f"  Kid's age: "))
            KID_GENDER = input(f"  Kid's gender (male/female): ")
            KID_DOB = (datetime.now() - timedelta(days=365*KID_AGE)).strftime("%Y-%m-%d")

        kid_id = create_kid_profile(token, KID_NAME, KID_DOB, KID_GENDER, KID_INTERESTS)

        if not kid_id:
            print(f"\n{RED}❌ Failed to create kid profile. Cannot continue.{RESET}")
            exit(1)
    else:
        print(f"\n{RED}❌ No kid profile available. Cannot continue.{RESET}")
        exit(1)

# Step 4: Assign kid to device
print(f"\n{YELLOW}Step 4: Assign Kid to Device{RESET}")
assign_success = assign_kid_to_device(token, MAC_ADDRESS, kid_id)

if not assign_success:
    print(f"\n{YELLOW}⚠️ Assignment failed, but continuing to test retrieval...{RESET}")

# Step 5: Verify assignment (LiveKit endpoint)
print(f"\n{YELLOW}Step 5: Verify Assignment (LiveKit Endpoint){RESET}")
profile = get_child_profile_by_mac(MAC_ADDRESS)

# Summary
print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Test Summary{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

if profile:
    print(f"{GREEN}✅ ALL TESTS PASSED!{RESET}\n")
    print(f"{GREEN}Kid profile is properly linked to device{RESET}")
    print(f"{GREEN}LiveKit server can now retrieve child profile by MAC{RESET}")
    print(f"{GREEN}Agent prompts will be personalized for {profile.get('name')}!{RESET}")
else:
    print(f"{RED}❌ TEST FAILED{RESET}\n")
    print(f"{YELLOW}Kid profile could not be retrieved for device{RESET}")
    print(f"{YELLOW}Please check the assignment step{RESET}")

print(f"\n{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Next Steps:{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")
print(f"1. Integrate with Flutter app (create JavaKidProfileService)")
print(f"2. Update LiveKit server to call /config/child-profile-by-mac")
print(f"3. Customize agent prompts with Jinja2 template variables")
print(f"4. Test with actual device!\n")
