#!/bin/bash

# Configure EMQX HTTP Authentication via API using correct API key method
EMQX_API_BASE="http://localhost:18083/api/v5"

echo "Configuring EMQX HTTP Authentication via API..."

# Generate API key first
echo "Creating API key..."
API_KEY_RESPONSE=$(curl -s -X POST "${EMQX_API_BASE}/api_key" \
  -u "admin:public" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "config-key",
    "enable": true,
    "expired_at": "2030-01-01T00:00:00Z"
  }')

echo "API Key Response: $API_KEY_RESPONSE"

# Extract API key and secret
API_KEY=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('api_key', ''))" 2>/dev/null)
API_SECRET=$(echo "$API_KEY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('api_secret', ''))" 2>/dev/null)

if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    echo "Failed to get API key, trying with default credentials..."
    API_KEY="admin"
    API_SECRET="public"
fi

echo "Using API_KEY: $API_KEY"

# Configure HTTP Authentication
echo "Configuring HTTP Authentication..."
AUTH_CONFIG='{
  "mechanism": "password_based",
  "backend": "http",
  "method": "post",
  "url": "http://172.17.0.1:8003/mqtt/auth",
  "headers": {
    "content-type": "application/json"
  },
  "body": {
    "client_id": "${clientid}",
    "username": "${username}",
    "password": "${password}",
    "peerhost": "${peerhost}",
    "protocol": "${proto_name}"
  },
  "connect_timeout": "5s",
  "request_timeout": "10s",
  "pool_size": 8,
  "enable_pipelining": 100
}'

# Create HTTP Authentication
AUTH_RESPONSE=$(curl -s -u "${API_KEY}:${API_SECRET}" \
  -X POST "${EMQX_API_BASE}/authentication" \
  -H "Content-Type: application/json" \
  -d "${AUTH_CONFIG}")

echo "Authentication Response: $AUTH_RESPONSE"

# Verify the configuration
echo "Verifying authentication config..."
VERIFY_RESPONSE=$(curl -s -u "${API_KEY}:${API_SECRET}" \
  -X GET "${EMQX_API_BASE}/authentication")

echo "Verification Response: $VERIFY_RESPONSE"

echo "Authentication configuration completed!"