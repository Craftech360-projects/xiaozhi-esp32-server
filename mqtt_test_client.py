#!/usr/bin/env python3
"""
Simple MQTT test client to verify EMQX integration
"""
import json
import time
import uuid
import base64
import hashlib
import hmac
import requests

try:
    import paho.mqtt.client as mqtt_client
    from paho.mqtt.enums import CallbackAPIVersion
except ImportError:
    print("Installing paho-mqtt...")
    import subprocess
    subprocess.check_call(["pip", "install", "--break-system-packages", "paho-mqtt"])
    import paho.mqtt.client as mqtt_client
    from paho.mqtt.enums import CallbackAPIVersion

# Configuration
SERVER_IP = "64.227.170.31"
OTA_PORT = 8002
MQTT_BROKER_HOST = "64.227.170.31"
MQTT_BROKER_PORT = 1884

def generate_mqtt_credentials(device_mac: str) -> dict:
    """Generate MQTT credentials matching the ESP32 server logic."""
    # Create client ID
    client_id = f"GID_test@@@{device_mac}@@@{uuid.uuid4()}"
    
    # Create username (base64 encoded JSON)
    username_data = {"ip": "192.168.1.10"}
    username = base64.b64encode(json.dumps(username_data).encode()).decode()
    
    # Create password (HMAC-SHA256)
    secret_key = "test-signature-key-12345"
    content = f"{client_id}|{username}"
    password = base64.b64encode(hmac.new(secret_key.encode(), content.encode(), hashlib.sha256).digest()).decode()
    
    return {
        "client_id": client_id,
        "username": username,
        "password": password
    }

def get_mqtt_credentials_from_api(device_mac: str) -> dict:
    """Get MQTT credentials from manager API."""
    try:
        headers = {"device-id": device_mac}
        data = {
            "application": {"version": "1.7.6", "name": "DOIT AI Kit v1.7.6"},
            "board": {"type": "doit-ai-01-kit"},
            "client_id": str(uuid.uuid4())
        }
        
        print(f"🔄 Requesting MQTT credentials from manager API...")
        response = requests.post(f"http://{SERVER_IP}:{OTA_PORT}/toy/ota/", 
                               headers=headers, json=data, timeout=10)
        response.raise_for_status()
        
        ota_config = response.json()
        print(f"✅ OTA Response: {json.dumps(ota_config, indent=2)}")
        
        mqtt_info = ota_config.get("mqtt", {})
        if mqtt_info:
            return {
                "client_id": mqtt_info.get("client_id"),
                "username": mqtt_info.get("username"), 
                "password": mqtt_info.get("password")
            }
        else:
            print("⚠️ No MQTT info in API response, generating locally")
            return generate_mqtt_credentials(device_mac)
            
    except Exception as e:
        print(f"❌ Failed to get credentials from API: {e}")
        print("🔄 Falling back to local generation")
        return generate_mqtt_credentials(device_mac)

def test_mqtt_connection():
    """Test MQTT connection to EMQX broker."""
    device_mac = "00:16:3e:ac:b5:38"
    
    # Get MQTT credentials
    mqtt_creds = get_mqtt_credentials_from_api(device_mac)
    
    print(f"\n🔐 MQTT Credentials:")
    print(f"   Client ID: {mqtt_creds['client_id']}")
    print(f"   Username: {mqtt_creds['username']}")
    print(f"   Password: {mqtt_creds['password'][:20]}...")
    
    connected = False
    
    def on_connect(client, userdata, flags, rc, properties=None):
        nonlocal connected
        if rc == 0:
            print(f"✅ MQTT Connected successfully!")
            connected = True
            # Subscribe to a test topic
            topic = f"devices/p2p/{device_mac}"
            client.subscribe(topic)
            print(f"📡 Subscribed to topic: {topic}")
            
            # Publish a test message
            test_msg = {"type": "test", "timestamp": time.time(), "message": "Hello from test client"}
            client.publish("device-server", json.dumps(test_msg))
            print(f"📤 Published test message to device-server")
            
        else:
            print(f"❌ MQTT Connection failed with code {rc}")
            
    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"📨 Received message on {msg.topic}: {json.dumps(payload, indent=2)}")
        except:
            print(f"📨 Received message on {msg.topic}: {msg.payload}")
    
    # Create MQTT client
    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=mqtt_creds["client_id"]
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqtt_creds["username"], mqtt_creds["password"])
    
    print(f"\n🔄 Connecting to EMQX broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start()
        
        # Wait for connection and test messages
        for i in range(30):
            if connected:
                break
            time.sleep(1)
            print(f"⏳ Waiting for connection... {i+1}/30")
        
        if connected:
            print("✅ MQTT connection test successful!")
            print("🔄 Keeping connection open for 10 seconds to test messaging...")
            time.sleep(10)
        else:
            print("❌ MQTT connection test failed!")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Disconnected from MQTT broker")

if __name__ == "__main__":
    print("🧪 EMQX MQTT Integration Test")
    print("=" * 50)
    test_mqtt_connection()