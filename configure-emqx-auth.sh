#!/bin/bash

# Configure EMQX HTTP Authentication via API
EMQX_API_BASE="http://localhost:18083/api/v5"
EMQX_USER="admin"
EMQX_PASS="public"

echo "Configuring EMQX HTTP Authentication..."

# First, get current authentication config
echo "Getting current authentication config..."
curl -s -u "${EMQX_USER}:${EMQX_PASS}" \
  -X GET "${EMQX_API_BASE}/authentication" | jq '.'

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
    "clientid": "${clientid}",
    "username": "${username}",
    "password": "${password}",
    "peerhost": "${peerhost}",
    "protocol": "${proto_name}"
  },
  "connect_timeout": "5s",
  "request_timeout": "10s",
  "pool_size": 8,
  "enable_pipelining": 100,
  "request_body": "json"
}'

# Create HTTP Authentication
curl -s -u "${EMQX_USER}:${EMQX_PASS}" \
  -X POST "${EMQX_API_BASE}/authentication" \
  -H "Content-Type: application/json" \
  -d "${AUTH_CONFIG}" | jq '.'

echo "Authentication configuration completed!"

# Verify the configuration
echo "Verifying authentication config..."
curl -s -u "${EMQX_USER}:${EMQX_PASS}" \
  -X GET "${EMQX_API_BASE}/authentication" | jq '.'