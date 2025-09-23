#!/usr/bin/env python3
"""
Simple HTTP server to simulate LiveKit API for testing chat data fetching
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse as urlparse
import time

class LiveKitTestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        query_params = urlparse.parse_qs(parsed_path.query)

        if parsed_path.path == '/api/chat-data':
            # Extract agent_id and session_id from query parameters
            agent_id = query_params.get('agent_id', ['unknown'])[0]
            session_id = query_params.get('session_id', ['test-session'])[0]

            # Generate mock chat data
            mock_data = [
                {
                    "session_id": session_id,
                    "type": "user_input_transcribed",
                    "content": "Hello, how are you today?",
                    "speaker": "user",
                    "timestamp": int(time.time() * 1000) - 5000,
                    "agent_id": agent_id,
                    "mac_address": "00:11:22:33:44:55"
                },
                {
                    "session_id": session_id,
                    "type": "speech_created",
                    "content": "I'm doing great, thank you for asking! How can I help you today?",
                    "speaker": "agent",
                    "timestamp": int(time.time() * 1000),
                    "speech_id": "speech-123",
                    "duration_ms": 3500,
                    "agent_id": agent_id,
                    "mac_address": "00:11:22:33:44:55"
                }
            ]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            response = json.dumps(mock_data, indent=2)
            self.wfile.write(response.encode())

            print(f"Served chat data for agent: {agent_id}, session: {session_id}")

        elif parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            health_data = {
                "status": "ok",
                "service": "LiveKit Test Server",
                "timestamp": int(time.time() * 1000)
            }

            response = json.dumps(health_data)
            self.wfile.write(response.encode())

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

if __name__ == '__main__':
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, LiveKitTestHandler)
    print(f"LiveKit Test Server running on http://{server_address[0]}:{server_address[1]}")
    print("Available endpoints:")
    print("  GET /api/chat-data?agent_id=xxx&session_id=yyy")
    print("  GET /health")
    print("Press Ctrl+C to stop...")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()