import json
import base64
import hmac
import hashlib
import os
from aiohttp import web
from core.api.base_handler import BaseHandler

# Try to load environment variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TAG = __name__


class MQTTAuthHandler(BaseHandler):
    def __init__(self, config: dict):
        super().__init__(config)
        # Load MQTT signature key from environment or config (same as OTA handler)
        self.mqtt_signature_key = os.getenv(
            'MQTT_SIGNATURE_KEY', 'test-signature-key-12345')

    async def handle_post(self, request):
        """Handle MQTT Authentication request from EMQX"""
        try:
            # Get authentication data from EMQX
            data = await request.json()
            client_id = data.get('client_id', '')
            username = data.get('username', '')
            password = data.get('password', '')
            
            self.logger.bind(tag=TAG).info(
                f"MQTT Auth request for client_id: {client_id[:20]}...")
            
            # Validate required fields
            if not client_id or not username or not password:
                self.logger.bind(tag=TAG).warning(
                    "MQTT Auth failed: Missing required fields")
                return web.Response(status=401, text="Missing credentials")
            
            # Validate client_id format (should match: GID_test@@@mac_address@@@uuid)
            if not client_id.startswith("GID_test@@@") or client_id.count("@@@") != 2:
                self.logger.bind(tag=TAG).warning(
                    f"MQTT Auth failed: Invalid client_id format: {client_id}")
                return web.Response(status=401, text="Invalid client ID format")
            
            # Validate username (should be base64 encoded JSON with IP)
            try:
                decoded_username = base64.b64decode(username).decode()
                user_data = json.loads(decoded_username)
                if 'ip' not in user_data:
                    raise ValueError("Missing IP in username")
            except Exception as e:
                self.logger.bind(tag=TAG).warning(
                    f"MQTT Auth failed: Invalid username format: {e}")
                return web.Response(status=401, text="Invalid username format")
            
            # Generate expected password using same logic as OTA handler
            content = f"{client_id}|{username}"
            expected_password = base64.b64encode(
                hmac.new(self.mqtt_signature_key.encode(),
                         content.encode(), hashlib.sha256).digest()
            ).decode()
            
            # Compare passwords
            if password == expected_password:
                self.logger.bind(tag=TAG).info(
                    f"MQTT Auth successful for client: {client_id[:20]}...")
                return web.Response(status=200, text="Authentication successful")
            else:
                self.logger.bind(tag=TAG).warning(
                    f"MQTT Auth failed: Invalid password for client: {client_id[:20]}...")
                return web.Response(status=401, text="Authentication failed")
                
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"MQTT Auth exception: {e}")
            return web.Response(status=500, text="Internal server error")
        finally:
            # Always add CORS headers for web requests
            pass

    async def handle_get(self, request):
        """Handle GET request for MQTT Auth status"""
        try:
            status_message = f"""MQTT Authentication Handler Status:
- Handler: Active
- Signature Key: {'Configured' if self.mqtt_signature_key else 'Not Set'}
- Endpoint: /mqtt/auth (POST)
- Compatible with EMQX HTTP Authentication Plugin"""
            
            response = web.Response(
                text=status_message, 
                content_type="text/plain; charset=utf-8"
            )
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"MQTT Auth GET exception: {e}")
            response = web.Response(
                text="MQTT Auth handler error", 
                content_type="text/plain"
            )
        finally:
            self._add_cors_headers(response)
            return response