#!/usr/bin/env python3
"""
Simplified test client for xiaozhi-server without audio hardware dependencies
Tests MQTT connection and session establishment
"""
import json
import time
import uuid
import threading
import socket
import struct
import logging
from typing import Dict, Optional, Tuple
import requests
import paho.mqtt.client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from queue import Queue, Empty

# --- Configuration ---
SERVER_IP = "64.227.170.31"  # Local server IP
OTA_PORT = 8003
MQTT_BROKER_HOST = "64.227.170.31"  # MQTT gateway IP
MQTT_BROKER_PORT = 1884

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("SimpleTestClient")

# --- Global variables ---
mqtt_message_queue = Queue()
udp_session_details = {}

class SimpleTestClient:
    def __init__(self):
        self.mqtt_client = None
        # Use a fixed test MAC address
        self.device_mac_formatted = "00:16:3e:ac:b5:38"
        logger.info(f"Using test MAC address: {self.device_mac_formatted}")
        
        # MQTT credentials will be set from OTA response
        self.mqtt_credentials = None
        
        # The P2P topic will be unique to this client's MAC address
        self.p2p_topic = f"devices/p2p/{self.device_mac_formatted}"
        self.ota_config = {}
        self.udp_socket = None
        self.udp_local_sequence = 0

    def generate_mqtt_credentials(self, device_mac: str) -> Dict[str, str]:
        """Generate MQTT credentials for the gateway."""
        import base64
        import hashlib
        import hmac
        
        # Create client ID
        client_id = f"GID_test@@@{device_mac.replace(':', '_')}@@@{uuid.uuid4()}"
        
        # Create username (base64 encoded JSON)
        username_data = {"ip": "127.0.0.1"}  # Local server IP
        username = base64.b64encode(json.dumps(username_data).encode()).decode()
        
        # Create password (HMAC-SHA256) - must match gateway's logic
        secret_key = "test-signature-key-12345"  # Must match MQTT_SIGNATURE_KEY in gateway's .env
        content = f"{client_id}|{username}"
        password = base64.b64encode(hmac.new(secret_key.encode(), content.encode(), hashlib.sha256).digest()).decode()
        
        return {
            "client_id": client_id,
            "username": username,
            "password": password
        }

    def on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info(f"✅ MQTT Connected! Subscribing to P2P topic: {self.p2p_topic}")
            client.subscribe(self.p2p_topic)
        else:
            logger.error(f"❌ MQTT Connection failed with code {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        """Callback for MQTT message reception."""
        try:
            payload_str = msg.payload.decode()
            payload = json.loads(payload_str)
            logger.info(f"📨 MQTT Message received on topic '{msg.topic}':")
            logger.info(f"    {json.dumps(payload, indent=2)}")
            
            # Add to queue for processing
            mqtt_message_queue.put(payload)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error processing MQTT message: {e}")

    def get_ota_config(self) -> bool:
        """Requests OTA configuration from the server."""
        logger.info(f"🔄 Requesting OTA config from http://{SERVER_IP}:{OTA_PORT}/toy/ota/")
        try:
            session_client_id = str(uuid.uuid4())
            
            headers = {"device-id": self.device_mac_formatted}
            data = {
                "application": {
                    "version": "1.7.6",
                    "name": "DOIT AI Kit v1.7.6"
                },
                "board": {
                    "type": "doit-ai-01-kit"
                },
                "client_id": session_client_id
            }
            response = requests.post(f"http://{SERVER_IP}:{OTA_PORT}/toy/ota/", headers=headers, json=data, timeout=10)
            response.raise_for_status()
            self.ota_config = response.json()
            
            logger.info("✅ OTA Config received:")
            logger.info(json.dumps(self.ota_config, indent=2))
            
            # Extract MQTT credentials from OTA response
            mqtt_info = self.ota_config.get("mqtt", {})
            if mqtt_info:
                self.mqtt_credentials = {
                    "client_id": mqtt_info.get("client_id"),
                    "username": mqtt_info.get("username"),
                    "password": mqtt_info.get("password")
                }
                logger.info(f"✅ Got MQTT credentials from OTA: {self.mqtt_credentials['client_id']}")
            else:
                logger.warning("⚠️ No MQTT credentials in OTA response, generating locally")
                self.mqtt_credentials = self.generate_mqtt_credentials(self.device_mac_formatted)
                logger.info(f"✅ Generated MQTT credentials locally: {self.mqtt_credentials['client_id']}")
            
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get OTA config: {e}")
            return False

    def connect_mqtt(self) -> bool:
        """Connects to the MQTT Broker."""
        logger.info(f"🔄 Connecting to MQTT Gateway at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}...")
        
        self.mqtt_client = mqtt_client.Client(
            callback_api_version=CallbackAPIVersion.VERSION2, 
            client_id=self.mqtt_credentials["client_id"]
        )
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.username_pw_set(
            self.mqtt_credentials["username"], 
            self.mqtt_credentials["password"]
        )
        
        try:
            logger.info(f"   Host: {MQTT_BROKER_HOST}")
            logger.info(f"   Port: {MQTT_BROKER_PORT}")
            logger.info(f"   Client ID: {self.mqtt_credentials['client_id']}")
            logger.info(f"   Username: {self.mqtt_credentials['username']}")
            
            self.mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.mqtt_client.loop_start()
            
            # Wait for connection
            time.sleep(3)
            
            if self.mqtt_client.is_connected():
                logger.info("✅ MQTT client is connected!")
                return True
            else:
                logger.error("❌ MQTT client failed to connect")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT Gateway: {e}")
            return False

    def send_hello_and_get_session(self) -> bool:
        """Sends 'hello' message and waits for session details."""
        logger.info("🔄 Sending 'hello' message and waiting for session details...")
        
        hello_message = {
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
        
        self.mqtt_client.publish("device-server", json.dumps(hello_message))
        logger.info("📤 Published hello message to device-server topic")
        
        try:
            response = mqtt_message_queue.get(timeout=15)
            logger.info("📨 Received response:")
            logger.info(json.dumps(response, indent=2))
            
            if response.get("type") == "hello" and "udp" in response:
                global udp_session_details
                udp_session_details = response
                
                # Create UDP socket for testing connection
                self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.udp_socket.settimeout(5.0)
                
                # Test UDP connectivity with a simple ping
                server_udp_addr = (udp_session_details['udp']['server'], udp_session_details['udp']['port'])
                test_message = b"test-ping-from-server"
                
                logger.info(f"🔄 Testing UDP connectivity to {server_udp_addr}...")
                
                try:
                    self.udp_socket.sendto(test_message, server_udp_addr)
                    logger.info("✅ UDP message sent successfully")
                    
                    # Try to receive a response (may timeout, that's OK)
                    try:
                        data, addr = self.udp_socket.recvfrom(1024)
                        logger.info(f"📨 UDP response received from {addr}: {len(data)} bytes")
                    except socket.timeout:
                        logger.info("⏰ No UDP response (timeout) - this is normal for test ping")
                        
                except Exception as e:
                    logger.error(f"❌ UDP connectivity test failed: {e}")
                
                logger.info("✅ Session established successfully!")
                return True
            else:
                logger.error(f"❌ Received unexpected response type: {response.get('type')}")
                return False
                
        except Empty:
            logger.error("❌ Timed out waiting for 'hello' response from server")
            return False

    def send_listen_message(self):
        """Send a listen message to trigger server response."""
        logger.info("🔄 Sending listen message to trigger server response...")
        
        listen_message = {
            "type": "listen",
            "session_id": udp_session_details["session_id"],
            "state": "detect",
            "text": "hello from simple test client"
        }
        
        self.mqtt_client.publish("device-server", json.dumps(listen_message))
        logger.info("📤 Published listen message")
        
        # Wait for server responses
        logger.info("⏳ Waiting for server responses...")
        responses_received = 0
        
        for i in range(10):  # Wait up to 10 seconds
            try:
                response = mqtt_message_queue.get(timeout=1)
                responses_received += 1
                
                logger.info(f"📨 Response #{responses_received}:")
                logger.info(f"    Type: {response.get('type')}")
                
                if response.get("type") == "tts":
                    logger.info(f"    TTS State: {response.get('state')}")
                elif response.get("type") == "stt":
                    logger.info(f"    STT Text: {response.get('text')}")
                elif response.get("type") == "llm":
                    logger.info(f"    LLM Response: {response.get('text')}")
                elif response.get("type") == "goodbye":
                    logger.info("👋 Received goodbye message")
                    break
                    
            except Empty:
                continue
        
        logger.info(f"✅ Received {responses_received} responses from server")

    def cleanup(self):
        """Clean up resources."""
        logger.info("🔄 Cleaning up...")
        
        if self.mqtt_client and udp_session_details:
            goodbye_message = {
                "type": "goodbye",
                "session_id": udp_session_details.get("session_id")
            }
            self.mqtt_client.publish("device-server", json.dumps(goodbye_message))
            logger.info("👋 Sent goodbye message")
            
        if self.udp_socket:
            self.udp_socket.close()
            
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("🔌 MQTT Disconnected")

    def run_test(self):
        """Run the complete test sequence."""
        logger.info("🧪 Starting simplified xiaozhi-server client test")
        logger.info("=" * 60)
        
        try:
            # Step 1: Get OTA configuration
            if not self.get_ota_config():
                logger.error("❌ Failed to get OTA config")
                return False
                
            # Step 2: Connect to MQTT
            if not self.connect_mqtt():
                logger.error("❌ Failed to connect to MQTT")
                return False
                
            # Step 3: Establish session
            if not self.send_hello_and_get_session():
                logger.error("❌ Failed to establish session")
                return False
                
            # Step 4: Test conversation
            self.send_listen_message()
            
            # Step 5: Wait a bit to see all responses
            time.sleep(3)
            
            logger.info("✅ Test completed successfully!")
            return True
            
        except KeyboardInterrupt:
            logger.info("⚠️ Test interrupted by user")
            return False
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            return False
        finally:
            self.cleanup()

if __name__ == "__main__":
    client = SimpleTestClient()
    success = client.run_test()
    
    if success:
        logger.info("🎉 All tests passed!")
    else:
        logger.info("❌ Some tests failed!")