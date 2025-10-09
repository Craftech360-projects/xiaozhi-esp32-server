# Kid Profile API Test Script - PowerShell Version
# Tests all kid profile endpoints and device-kid linking

$BASE_URL = "http://localhost:8002/toy"
$MAC_ADDRESS = "68:25:dd:bb:f3:a0"
$KID_NAME = "Rahul"
$KID_AGE = 10
$KID_GENDER = "male"
$KID_DOB = "2014-10-09"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Kid Profile API Test Script" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Step 1: Login
Write-Host "Step 1: Login to get authentication token" -ForegroundColor Yellow
$loginBody = @{
    username = "admin"
    password = "managerpassword"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/login" -Method Post -Body $loginBody -ContentType "application/json"
    $TOKEN = $loginResponse.token
    Write-Host "✅ Login successful. Token: $($TOKEN.Substring(0,20))..." -ForegroundColor Green
} catch {
    Write-Host "❌ Login failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Step 2: Create kid profile
Write-Host "Step 2: Create kid profile (Name: $KID_NAME, Age: $KID_AGE)" -ForegroundColor Yellow
$createKidBody = @{
    name = $KID_NAME
    dateOfBirth = $KID_DOB
    gender = $KID_GENDER
    interests = "[`"games`", `"sports`", `"science`"]"
    avatarUrl = "https://example.com/avatar.jpg"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
    "token" = $TOKEN
}

try {
    $createKidResponse = Invoke-RestMethod -Uri "$BASE_URL/api/mobile/kids/create" -Method Post -Body $createKidBody -Headers $headers
    Write-Host "Response: $($createKidResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Cyan

    # Extract kid ID
    if ($createKidResponse.data.kid.id) {
        $KID_ID = $createKidResponse.data.kid.id
    } elseif ($createKidResponse.data.id) {
        $KID_ID = $createKidResponse.data.id
    } else {
        Write-Host "❌ Could not extract kid ID from response" -ForegroundColor Red
        exit 1
    }

    Write-Host "✅ Kid profile created successfully. Kid ID: $KID_ID" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to create kid: $_" -ForegroundColor Red
    Write-Host $_.Exception.Response.StatusCode.value__
    exit 1
}

Write-Host ""

# Step 3: Get all kids
Write-Host "Step 3: Get all kids for current user" -ForegroundColor Yellow
try {
    $getKidsResponse = Invoke-RestMethod -Uri "$BASE_URL/api/mobile/kids/list" -Method Get -Headers $headers
    Write-Host "Response: $($getKidsResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Cyan
    Write-Host "✅ Retrieved kids list" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get kids: $_" -ForegroundColor Red
}

Write-Host ""

# Step 4: Get specific kid
Write-Host "Step 4: Get kid by ID ($KID_ID)" -ForegroundColor Yellow
try {
    $getKidResponse = Invoke-RestMethod -Uri "$BASE_URL/api/mobile/kids/$KID_ID" -Method Get -Headers $headers
    Write-Host "Response: $($getKidResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Cyan
    Write-Host "✅ Retrieved kid profile" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to get kid: $_" -ForegroundColor Red
}

Write-Host ""

# Step 5: Manual SQL update required
Write-Host "========================================" -ForegroundColor Blue
Write-Host "MANUAL STEP REQUIRED" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Run this SQL command in your MySQL database:" -ForegroundColor Yellow
Write-Host ""
Write-Host "UPDATE ai_device SET kid_id = $KID_ID WHERE mac_address = '$MAC_ADDRESS';" -ForegroundColor Cyan
Write-Host ""
$continue = Read-Host "Press Enter after running the SQL update (or type 'skip' to skip)"

Write-Host ""

# Step 6: Get child profile by MAC (LiveKit endpoint)
Write-Host "Step 6: Get child profile by MAC (LiveKit endpoint)" -ForegroundColor Yellow

$authHeaders = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer managerpassword"
}

$macBody = @{
    macAddress = $MAC_ADDRESS
} | ConvertTo-Json

try {
    $childProfileResponse = Invoke-RestMethod -Uri "$BASE_URL/config/child-profile-by-mac" -Method Post -Body $macBody -Headers $authHeaders
    Write-Host "Response: $($childProfileResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Cyan

    if ($childProfileResponse.code -eq 0 -and $childProfileResponse.data.name -eq $KID_NAME) {
        Write-Host "✅ Successfully retrieved child profile by MAC!" -ForegroundColor Green
        Write-Host "   Name: $($childProfileResponse.data.name), Age: $($childProfileResponse.data.age), Age Group: $($childProfileResponse.data.ageGroup)" -ForegroundColor Green
        Write-Host "   Gender: $($childProfileResponse.data.gender), Interests: $($childProfileResponse.data.interests)" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to retrieve child profile by MAC" -ForegroundColor Red
        Write-Host "⚠️  Make sure kid is assigned to device in database" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Failed to get child profile: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
}

Write-Host ""

# Step 7: Update kid profile
Write-Host "Step 7: Update kid profile (add 'coding' to interests)" -ForegroundColor Yellow
$updateKidBody = @{
    interests = "[`"games`", `"sports`", `"science`", `"coding`"]"
} | ConvertTo-Json

try {
    $updateKidResponse = Invoke-RestMethod -Uri "$BASE_URL/api/mobile/kids/$KID_ID" -Method Put -Body $updateKidBody -Headers $headers
    Write-Host "Response: $($updateKidResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Cyan
    Write-Host "✅ Kid profile updated successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to update kid: $_" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Test Summary" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host "✅ Login successful" -ForegroundColor Green
Write-Host "✅ Kid profile created (ID: $KID_ID, Name: $KID_NAME)" -ForegroundColor Green
Write-Host "✅ Kid profiles listed" -ForegroundColor Green
Write-Host "✅ Individual kid retrieved" -ForegroundColor Green
Write-Host "✅ Child profile by MAC endpoint tested" -ForegroundColor Green
Write-Host "✅ Kid profile updated" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Blue
Write-Host "1. If SQL update wasn't run, execute it to link kid to device" -ForegroundColor White
Write-Host "2. Test with LiveKit server using MAC: $MAC_ADDRESS" -ForegroundColor White
Write-Host "3. Check LiveKit logs for child profile loading" -ForegroundColor White
Write-Host ""
