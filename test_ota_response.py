#!/usr/bin/env python3
"""
Test script to verify OTA response format
"""
import requests
import json

def test_ota_response():
    """Test the OTA endpoint response format"""
    
    # OTA endpoint
    ota_url = "http://172.20.10.2:8003/xiaozhi/ota"
    
    # Sample device data (similar to what ESP32 would send)
    device_data = {
        "application": {
            "version": "1.7.6"
        }
    }
    
    # Headers (device-id is required)
    headers = {
        "device-id": "78:1c:3c:4c:43:60",  # Sample MAC address
        "Content-Type": "application/json"
    }
    
    try:
        print("🔗 Testing OTA endpoint...")
        print(f"URL: {ota_url}")
        print(f"Device ID: {headers['device-id']}")
        
        # Send POST request
        response = requests.post(ota_url, json=device_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ OTA request successful!")
            
            # Parse response
            ota_response = response.json()
            print("\n📋 OTA Response:")
            print(json.dumps(ota_response, indent=2))
            
            # Check if MQTT credentials are present
            if "mqtt" in ota_response:
                mqtt_config = ota_response["mqtt"]
                print("\n🎯 MQTT Configuration Found:")
                print(f"  Endpoint: {mqtt_config.get('endpoint')}")
                print(f"  Client ID: {mqtt_config.get('client_id')}")
                print(f"  Username: {mqtt_config.get('username')}")
                print(f"  Password: {mqtt_config.get('password')[:20]}..." if mqtt_config.get('password') else "  Password: None")
                print(f"  Publish Topic: {mqtt_config.get('publish_topic')}")
                print(f"  Subscribe Topic: {mqtt_config.get('subscribe_topic')}")
                
                # Verify client_id format
                client_id = mqtt_config.get('client_id', '')
                if '@@@' in client_id:
                    parts = client_id.split('@@@')
                    if len(parts) == 3:
                        print(f"✅ Client ID format is correct: {parts[0]}@@@{parts[1]}@@@{parts[2][:8]}...")
                    else:
                        print(f"❌ Client ID format is incorrect: {client_id}")
                else:
                    print(f"❌ Client ID missing @@@ separators: {client_id}")
            else:
                print("❌ No MQTT configuration found in response")
                
        else:
            print(f"❌ OTA request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_ota_response()