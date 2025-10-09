#!/usr/bin/env python3
"""
Simple Kid Profile API Test Script
Uses secret token directly (no login required)
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8002/toy"
SECRET = "managerpassword"  # From application-dev.yml
MAC_ADDRESS = "68:25:dd:bb:f3:a0"
KID_NAME = "Rahul"
KID_AGE = 10
KID_GENDER = "male"
KID_DOB = (datetime.now() - timedelta(days=365*KID_AGE)).strftime("%Y-%m-%d")

print("=" * 60)
print("Kid Profile API Test - Simple Version (No Login)")
print("=" * 60)
print()

# Headers with secret token
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SECRET}"
}

# Note: For mobile API endpoints, we might need user authentication
# For now, let's test the config endpoint which uses the secret

print("Testing LiveKit Config Endpoint (uses secret token)")
print("-" * 60)

# First, let's create kid profile directly via SQL or skip to testing the config endpoint
print("\nTo test the full flow, you need to:")
print("1. Create a kid profile manually in MySQL:")
print()
print(f"INSERT INTO kid_profile (user_id, name, date_of_birth, gender, interests)")
print(f"VALUES (1, '{KID_NAME}', '{KID_DOB}', '{KID_GENDER}', '[\"games\",\"sports\",\"science\"]');")
print()
print("2. Link the kid to the device:")
print()
print(f"UPDATE ai_device SET kid_id = (SELECT id FROM kid_profile WHERE name = '{KID_NAME}' LIMIT 1)")
print(f"WHERE mac_address = '{MAC_ADDRESS}';")
print()

input("Press Enter after running the SQL commands above...")

print("\nStep: Testing child-profile-by-mac endpoint")
print("-" * 60)

try:
    response = requests.post(
        f"{BASE_URL}/config/child-profile-by-mac",
        headers=headers,
        json={"macAddress": MAC_ADDRESS}
    )

    print(f"Status Code: {response.status_code}")

    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    if response.status_code == 200 and data.get('code') == 0:
        profile = data.get('data', {})
        print()
        print("✅ SUCCESS! Child Profile Retrieved:")
        print(f"   Name: {profile.get('name')}")
        print(f"   Age: {profile.get('age')}")
        print(f"   Age Group: {profile.get('ageGroup')}")
        print(f"   Gender: {profile.get('gender')}")
        print(f"   Interests: {profile.get('interests')}")
    else:
        print()
        print("❌ Failed to get child profile")
        if response.status_code == 404:
            print("   → Device not found for MAC address")
        elif 'No child assigned' in str(data):
            print("   → No kid assigned to this device")

except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=" * 60)
print("Test Complete")
print("=" * 60)
