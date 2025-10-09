#!/usr/bin/env python3
"""
Quick script to verify kid-device linking in database
"""

import requests

# Configuration
BASE_URL = "http://localhost:8002/toy"
SECRET = "da11d988-f105-4e71-b095-da62ada82189"
MAC_ADDRESS = "68:25:dd:bb:f3:a0"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'

print(f"{BLUE}{'='*60}{RESET}")
print(f"{BLUE}Verifying Kid-Device Link{RESET}")
print(f"{BLUE}{'='*60}{RESET}\n")

print(f"{YELLOW}Testing /config/child-profile-by-mac endpoint{RESET}")
print(f"MAC Address: {MAC_ADDRESS}\n")

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
    data = response.json()
    print(f"Response: {data}\n")

    if response.status_code == 200 and data.get('code') == 0:
        profile = data.get('data', {})
        print(f"{GREEN}✅ SUCCESS! Kid profile found:{RESET}")
        print(f"{GREEN}   👶 Name: {profile.get('name')}{RESET}")
        print(f"{GREEN}   🎂 Age: {profile.get('age')} years old{RESET}")
        print(f"{GREEN}   📚 Age Group: {profile.get('ageGroup')}{RESET}")
        print(f"{GREEN}   🚻 Gender: {profile.get('gender')}{RESET}")
        print(f"{GREEN}   ⚽ Interests: {profile.get('interests')}{RESET}")
    elif data.get('msg') == 'No child assigned to this device':
        print(f"{RED}❌ No child assigned to this device{RESET}\n")
        print(f"{YELLOW}Possible causes:{RESET}")
        print(f"  1. Device exists but kid_id is NULL")
        print(f"  2. You haven't run the SQL UPDATE yet\n")
        print(f"{YELLOW}Solution - Run this SQL:{RESET}\n")
        print(f"-- First, check what kid profiles exist:")
        print(f"SELECT id, name, user_id FROM kid_profile;\n")
        print(f"-- Then, check the device:")
        print(f"SELECT id, mac_address, kid_id, user_id FROM ai_device WHERE mac_address = '{MAC_ADDRESS}';\n")
        print(f"-- Finally, link kid to device (replace 1 with actual kid_id):")
        print(f"UPDATE ai_device SET kid_id = 1 WHERE mac_address = '{MAC_ADDRESS}';\n")
    elif data.get('msg') == f'Device not found for MAC: {MAC_ADDRESS}':
        print(f"{RED}❌ Device not found in database{RESET}\n")
        print(f"{YELLOW}Solution - Run this SQL to create device:{RESET}\n")
        print(f"INSERT INTO ai_device (id, user_id, mac_address, agent_id, creator, create_date)")
        print(f"SELECT UUID(), 1, '{MAC_ADDRESS}', (SELECT id FROM ai_agent LIMIT 1), 1, NOW()")
        print(f"WHERE NOT EXISTS (SELECT 1 FROM ai_device WHERE mac_address = '{MAC_ADDRESS}');\n")
    else:
        print(f"{RED}❌ Error: {data.get('msg')}{RESET}")

except requests.exceptions.ConnectionError:
    print(f"{RED}❌ Connection Error{RESET}")
    print(f"{YELLOW}Make sure Manager API is running at: {BASE_URL}{RESET}")
except Exception as e:
    print(f"{RED}❌ Error: {e}{RESET}")

print(f"\n{BLUE}{'='*60}{RESET}")
