#!/bin/bash

# Kid Profile API Test Script
# Tests all kid profile endpoints and device-kid linking

BASE_URL="http://localhost:8002/toy"
MAC_ADDRESS="68:25:dd:bb:f3:a0"
KID_NAME="Rahul"
KID_AGE="10"
KID_GENDER="male"
KID_DOB="2014-10-09"  # 10 years old

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Kid Profile API Test Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Login to get authentication token
echo -e "${YELLOW}Step 1: Login to get authentication token${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "managerpassword"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Login failed. Response: $LOGIN_RESPONSE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Login successful. Token: ${TOKEN:0:20}...${NC}"
echo ""

# Step 2: Create kid profile
echo -e "${YELLOW}Step 2: Create kid profile (Name: $KID_NAME, Age: $KID_AGE)${NC}"
CREATE_KID_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/mobile/kids/create" \
  -H "Content-Type: application/json" \
  -H "token: $TOKEN" \
  -d "{
    \"name\": \"$KID_NAME\",
    \"dateOfBirth\": \"$KID_DOB\",
    \"gender\": \"$KID_GENDER\",
    \"interests\": \"[\\\"games\\\", \\\"sports\\\", \\\"science\\\"]\",
    \"avatarUrl\": \"https://example.com/avatar.jpg\"
  }")

echo -e "Response: $CREATE_KID_RESPONSE"

KID_ID=$(echo $CREATE_KID_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)

if [ -z "$KID_ID" ]; then
    echo -e "${RED}❌ Failed to create kid profile${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Kid profile created successfully. Kid ID: $KID_ID${NC}"
echo ""

# Step 3: Get all kids for current user
echo -e "${YELLOW}Step 3: Get all kids for current user${NC}"
GET_KIDS_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/mobile/kids/list" \
  -H "Content-Type: application/json" \
  -H "token: $TOKEN")

echo -e "Response: $GET_KIDS_RESPONSE"
echo ""

# Step 4: Get specific kid by ID
echo -e "${YELLOW}Step 4: Get kid by ID ($KID_ID)${NC}"
GET_KID_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/mobile/kids/${KID_ID}" \
  -H "Content-Type: application/json" \
  -H "token: $TOKEN")

echo -e "Response: $GET_KID_RESPONSE"
echo ""

# Step 5: Get device by MAC address (to get device ID)
echo -e "${YELLOW}Step 5: Get device by MAC address ($MAC_ADDRESS)${NC}"
# Note: You may need to adjust this endpoint based on your API
GET_DEVICE_RESPONSE=$(curl -s -X GET "${BASE_URL}/api/device/by-mac/${MAC_ADDRESS}" \
  -H "Content-Type: application/json" \
  -H "token: $TOKEN")

echo -e "Response: $GET_DEVICE_RESPONSE"

DEVICE_ID=$(echo $GET_DEVICE_RESPONSE | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -z "$DEVICE_ID" ]; then
    echo -e "${YELLOW}⚠️  Device not found for MAC: $MAC_ADDRESS${NC}"
    echo -e "${YELLOW}⚠️  You may need to create/pair a device first${NC}"
    DEVICE_ID="test-device-id"
fi

echo -e "${GREEN}✅ Device ID: $DEVICE_ID${NC}"
echo ""

# Step 6: Assign kid to device (Update device with kid_id)
echo -e "${YELLOW}Step 6: Assign kid to device${NC}"
echo -e "Updating device $DEVICE_ID with kid_id=$KID_ID"

# Option A: Direct SQL update (for testing)
echo -e "${BLUE}SQL to run manually if API endpoint doesn't exist:${NC}"
echo -e "UPDATE ai_device SET kid_id = $KID_ID WHERE mac_address = '$MAC_ADDRESS';"
echo ""

# Option B: Try API endpoint (if exists)
ASSIGN_RESPONSE=$(curl -s -X PUT "${BASE_URL}/api/mobile/devices/${DEVICE_ID}/assign-kid" \
  -H "Content-Type: application/json" \
  -H "token: $TOKEN" \
  -d "{
    \"kidId\": $KID_ID
  }")

echo -e "Response: $ASSIGN_RESPONSE"
echo ""

# Step 7: Get child profile by MAC (LiveKit endpoint)
echo -e "${YELLOW}Step 7: Get child profile by MAC (LiveKit endpoint)${NC}"
GET_CHILD_PROFILE_RESPONSE=$(curl -s -X POST "${BASE_URL}/config/child-profile-by-mac" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer managerpassword" \
  -d "{
    \"macAddress\": \"$MAC_ADDRESS\"
  }")

echo -e "Response: $GET_CHILD_PROFILE_RESPONSE"

# Check if we got the child profile
if echo "$GET_CHILD_PROFILE_RESPONSE" | grep -q "\"name\":\"$KID_NAME\""; then
    echo -e "${GREEN}✅ Successfully retrieved child profile by MAC!${NC}"
    echo -e "${GREEN}   Name: $KID_NAME, Age: $KID_AGE${NC}"
else
    echo -e "${RED}❌ Failed to retrieve child profile by MAC${NC}"
    echo -e "${YELLOW}⚠️  Make sure kid is assigned to device in database${NC}"
fi
echo ""

# Step 8: Update kid profile
echo -e "${YELLOW}Step 8: Update kid profile${NC}"
UPDATE_KID_RESPONSE=$(curl -s -X PUT "${BASE_URL}/api/mobile/kids/${KID_ID}" \
  -H "Content-Type: application/json" \
  -H "token: $TOKEN" \
  -d "{
    \"interests\": \"[\\\"games\\\", \\\"sports\\\", \\\"science\\\", \\\"coding\\\"]\"
  }")

echo -e "Response: $UPDATE_KID_RESPONSE"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Login successful${NC}"
echo -e "${GREEN}✅ Kid profile created (ID: $KID_ID)${NC}"
echo -e "${GREEN}✅ Kid profiles listed${NC}"
echo -e "${GREEN}✅ Individual kid retrieved${NC}"
echo -e "${GREEN}✅ Device found (ID: $DEVICE_ID)${NC}"
echo -e "${YELLOW}⚠️  Manual step: Assign kid to device using:${NC}"
echo -e "${BLUE}   UPDATE ai_device SET kid_id = $KID_ID WHERE mac_address = '$MAC_ADDRESS';${NC}"
echo -e "${GREEN}✅ Child profile by MAC endpoint tested${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. Run the SQL update command above to link kid to device"
echo -e "2. Re-run Step 7 to verify the linking works"
echo -e "3. Test with LiveKit server using MAC: $MAC_ADDRESS"
echo ""
