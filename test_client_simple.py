#!/usr/bin/env python3
"""
Simple test client to verify the MQTT gateway connection
"""

import json
import time
import uuid
import logging
import paho.mqtt.client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
import base64
import hashlib
import hmac

# Configuration
MQTT_BROKER_HOST = "192.168.1.99"
MQTT_BROKER_PORT = 1883

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("SimpleTestClient")

def generate_unique_mac():
    """Generate a unique MAC address."""
    mac_bytes = [0x00, 0x16, 0x3E, 
                 uuid.uuid4().bytes[0], uuid.uuid4().bytes[1], uuid.uuid4().bytes[2]]
    return '_'.join(f'{b:02x}' for b in mac_bytes)

def generate_mqtt_credentials(mac_address):
    """Generate MQTT credentials for the gateway."""
    group_id = "GID_test"
    client_uuid = str(uuid.uuid4())
    
    client_id = f"{group_id}@@@{mac_address}@@@{client_uuid}"
    
    # Create user data and encode as base64 JSON
    user_data = {"ip": "192.168.1.100"}
    username = base64.b64encode(json.dumps(user_data).encode()).decode()
    
    # Generate password signature
    signature_key = "test-signature-key-12345"
    content = f"{client_id}|{username}"
    password = base64.b64encode(
        hmac.new(signature_key.encode(), content.encode(), hashlib.sha256).digest()
    ).decode()
    
    return {
        "client_id": client_id,
        "username": username,
        "password": password
    }

class SimpleTestClient:
    def __init__(self):
        self.mac_address = generate_unique_mac()
        self.credentials = generate_mqtt_credentials(self.mac_address)
        self.p2p_topic = f"devices/p2p/{self.mac_address}"
        self.device_server_topic = "device-server"
        self.mqtt_client = None
        self.session_id = None
        
        logger.info(f"Generated MAC: {self.mac_address}")
        logger.info(f"Client ID: {self.credentials['client_id']}")

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info(f"✅ Connected! Subscribing to: {self.p2p_topic}")
            client.subscribe(self.p2p_topic)
            # Send hello message
            self.send_hello()
        else:
            logger.error(f"❌ Connection failed: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"📨 Received: {json.dumps(payload, indent=2)}")
            
            if payload.get("type") == "hello" and "session_id" in payload:
                self.session_id = payload["session_id"]
                logger.info(f"🎉 Session established: {self.session_id}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def send_hello(self):
        hello_msg = {
            "type": "hello",
            "version": 3,
            "transport": "mqtt",
            "audio_params": {
                "sample_rate": 16000,
                "channels": 1,
                "frame_duration": 20,
                "format": "opus"
            },
            "features": ["tts", "asr", "vad"]
        }
        logger.info("📤 Sending hello message...")
        self.mqtt_client.publish(self.device_server_topic, json.dumps(hello_msg))

    def run_test(self):
        self.mqtt_client = mqtt_client.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=self.credentials["client_id"]
        )
        
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.username_pw_set(
            self.credentials["username"],
            self.credentials["password"]
        )
        
        try:
            logger.info(f"🔗 Connecting to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            self.mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for a few seconds to see the response
            time.sleep(5)
            
            if self.session_id:
                logger.info("✅ Test successful - session established!")
            else:
                logger.warning("⚠️ No session established")
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
        finally:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

if __name__ == "__main__":
    client = SimpleTestClient()
    client.run_test()