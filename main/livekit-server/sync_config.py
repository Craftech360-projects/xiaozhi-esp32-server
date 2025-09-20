#!/usr/bin/env python3
"""
Configuration sync script that fetches model configuration from manager-api backend
and updates the .env file for the LiveKit agent.
"""

import os
import requests
import json
from typing import Dict, Any

# Manager API configuration
MANAGER_API_BASE_URL = 'http://localhost:8080'
DEFAULT_MODELS_ENDPOINT = '/config/livekit/default-models'

def get_default_models() -> Dict[str, str]:
    """Get default model configurations from manager-api backend"""
    config_map = {}

    try:
        print("Fetching default models from manager-api backend...")

        # Call the new backend endpoint that returns configured models
        url = f"{MANAGER_API_BASE_URL}{DEFAULT_MODELS_ENDPOINT}"

        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                models_data = data['data']

                # Extract configuration from backend response
                if 'LLM_MODEL' in models_data:
                    config_map['LLM_MODEL'] = models_data['LLM_MODEL']
                    print(f"Selected LLM: {models_data.get('llm_name', 'Unknown')} -> {models_data['LLM_MODEL']}")

                if 'STT_MODEL' in models_data:
                    config_map['STT_MODEL'] = models_data['STT_MODEL']
                    print(f"Selected STT: {models_data.get('stt_name', 'Unknown')} -> {models_data['STT_MODEL']}")

                if 'TTS_MODEL' in models_data:
                    config_map['TTS_MODEL'] = models_data['TTS_MODEL']
                    if 'TTS_PROVIDER' in models_data:
                        config_map['TTS_PROVIDER'] = models_data['TTS_PROVIDER']
                    print(f"Selected TTS: {models_data.get('tts_name', 'Unknown')} -> {models_data['TTS_MODEL']} with {config_map.get('TTS_PROVIDER', 'unknown')} provider")

                print(f"Successfully fetched models from backend: {config_map}")
            else:
                print("Invalid response format from backend API")
        else:
            print(f"HTTP {response.status_code} when fetching default models")
            if response.status_code == 404:
                print("Endpoint not found - make sure manager-api is running")
            elif response.status_code == 500:
                print("Internal server error in manager-api")

    except requests.exceptions.ConnectionError:
        print("Failed to connect to manager-api")
        print("Make sure manager-api is running on localhost:8080")
    except requests.exceptions.Timeout:
        print("Timeout connecting to manager-api")
    except Exception as e:
        print(f"Error fetching models from manager-api: {e}")

    return config_map

def update_env_file(config_updates: Dict[str, str]):
    """Update the .env file with new configuration"""
    env_file_path = '.env'

    if not os.path.exists(env_file_path):
        print(f"Warning: {env_file_path} not found")
        return

    # Read current .env file
    with open(env_file_path, 'r') as f:
        lines = f.readlines()

    # Update lines with new config
    updated_lines = []
    updated_keys = set()

    for line in lines:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            key = line.split('=')[0].strip()
            if key in config_updates:
                updated_lines.append(f"{key}={config_updates[key]}\n")
                updated_keys.add(key)
            else:
                updated_lines.append(line + '\n')
        else:
            updated_lines.append(line + '\n')

    # Add any new keys that weren't in the file
    for key, value in config_updates.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}\n")

    # Write back to .env file
    with open(env_file_path, 'w') as f:
        f.writelines(updated_lines)

    print(f"Updated .env file with {len(config_updates)} configuration changes")

    # Show what was updated
    for key, value in config_updates.items():
        print(f"  {key}={value}")

def main():
    """Main function to sync configuration"""
    print("Syncing configuration from manager-api backend to LiveKit agent...")

    # Get model configurations from backend
    model_configs = get_default_models()

    if model_configs:
        print(f"Found configurations: {model_configs}")

        # Update .env file
        update_env_file(model_configs)

        print("Configuration sync completed!")
        print("Please restart the LiveKit agent to apply changes:")
        print("   python main.py dev")
    else:
        print("No configuration found or error connecting to backend")

if __name__ == "__main__":
    main()