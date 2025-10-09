#!/usr/bin/env python3
"""
Test Agent Prompt Fetching with Child Profile Integration
Shows exactly what prompt is fetched and from where (Manager API vs config.yaml)
"""

import requests
import json
import os
from pathlib import Path

# Configuration
MANAGER_API_URL = "http://localhost:8002/toy"
MANAGER_API_SECRET = "da11d988-f105-4e71-b095-da62ada82189"  # Server secret
DEVICE_MAC = "68:25:dd:bb:f3:a0"  # Device with Rahul assigned

def check_config_yaml_source():
    """Check what's in config.yaml for comparison"""
    config_path = Path("main/livekit-server/config.yaml")

    print("\n" + "=" * 60)
    print("📄 CHECKING CONFIG.YAML FILE")
    print("=" * 60)

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if API fetching is enabled
        if "read_config_from_api: true" in content:
            print("✅ read_config_from_api: true")
            print("   → Prompt will be fetched from Manager API")
        else:
            print("⚠️  read_config_from_api: false")
            print("   → Prompt will be read from config.yaml")

        # Check if config.yaml has child profile template
        if "{% if child_name %}" in content:
            print("✅ config.yaml contains child profile Jinja2 template")
        else:
            print("❌ config.yaml does NOT contain child profile template")

        # Find default_prompt section
        if "default_prompt:" in content:
            start_idx = content.find("default_prompt:")
            end_idx = content.find("\nend_prompt:", start_idx)
            if end_idx == -1:
                end_idx = content.find("\n\napi_keys:", start_idx)

            default_prompt = content[start_idx:end_idx]
            print(f"\n📋 default_prompt preview (first 500 chars):")
            print("-" * 60)
            print(default_prompt[:500])
            print("-" * 60)
    else:
        print("❌ config.yaml not found at:", config_path.absolute())

def test_prompt_fetch():
    """Test fetching agent prompt with child profile"""

    print("\n" + "=" * 60)
    print("📡 FETCHING PROMPT FROM MANAGER API")
    print("=" * 60)

    url = f"{MANAGER_API_URL}/config/agent-prompt"
    headers = {
        "Authorization": f"Bearer {MANAGER_API_SECRET}",
        "Content-Type": "application/json"
    }
    payload = {"macAddress": DEVICE_MAC}

    print(f"\n📡 Request Details:")
    print(f"   URL: {url}")
    print(f"   Device MAC: {DEVICE_MAC}")
    print(f"   Authorization: Bearer {MANAGER_API_SECRET[:20]}...")

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        data = response.json()

        if data.get('code') == 0:
            prompt = data.get('data')

            print(f"\n✅ Prompt fetched successfully from Manager API!")
            print(f"   Source: Manager API (agent.system_prompt from database)")
            print(f"   Length: {len(prompt)} characters")
            print(f"   Lines: {len(prompt.splitlines())}")

            # Check if child profile section is included
            if "{% if child_name %}" in prompt:
                print(f"\n✅ Child profile template variables found in prompt!")
                print(f"\n📝 Checking for template variables:")

                variables = [
                    "{{ child_name }}",
                    "{{ child_age }}",
                    "{{ age_group }}",
                    "{{ child_gender }}",
                    "{{ child_interests }}"
                ]

                for var in variables:
                    if var in prompt:
                        print(f"   ✅ Found: {var}")
                    else:
                        print(f"   ❌ Missing: {var}")

                # Display excerpt around child profile section
                start_idx = prompt.find("{% if child_name %}")
                if start_idx != -1:
                    end_idx = prompt.find("{% endif %}", start_idx)
                    if end_idx != -1:
                        excerpt = prompt[start_idx:end_idx + 11]
                        print(f"\n📋 Child Profile Section:")
                        print("-" * 60)
                        print(excerpt)
                        print("-" * 60)
            else:
                print(f"\n❌ Child profile template NOT found in prompt!")
                print(f"   Possible reasons:")
                print(f"   1. Device {DEVICE_MAC} has no child assigned")
                print(f"   2. Backend code not yet applied/restarted")
                print(f"   3. Database agent prompt doesn't have child profile injection")

            # Display full prompt structure
            print(f"\n📄 FULL PROMPT FROM MANAGER API:")
            print("=" * 60)
            print(prompt)
            print("=" * 60)

            # Save to file for inspection
            output_file = "fetched_prompt_output.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("PROMPT FETCHED FROM MANAGER API\n")
                f.write("=" * 60 + "\n")
                f.write(f"Device MAC: {DEVICE_MAC}\n")
                f.write(f"API Response Code: {data.get('code')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(prompt)
            print(f"\n💾 Full prompt saved to: {output_file}")

            return True

        else:
            print(f"\n❌ API returned error: {data.get('msg')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")
        return False

if __name__ == "__main__":
    # First check config.yaml
    check_config_yaml_source()

    # Then fetch from Manager API
    success = test_prompt_fetch()

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("\nLiveKit Server Prompt Source Priority:")
    print("1. ✅ read_config_from_api: true → Fetch from Manager API")
    print("2. ❌ read_config_from_api: false → Use config.yaml")
    print("\nCurrent Configuration:")
    print("   → Should be using Manager API (check output above)")

    if success:
        print("\n✅ Test completed successfully!")
        print("\nNext Steps:")
        print("1. Check fetched_prompt_output.txt to see full prompt")
        print("2. Verify child profile Jinja2 templates are present")
        print("3. Test with LiveKit server to see rendered prompt")
    else:
        print("\n❌ Test failed!")
        print("\nTroubleshooting:")
        print("1. Check if Manager API is running on http://localhost:8002")
        print("2. Verify device MAC exists in database")
        print("3. Ensure child profile is assigned to device")
    print("=" * 60)
