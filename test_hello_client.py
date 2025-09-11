#!/usr/bin/env python3
"""
Test client to send hello message to EMQX and test the rule engine integration
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
        print(f"✅ OTA Response received")
        
        mqtt_info = ota_config.get("mqtt", {})
        if mqtt_info:
            return {
                "client_id": mqtt_info.get("client_id"),
                "username": mqtt_info.get("username"), 
                "password": mqtt_info.get("password")
            }
            
    except Exception as e:
        print(f"❌ Failed to get credentials from API: {e}")
        return None

def test_hello_message():
    """Test sending hello message to EMQX."""
    device_mac = "00:16:3e:ac:b5:38"
    
    # Get MQTT credentials
    mqtt_creds = get_mqtt_credentials_from_api(device_mac)
    if not mqtt_creds:
        return
    
    print(f"🔐 MQTT Client ID: {mqtt_creds['client_id']}")
    
    connected = False
    message_received = False
    
    def on_connect(client, userdata, flags, rc, properties=None):
        nonlocal connected
        if rc == 0:
            print(f"✅ MQTT Connected successfully!")
            connected = True
            # Subscribe to response topic
            topic = f"devices/p2p/{device_mac.replace(':', '_')}"
            client.subscribe(topic)
            print(f"📡 Subscribed to response topic: {topic}")
            
            # Send hello message
            hello_msg = {
                "type": "hello",
                "content": "Hello from test client",
                "timestamp": int(time.time() * 1000),
                "device_id": device_mac
            }
            print(f"📤 Sending hello message: {json.dumps(hello_msg)}")
            client.publish("device-server", json.dumps(hello_msg))
            
        else:
            print(f"❌ MQTT Connection failed with code {rc}")
            
    def on_message(client, userdata, msg):
        nonlocal message_received
        try:
            payload = json.loads(msg.payload.decode())
            print(f"🎉 Received response on {msg.topic}: {json.dumps(payload, indent=2)}")
            message_received = True
        except:
            print(f"📨 Received non-JSON message on {msg.topic}: {msg.payload}")
    
    # Create MQTT client
    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=mqtt_creds["client_id"]
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(mqtt_creds["username"], mqtt_creds["password"])
    
    print(f"🔄 Connecting to EMQX broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start()
        
        # Wait for connection
        for i in range(10):
            if connected:
                break
            time.sleep(1)
            print(f"⏳ Waiting for connection... {i+1}/10")
        
        if connected:
            print("✅ Connected! Waiting for hello response...")
            # Wait for response
            for i in range(15):
                if message_received:
                    print("🎉 Test successful - received response!")
                    break
                time.sleep(1)
                print(f"⏳ Waiting for response... {i+1}/15")
            
            if not message_received:
                print("❌ No response received within 15 seconds")
        else:
            print("❌ Failed to connect")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Disconnected from MQTT broker")

if __name__ == "__main__":
    print("🧪 EMQX Hello Message Test")
    print("=" * 50)
    test_hello_message()