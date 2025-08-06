import json
import time
from aiohttp import web
from core.utils.util import get_local_ip
from core.api.base_handler import BaseHandler

TAG = __name__


class OTAHandler(BaseHandler):
    def __init__(self, config: dict):
        super().__init__(config)

    def _get_websocket_url(self, local_ip: str, port: int) -> str:
        """获取websocket地址

        Args:
            local_ip: 本地IP地址
            port: 端口号

        Returns:
            str: websocket地址
        """
        server_config = self.config["server"]
        websocket_config = server_config.get("websocket", "")

        if "你的" not in websocket_config:
            return websocket_config
        else:
            return f"ws://{local_ip}:{port}/xiaozhi/v1/"

    async def handle_post(self, request):
        """处理 OTA POST 请求"""
        try:
            data = await request.text()
            self.logger.bind(tag=TAG).debug(f"OTA请求方法: {request.method}")
            self.logger.bind(tag=TAG).debug(f"OTA请求头: {request.headers}")
            self.logger.bind(tag=TAG).debug(f"OTA请求数据: {data}")

            device_id = request.headers.get("device-id", "")
            if device_id:
                self.logger.bind(tag=TAG).info(f"OTA请求设备ID: {device_id}")
            else:
                raise Exception("OTA请求设备ID为空")

            data_json = json.loads(data)

            server_config = self.config["server"]
            port = int(server_config.get("port", 8000))
            local_ip = get_local_ip()

            # Get device MAC address from the request
            device_mac = request.headers.get("device-id", "unknown_device")
            
            # Check if MQTT gateway is configured
            mqtt_config = server_config.get("mqtt_gateway", {})
            
            # Build response in the exact format as ota.json
            if mqtt_config.get("enabled", False):
                import base64
                import uuid
                
                # Generate client ID in the required format
                device_uuid = str(uuid.uuid4())
                client_id = f"GID_test@@@{device_mac}@@@{device_uuid}"
                
                # Create username (base64 encoded JSON with IP)
                username = base64.b64encode(json.dumps({"ip": local_ip}).encode()).decode()
                
                # Generate a simple password (in production, use proper authentication)
                password = base64.b64encode(f"device_{device_mac}_password".encode()).decode()
                
                return_json = {
                    "mqtt": {
                        "endpoint": f"{mqtt_config.get('broker', local_ip)}:{mqtt_config.get('port', 1883)}",
                        "client_id": client_id,
                        "username": username,
                        "password": password,
                        "publish_topic": "device-server",
                        "subscribe_topic": f"devices/p2p/{device_mac.replace(':', '_')}"
                    },
                    "websocket": {
                        "url": self._get_websocket_url(local_ip, port),
                        "token": "test-token"
                    },
                    "server_time": {
                        "timestamp": int(round(time.time() * 1000)),
                        "timezone_offset": server_config.get("timezone_offset", 8) * 60,
                    },
                    "firmware": {
                        "version": data_json["application"].get("version", "1.0.0"),
                        "url": "",
                    }
                }
            else:
                # Fallback to WebSocket-only format
                return_json = {
                    "server_time": {
                        "timestamp": int(round(time.time() * 1000)),
                        "timezone_offset": server_config.get("timezone_offset", 8) * 60,
                    },
                    "firmware": {
                        "version": data_json["application"].get("version", "1.0.0"),
                        "url": "",
                    },
                    "websocket": {
                        "url": self._get_websocket_url(local_ip, port),
                        "token": "test-token"
                    },
                }
            response = web.Response(
                text=json.dumps(return_json, separators=(",", ":")),
                content_type="application/json",
            )
        except Exception as e:
            return_json = {"success": False, "message": "request error."}
            response = web.Response(
                text=json.dumps(return_json, separators=(",", ":")),
                content_type="application/json",
            )
        finally:
            self._add_cors_headers(response)
            return response

    async def handle_get(self, request):
        """处理 OTA GET 请求"""
        try:
            server_config = self.config["server"]
            local_ip = get_local_ip()
            port = int(server_config.get("port", 8000))
            websocket_url = self._get_websocket_url(local_ip, port)
            message = f"OTA接口运行正常，向设备发送的websocket地址是：{websocket_url}"
            response = web.Response(text=message, content_type="text/plain")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"OTA GET请求异常: {e}")
            response = web.Response(text="OTA接口异常", content_type="text/plain")
        finally:
            self._add_cors_headers(response)
            return response
