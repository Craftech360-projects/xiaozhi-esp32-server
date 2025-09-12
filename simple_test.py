#!/usr/bin/env python3
"""
Simple test to publish to EMQX without authentication (if allowed)
"""
import json
import time
import uuid

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
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1884

def test_simple_publish():
    """Test publishing to internal/server-ingest without authentication."""
    
    connected = False
    published = False
    
    def on_connect(client, userdata, flags, rc, properties=None):
        nonlocal connected
        if rc == 0:
            print(f"✅ MQTT Connected successfully!")
            connected = True
            
            # Test message
            test_msg = {
                "type": "test",
                "timestamp": int(time.time() * 1000),
                "message": "Hello from simple test client",
                "test_id": str(uuid.uuid4())
            }
            
            # Publish test message to internal/server-ingest
            print(f"📤 Publishing test message to internal/server-ingest...")
            result = client.publish("internal/server-ingest", json.dumps(test_msg))
            print(f"   📡 Publish result: {result}")
            
        else:
            print(f"❌ MQTT Connection failed with code {rc}")
            
    def on_publish(client, userdata, mid):
        nonlocal published
        print(f"✅ Message {mid} published successfully")
        published = True
    
    # Create MQTT client with simple client ID
    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=f"simple_test_{uuid.uuid4().hex[:8]}"
    )
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    print(f"🔄 Connecting to EMQX broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} (no auth)")
    
    try:
        client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
        client.loop_start()
        
        # Wait for connection and test messages
        for i in range(10):
            if connected:
                break
            time.sleep(1)
            print(f"⏳ Waiting for connection... {i+1}/10")
        
        if connected:
            print("✅ Connected! Waiting for publish...")
            # Wait a bit for publish to complete
            for i in range(5):
                if published:
                    break
                time.sleep(1)
                print(f"⏳ Waiting for publish... {i+1}/5")
                
            if published:
                print("✅ Test message published successfully!")
            else:
                print("⚠️ Published but no confirmation received")
                
            print("🔄 Keeping connection open for 3 seconds...")
            time.sleep(3)
        else:
            print("❌ Connection test failed!")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Disconnected from MQTT broker")

if __name__ == "__main__":
    print("🧪 Simple EMQX Publish Test (No Auth)")
    print("=" * 50)
    test_simple_publish()