#!/usr/bin/env python3
"""
Test basic MQTT connection without authentication
"""
import json
import time

try:
    import paho.mqtt.client as mqtt_client
    from paho.mqtt.enums import CallbackAPIVersion
except ImportError:
    import subprocess
    subprocess.check_call(["pip", "install", "--break-system-packages", "paho-mqtt"])
    import paho.mqtt.client as mqtt_client
    from paho.mqtt.enums import CallbackAPIVersion

# Configuration
MQTT_BROKER_HOST = "64.227.170.31"
MQTT_BROKER_PORT = 1883

def test_simple_mqtt():
    """Test MQTT connection without authentication."""
    connected = False
    
    def on_connect(client, userdata, flags, rc, properties=None):
        nonlocal connected
        if rc == 0:
            print(f"✅ MQTT Connected successfully!")
            connected = True
            client.subscribe("test/topic")
            client.publish("test/topic", "Hello EMQX!")
        else:
            print(f"❌ MQTT Connection failed with code {rc}")
            
    def on_message(client, userdata, msg):
        print(f"📨 Received message: {msg.payload.decode()}")
    
    # Create simple MQTT client (no authentication)
    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id="test-client-simple"
    )
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"🔄 Testing basic MQTT connection to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start()
        
        # Wait for connection
        for i in range(10):
            if connected:
                break
            time.sleep(1)
            print(f"⏳ Waiting... {i+1}/10")
        
        if connected:
            print("✅ Basic MQTT connection successful!")
            time.sleep(5)  # Keep connection open briefly
        else:
            print("❌ Basic MQTT connection failed!")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Disconnected")

if __name__ == "__main__":
    test_simple_mqtt()