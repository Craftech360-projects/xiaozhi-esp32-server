#!/usr/bin/env python3
"""
Test Complete Prompt Rendering Flow
Shows:
1. Raw prompt fetched from Manager API (with {{ }} templates)
2. Child profile data fetched from Manager API
3. Final rendered prompt (with actual values replacing {{ }})
"""

import requests
import json
from jinja2 import Template

# Configuration
MANAGER_API_URL = "http://localhost:8002/toy"
MANAGER_API_SECRET = "da11d988-f105-4e71-b095-da62ada82189"
DEVICE_MAC = "68:25:dd:bb:f3:a0"  # Device with Rahul assigned

def fetch_agent_prompt():
    """Fetch raw agent prompt from Manager API"""
    print("\n" + "=" * 80)
    print("STEP 1: FETCHING RAW PROMPT FROM MANAGER API")
    print("=" * 80)

    url = f"{MANAGER_API_URL}/config/agent-prompt"
    headers = {
        "Authorization": f"Bearer {MANAGER_API_SECRET}",
        "Content-Type": "application/json"
    }
    payload = {"macAddress": DEVICE_MAC}

    print(f"\n📡 GET {url}")
    print(f"   MAC: {DEVICE_MAC}")

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if data.get('code') == 0:
        prompt = data.get('data')
        print(f"\n✅ Success!")
        print(f"   Length: {len(prompt)} characters")
        print(f"   Contains templates: {'Yes' if '{{' in prompt else 'No'}")

        print(f"\n📄 RAW PROMPT (with Jinja2 templates):")
        print("=" * 80)
        print(prompt)
        print("=" * 80)

        return prompt
    else:
        print(f"\n❌ Error: {data.get('msg')}")
        return None

def fetch_child_profile():
    """Fetch child profile data from Manager API"""
    print("\n" + "=" * 80)
    print("STEP 2: FETCHING CHILD PROFILE DATA FROM MANAGER API")
    print("=" * 80)

    url = f"{MANAGER_API_URL}/config/child-profile-by-mac"
    headers = {
        "Authorization": f"Bearer {MANAGER_API_SECRET}",
        "Content-Type": "application/json"
    }
    payload = {"macAddress": DEVICE_MAC}

    print(f"\n📡 GET {url}")
    print(f"   MAC: {DEVICE_MAC}")

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if data.get('code') == 0:
        child_profile = data.get('data')
        print(f"\n✅ Success!")
        print(f"\n👶 Child Profile Data:")
        print(f"   Name: {child_profile.get('name')}")
        print(f"   Age: {child_profile.get('age')}")
        print(f"   Age Group: {child_profile.get('ageGroup')}")
        print(f"   Gender: {child_profile.get('gender')}")
        print(f"   Interests: {child_profile.get('interests')}")

        return child_profile
    else:
        print(f"\n❌ Error: {data.get('msg')}")
        return None

def render_prompt(raw_prompt, child_profile):
    """Render the prompt with actual values (simulating what LiveKit does)"""
    print("\n" + "=" * 80)
    print("STEP 3: RENDERING PROMPT WITH ACTUAL VALUES (LiveKit Process)")
    print("=" * 80)

    # Prepare template variables (same as main.py lines 257-264)
    EMOJI_List = ["😶", "🙂", "😆", "😂", "😔", "😠", "😭", "😍", "😳",
                  "😲", "😱", "🤔", "😉", "😎", "😌", "🤤", "😘", "😏", "😴", "😜", "🙄"]

    template_vars = {
        'emojiList': EMOJI_List,
        'child_name': child_profile.get('name', 'friend') if child_profile else 'friend',
        'child_age': child_profile.get('age', '') if child_profile else '',
        'age_group': child_profile.get('ageGroup', '') if child_profile else '',
        'child_gender': child_profile.get('gender', '') if child_profile else '',
        'child_interests': child_profile.get('interests', '') if child_profile else ''
    }

    print(f"\n🎨 Template Variables:")
    print(f"   child_name: '{template_vars['child_name']}'")
    print(f"   child_age: '{template_vars['child_age']}'")
    print(f"   age_group: '{template_vars['age_group']}'")
    print(f"   child_gender: '{template_vars['child_gender']}'")
    print(f"   child_interests: '{template_vars['child_interests']}'")

    # Render with Jinja2 (same as main.py lines 267-269)
    if any(placeholder in raw_prompt for placeholder in ['{{', '{%']):
        template = Template(raw_prompt)
        rendered_prompt = template.render(**template_vars)

        print(f"\n✅ Template rendered successfully!")
        print(f"   Replaced {{ child_name }} with: {template_vars['child_name']}")
        print(f"   Replaced {{ child_age }} with: {template_vars['child_age']}")

        print(f"\n📄 FINAL RENDERED PROMPT (what agent actually sees):")
        print("=" * 80)
        print(rendered_prompt)
        print("=" * 80)

        return rendered_prompt
    else:
        print(f"\n⚠️  No templates found, using prompt as-is")
        return raw_prompt

def save_comparison(raw_prompt, child_profile, rendered_prompt):
    """Save comparison to file"""
    output_file = "prompt_rendering_comparison.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("PROMPT RENDERING COMPARISON\n")
        f.write("=" * 80 + "\n\n")

        f.write("1. RAW PROMPT FROM MANAGER API (with templates)\n")
        f.write("=" * 80 + "\n")
        f.write(raw_prompt)
        f.write("\n\n")

        f.write("2. CHILD PROFILE DATA\n")
        f.write("=" * 80 + "\n")
        f.write(json.dumps(child_profile, indent=2))
        f.write("\n\n")

        f.write("3. FINAL RENDERED PROMPT (what agent sees)\n")
        f.write("=" * 80 + "\n")
        f.write(rendered_prompt)
        f.write("\n\n")

    print(f"\n💾 Comparison saved to: {output_file}")

def main():
    print("\n" + "=" * 80)
    print("COMPLETE PROMPT RENDERING TEST")
    print("Simulating LiveKit's prompt processing pipeline")
    print("=" * 80)

    # Step 1: Fetch raw prompt with templates
    raw_prompt = fetch_agent_prompt()
    if not raw_prompt:
        print("\n❌ Failed to fetch prompt")
        return

    # Step 2: Fetch child profile data
    child_profile = fetch_child_profile()
    if not child_profile:
        print("\n⚠️  No child profile found, using defaults")
        child_profile = None

    # Step 3: Render prompt with actual values
    rendered_prompt = render_prompt(raw_prompt, child_profile)

    # Step 4: Save comparison
    save_comparison(raw_prompt, child_profile or {}, rendered_prompt)

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print("\n✅ Process Complete!")
    print("\nWhat happens in LiveKit:")
    print("1. Fetches raw prompt from Manager API (contains {{ }} templates)")
    print("2. Fetches child profile data by MAC address")
    print("3. Renders template, replacing {{ }} with actual values")
    print("4. Agent receives final prompt with personalized content")
    print("\nFiles created:")
    print("- prompt_rendering_comparison.txt (side-by-side comparison)")
    print("=" * 80)

if __name__ == "__main__":
    main()
