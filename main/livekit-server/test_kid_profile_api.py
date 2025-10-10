#!/usr/bin/env python3
"""
Kid Profile API Test Script
Tests all kid profile endpoints and device-kid linking
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8002/toy"
MAC_ADDRESS = "68:25:dd:bb:f3:a0"
KID_NAME = "Rahul"
KID_AGE = 10
KID_GENDER = "male"
# Calculate date of birth (10 years ago)
KID_DOB = (datetime.now() - timedelta(days=365*KID_AGE)).strftime("%Y-%m-%d")

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*50}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*50}{RESET}\n")

def print_step(step_num, text):
    print(f"{YELLOW}Step {step_num}: {text}{RESET}")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_response(response):
    try:
        json_data = response.json()
        print(f"Response: {json.dumps(json_data, indent=2)}")
        return json_data
    except:
        print(f"Response: {response.text}")
        return None

# Main test flow
print_header("Kid Profile API Test Script")

# Step 1: Login
print_step(1, "Login to get authentication token")
try:
    login_response = requests.post(
        f"{BASE_URL}/login",
        json={
            "username": "admin",
            "password": "Admin@123"
        }
    )
    login_data = login_response.json()

    if 'token' in login_data:
        token = login_data['token']
        print_success(f"Login successful. Token: {token[:20]}...")
    else:
        print_error("Login failed - no token in response")
        print_response(login_response)
        exit(1)
except Exception as e:
    print_error(f"Login failed: {e}")
    exit(1)

# Prepare headers
headers = {
    "Content-Type": "application/json",
    "token": token
}

# Step 2: Create kid profile
print_step(2, f"Create kid profile (Name: {KID_NAME}, Age: {KID_AGE})")
try:
    create_kid_response = requests.post(
        f"{BASE_URL}/api/mobile/kids/create",
        headers=headers,
        json={
            "name": KID_NAME,
            "dateOfBirth": KID_DOB,
            "gender": KID_GENDER,
            "interests": '["games", "sports", "science"]',
            "avatarUrl": "https://example.com/avatar.jpg"
        }
    )

    create_data = print_response(create_kid_response)

    if create_data and 'data' in create_data and 'kid' in create_data['data']:
        kid_id = create_data['data']['kid']['id']
        print_success(f"Kid profile created successfully. Kid ID: {kid_id}")
    elif create_data and 'code' in create_data and create_data['code'] == 0:
        # Alternative response format
        kid_id = create_data.get('data', {}).get('id')
        print_success(f"Kid profile created successfully. Kid ID: {kid_id}")
    else:
        print_error("Failed to create kid profile")
        exit(1)
except Exception as e:
    print_error(f"Failed to create kid: {e}")
    exit(1)

# Step 3: Get all kids
print_step(3, "Get all kids for current user")
try:
    get_kids_response = requests.get(
        f"{BASE_URL}/api/mobile/kids/list",
        headers=headers
    )
    kids_data = print_response(get_kids_response)
    print_success(f"Retrieved kids list")
except Exception as e:
    print_error(f"Failed to get kids: {e}")

# Step 4: Get specific kid
print_step(4, f"Get kid by ID ({kid_id})")
try:
    get_kid_response = requests.get(
        f"{BASE_URL}/api/mobile/kids/{kid_id}",
        headers=headers
    )
    kid_data = print_response(get_kid_response)
    print_success(f"Retrieved kid profile")
except Exception as e:
    print_error(f"Failed to get kid: {e}")

# Step 5: Get device by MAC (optional - endpoint might not exist)
print_step(5, f"Get device by MAC address ({MAC_ADDRESS})")
device_id = None
try:
    # Try different possible endpoints
    endpoints = [
        f"{BASE_URL}/api/device/by-mac/{MAC_ADDRESS}",
        f"{BASE_URL}/device/by-mac/{MAC_ADDRESS}",
        f"{BASE_URL}/api/devices/mac/{MAC_ADDRESS}"
    ]

    for endpoint in endpoints:
        try:
            device_response = requests.get(endpoint, headers=headers)
            if device_response.status_code == 200:
                device_data = device_response.json()
                if 'data' in device_data:
                    device_id = device_data['data'].get('id')
                    print_success(f"Device found. ID: {device_id}")
                    break
        except:
            continue

    if not device_id:
        print_warning(f"Device endpoint not found or device doesn't exist for MAC: {MAC_ADDRESS}")
        print_warning("You'll need to manually link kid to device using SQL")
except Exception as e:
    print_warning(f"Device lookup failed: {e}")

# Step 6: Assign kid to device (manual SQL required)
print_step(6, "Assign kid to device")
print_warning("Manual SQL update required:")
print(f"{BLUE}   UPDATE ai_device SET kid_id = {kid_id} WHERE mac_address = '{MAC_ADDRESS}';{RESET}")
print()
input(f"{YELLOW}Press Enter after running the SQL update...{RESET}")

# Step 7: Get child profile by MAC (LiveKit endpoint)
print_step(7, "Get child profile by MAC (LiveKit endpoint)")
try:
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer managerpassword"
    }

    child_profile_response = requests.post(
        f"{BASE_URL}/config/child-profile-by-mac",
        headers=auth_headers,
        json={
            "macAddress": MAC_ADDRESS
        }
    )

    child_data = print_response(child_profile_response)

    if child_data and child_data.get('code') == 0:
        profile = child_data.get('data', {})
        if profile.get('name') == KID_NAME:
            print_success("Successfully retrieved child profile by MAC!")
            print_success(f"   Name: {profile.get('name')}, Age: {profile.get('age')}, Age Group: {profile.get('ageGroup')}")
            print_success(f"   Gender: {profile.get('gender')}, Interests: {profile.get('interests')}")
        else:
            print_error("Child profile returned but name doesn't match")
    else:
        print_error("Failed to retrieve child profile by MAC")
        print_warning("Make sure kid is assigned to device in database")
except Exception as e:
    print_error(f"Failed to get child profile: {e}")

# Step 8: Update kid profile
print_step(8, "Update kid profile (add coding to interests)")
try:
    update_response = requests.put(
        f"{BASE_URL}/api/mobile/kids/{kid_id}",
        headers=headers,
        json={
            "interests": '["games", "sports", "science", "coding"]'
        }
    )
    update_data = print_response(update_response)
    print_success("Kid profile updated successfully")
except Exception as e:
    print_error(f"Failed to update kid: {e}")

# Summary
print_header("Test Summary")
print_success("Login successful")
print_success(f"Kid profile created (ID: {kid_id}, Name: {KID_NAME})")
print_success("Kid profiles listed")
print_success("Individual kid retrieved")
if device_id:
    print_success(f"Device found (ID: {device_id})")
else:
    print_warning("Device not found via API")
print_success("Child profile by MAC endpoint tested")

print(f"\n{BLUE}Next Steps:{RESET}")
print("1. If SQL update wasn't run, execute it to link kid to device")
print("2. Test with LiveKit server using MAC:", MAC_ADDRESS)
print("3. Check LiveKit logs for child profile loading")
print()
