#!/usr/bin/env python3
"""
Test script to publish messages to internal/server-ingest topic
"""
import json
import time
import uuid
import base64
import hashlib
import hmac

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

def generate_mqtt_credentials() -> dict:
    """Generate MQTT credentials for the test client."""
    # Create client ID for gateway testing
    client_id = f"GID_gateway@@@test_publisher@@@{uuid.uuid4()}"
    
    # Create username (base64 encoded JSON)
    username_data = {"ip": "127.0.0.1"}
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

def test_internal_ingest():
    """Test publishing to internal/server-ingest topic."""
    
    # Get MQTT credentials
    mqtt_creds = generate_mqtt_credentials()
    
    print(f"🔐 MQTT Credentials:")
    print(f"   Client ID: {mqtt_creds['client_id']}")
    print(f"   Username: {mqtt_creds['username']}")
    print(f"   Password: {mqtt_creds['password'][:20]}...")
    
    connected = False
    
    def on_connect(client, userdata, flags, rc, properties=None):
        nonlocal connected
        if rc == 0:
            print(f"✅ MQTT Connected successfully!")
            connected = True
            
            # Test message 1: Server metrics
            test_msg1 = {
                "type": "metrics",
                "timestamp": int(time.time() * 1000),
                "server": "xiaozhi-server",
                "metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 68.7,
                    "active_connections": 3,
                    "uptime_seconds": 86400
                }
            }
            
            # Test message 2: Log entry
            test_msg2 = {
                "type": "log",
                "timestamp": int(time.time() * 1000),
                "level": "info",
                "service": "audio-processor",
                "message": "Audio processing completed successfully",
                "session_id": str(uuid.uuid4())
            }
            
            # Test message 3: Alert/notification
            test_msg3 = {
                "type": "alert",
                "timestamp": int(time.time() * 1000),
                "severity": "warning",
                "message": "High memory usage detected",
                "details": {
                    "memory_percent": 85.3,
                    "threshold": 80.0
                }
            }
            
            # Publish test messages to internal/server-ingest
            print(f"📤 Publishing test messages to internal/server-ingest...")
            
            client.publish("internal/server-ingest", json.dumps(test_msg1))
            print(f"   ✅ Published metrics message")
            
            time.sleep(1)
            
            client.publish("internal/server-ingest", json.dumps(test_msg2))
            print(f"   ✅ Published log message")
            
            time.sleep(1)
            
            client.publish("internal/server-ingest", json.dumps(test_msg3))
            print(f"   ✅ Published alert message")
            
        else:
            print(f"❌ MQTT Connection failed with code {rc}")
            
    def on_publish(client, userdata, mid):
        print(f"📡 Message {mid} published successfully")
    
    # Create MQTT client
    client = mqtt_client.Client(
        callback_api_version=CallbackAPIVersion.VERSION2,
        client_id=mqtt_creds["client_id"]
    )
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.username_pw_set(mqtt_creds["username"], mqtt_creds["password"])
    
    print(f"\n🔄 Connecting to EMQX broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    
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
            print("✅ Test messages published!")
            print("🔄 Keeping connection open for 5 seconds...")
            time.sleep(5)
        else:
            print("❌ Connection test failed!")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("👋 Disconnected from MQTT broker")

if __name__ == "__main__":
    print("🧪 Testing internal/server-ingest Topic Subscription")
    print("=" * 60)
    test_internal_ingest()