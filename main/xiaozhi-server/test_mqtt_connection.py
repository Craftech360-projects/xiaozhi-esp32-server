import json
import time
import uuid
import base64
import hashlib
import hmac
import logging
import requests
import paho.mqtt.client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

# --- Configuration ---
SERVER_IP = "192.168.1.236"
OTA_PORT = 8002
MQTT_BROKER_HOST = "139.59.5.142"
MQTT_BROKER_PORT = 1883

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("MQTTTestClient")

def generate_mqtt_credentials(device_mac: str):
    """Generate MQTT credentials for the gateway."""
    # Create client ID
    client_id = f"GID_test@@@{device_mac}@@@{uuid.uuid4()}"

    # Create username (base64 encoded JSON)
    username_data = {"ip": "192.168.1.10"}  # Placeholder IP
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

class MQTTTestClient:
    def __init__(self):
        self.mqtt_client = None
        self.device_mac_formatted = "00:16:3e:ac:b5:38"
        self.mqtt_credentials = None
        self.ota_config = {}
        self.connected = False
        logger.info(f"Client initialized with MAC: {self.device_mac_formatted}")

    def on_mqtt_connect(self, client, userdata, flags, rc, properties=None):
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info(f"✅ MQTT Connected successfully! rc={rc}")
            self.connected = True
            # Subscribe to test topic
            test_topic = f"devices/p2p/{self.device_mac_formatted}"
            client.subscribe(test_topic)
            logger.info(f"📡 Subscribed to topic: {test_topic}")
        else:
            logger.error(f"❌ MQTT Connection failed with code {rc}")
            self.connected = False

    def on_mqtt_disconnect(self, client, userdata, rc, properties=None):
        """Callback for MQTT disconnection."""
        logger.info(f"🔌 MQTT Disconnected with rc={rc}")
        self.connected = False

    def on_mqtt_message(self, client, userdata, msg):
        """Callback for MQTT message reception."""
        try:
            payload_str = msg.payload.decode()
            payload = json.loads(payload_str)
            logger.info(f"📨 MQTT Message received on topic '{msg.topic}':\n{json.dumps(payload, indent=2)}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def get_ota_config(self):
        """Requests OTA configuration from the server."""
        logger.info(f"▶️ STEP 1: Requesting OTA config from http://{SERVER_IP}:{OTA_PORT}/toy/ota/")
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

            logger.info(f"📤 OTA Request Headers: {headers}")
            logger.info(f"📤 OTA Request Body: {json.dumps(data, indent=2)}")

            response = requests.post(f"http://{SERVER_IP}:{OTA_PORT}/toy/ota/", headers=headers, json=data, timeout=5)
            response.raise_for_status()
            self.ota_config = response.json()
            logger.info(f"✅ OTA Config received: {json.dumps(self.ota_config, indent=2)}")

            # Extract MQTT credentials from OTA response
            mqtt_info = self.ota_config.get("mqtt", {})
            if mqtt_info:
                self.mqtt_credentials = {
                    "client_id": mqtt_info.get("client_id"),
                    "username": mqtt_info.get("username"),
                    "password": mqtt_info.get("password")
                }
                logger.info(f"✅ Got MQTT credentials from OTA:")
                logger.info(f"   Client ID: {self.mqtt_credentials['client_id']}")
                logger.info(f"   Username: {self.mqtt_credentials['username']}")
                logger.info(f"   Password (first 20 chars): {self.mqtt_credentials['password'][:20]}...")
            else:
                logger.warning("⚠️ No MQTT credentials in OTA response, generating locally")
                self.mqtt_credentials = generate_mqtt_credentials(self.device_mac_formatted)

            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to get OTA config: {e}")
            return False

    def connect_mqtt(self):
        """Connects to the MQTT Broker."""
        # Get MQTT configuration from OTA response
        mqtt_config = self.ota_config.get("mqtt_gateway", {})
        mqtt_broker = mqtt_config.get("broker", MQTT_BROKER_HOST)
        mqtt_port = mqtt_config.get("port", MQTT_BROKER_PORT)

        logger.info("=" * 60)
        logger.info("📍 MQTT Connection Details:")
        logger.info(f"   Broker: {mqtt_broker}")
        logger.info(f"   Port: {mqtt_port}")
        logger.info(f"   Client ID: {self.mqtt_credentials.get('client_id', 'NOT SET')}")
        logger.info(f"   Username: {self.mqtt_credentials.get('username', 'NOT SET')}")
        logger.info(f"   Password (first 20 chars): {self.mqtt_credentials.get('password', 'NOT SET')[:20]}...")
        logger.info("=" * 60)

        logger.info(f"▶️ STEP 2: Connecting to MQTT Gateway at {mqtt_broker}:{mqtt_port}...")

        # Create MQTT client with v2 callback API
        self.mqtt_client = mqtt_client.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=self.mqtt_credentials["client_id"],
            protocol=mqtt_client.MQTTv311  # Explicitly set MQTT v3.1.1
        )

        # Enable logging
        self.mqtt_client.enable_logger()

        # Set callbacks
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
        self.mqtt_client.on_message = self.on_mqtt_message

        # Set credentials
        self.mqtt_client.username_pw_set(
            self.mqtt_credentials["username"],
            self.mqtt_credentials["password"]
        )

        try:
            logger.info("🔄 Attempting MQTT connection...")
            logger.info(f"   Using protocol: MQTTv3.1.1")

            # Connect with keepalive of 60 seconds
            self.mqtt_client.connect(mqtt_broker, mqtt_port, 60)

            # Start the network loop
            self.mqtt_client.loop_start()

            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.connected:
                logger.info("✅ MQTT client connected successfully!")

                # Send a test hello message
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

                logger.info("📤 Sending hello message to device-server topic...")
                self.mqtt_client.publish("device-server", json.dumps(hello_message))
                logger.info("✅ Hello message sent successfully!")

                return True
            else:
                logger.error(f"❌ Connection timeout after {timeout} seconds")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to MQTT Gateway: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            logger.error(f"   Broker: {mqtt_broker}:{mqtt_port}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.mqtt_client:
            logger.info("🔌 Disconnecting from MQTT...")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("✅ Disconnected")

    def run_test(self):
        """Run the MQTT connection test."""
        logger.info("=" * 60)
        logger.info("🚀 Starting MQTT Connection Test")
        logger.info("=" * 60)

        if not self.get_ota_config():
            logger.error("❌ Failed to get OTA config. Exiting.")
            return False

        if not self.connect_mqtt():
            logger.error("❌ Failed to connect to MQTT. Exiting.")
            return False

        # Keep connection alive for a bit to observe any messages
        logger.info("⏳ Keeping connection alive for 5 seconds...")
        time.sleep(5)

        self.disconnect()

        logger.info("=" * 60)
        logger.info("✅ Test completed successfully!")
        logger.info("=" * 60)
        return True

if __name__ == "__main__":
    client = MQTTTestClient()
    try:
        success = client.run_test()
        if success:
            logger.info("✅ Python client connected to EMQX successfully!")
        else:
            logger.info("❌ Python client failed to connect to EMQX")
    except KeyboardInterrupt:
        logger.info("Manual interruption detected. Cleaning up...")
        client.disconnect()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        client.disconnect()