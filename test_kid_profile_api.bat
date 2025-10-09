@echo off
setlocal enabledelayedexpansion

REM Kid Profile API Test Script - Windows Version
REM Tests all kid profile endpoints and device-kid linking

set BASE_URL=http://localhost:8002/toy
set MAC_ADDRESS=68:25:dd:bb:f3:a0
set KID_NAME=Rahul
set KID_AGE=10
set KID_GENDER=male
set KID_DOB=2014-10-09

echo ========================================
echo Kid Profile API Test Script
echo ========================================
echo.

REM Step 1: Login to get authentication token
echo Step 1: Login to get authentication token
curl -X POST "%BASE_URL%/login" ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"managerpassword\"}" ^
  -o login_response.json

REM Extract token from response (you may need jq or manually copy token)
echo Please check login_response.json for the token
echo.

REM For the rest of the script, replace YOUR_TOKEN with actual token
set TOKEN=YOUR_TOKEN_HERE

echo Step 2: Create kid profile (Name: %KID_NAME%, Age: %KID_AGE%)
curl -X POST "%BASE_URL%/api/mobile/kids/create" ^
  -H "Content-Type: application/json" ^
  -H "token: %TOKEN%" ^
  -d "{\"name\":\"%KID_NAME%\",\"dateOfBirth\":\"%KID_DOB%\",\"gender\":\"%KID_GENDER%\",\"interests\":\"[\\\"games\\\",\\\"sports\\\",\\\"science\\\"]\",\"avatarUrl\":\"https://example.com/avatar.jpg\"}" ^
  -o create_kid_response.json

echo Check create_kid_response.json for kid ID
echo.

REM Set KID_ID manually after checking response
set KID_ID=1

echo Step 3: Get all kids for current user
curl -X GET "%BASE_URL%/api/mobile/kids/list" ^
  -H "Content-Type: application/json" ^
  -H "token: %TOKEN%"
echo.
echo.

echo Step 4: Get kid by ID (%KID_ID%)
curl -X GET "%BASE_URL%/api/mobile/kids/%KID_ID%" ^
  -H "Content-Type: application/json" ^
  -H "token: %TOKEN%"
echo.
echo.

echo Step 5: Get child profile by MAC (LiveKit endpoint)
curl -X POST "%BASE_URL%/config/child-profile-by-mac" ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Bearer managerpassword" ^
  -d "{\"macAddress\":\"%MAC_ADDRESS%\"}" ^
  -o child_profile_response.json

echo Check child_profile_response.json
echo.

echo ========================================
echo Manual Steps Required:
echo ========================================
echo 1. Copy token from login_response.json and update TOKEN variable in this script
echo 2. Copy kid ID from create_kid_response.json and update KID_ID variable
echo 3. Run SQL to link kid to device:
echo    UPDATE ai_device SET kid_id = [KID_ID] WHERE mac_address = '%MAC_ADDRESS%';
echo 4. Re-run the child-profile-by-mac curl command to verify
echo.

pause
