# Quick Test - Manual curl commands for PowerShell

$BASE_URL = "http://localhost:8002/toy"

# 1. Login
Write-Host "`n1. Login..." -ForegroundColor Yellow
$login = Invoke-RestMethod -Uri "$BASE_URL/login" -Method Post -Body '{"username":"admin","password":"managerpassword"}' -ContentType "application/json"
$token = $login.token
Write-Host "Token: $($token.Substring(0,20))..." -ForegroundColor Green

# 2. Create Kid
Write-Host "`n2. Creating kid profile (Rahul, 10 years old)..." -ForegroundColor Yellow
$kid = Invoke-RestMethod -Uri "$BASE_URL/api/mobile/kids/create" -Method Post -Headers @{"token"=$token;"Content-Type"="application/json"} -Body '{"name":"Rahul","dateOfBirth":"2014-10-09","gender":"male","interests":"[\"games\",\"sports\",\"science\"]"}'
$kidId = $kid.data.kid.id
Write-Host "Kid ID: $kidId" -ForegroundColor Green

# 3. Get Kid
Write-Host "`n3. Getting kid profile..." -ForegroundColor Yellow
$getKid = Invoke-RestMethod -Uri "$BASE_URL/api/mobile/kids/$kidId" -Method Get -Headers @{"token"=$token}
$getKid.data | ConvertTo-Json

# 4. Manual SQL Step
Write-Host "`n4. MANUAL STEP:" -ForegroundColor Yellow
Write-Host "Run this SQL:" -ForegroundColor Cyan
Write-Host "UPDATE ai_device SET kid_id = $kidId WHERE mac_address = '68:25:dd:bb:f3:a0';" -ForegroundColor White
Read-Host "`nPress Enter after running SQL"

# 5. Test LiveKit endpoint
Write-Host "`n5. Testing LiveKit child-profile endpoint..." -ForegroundColor Yellow
$child = Invoke-RestMethod -Uri "$BASE_URL/config/child-profile-by-mac" -Method Post -Headers @{"Authorization"="Bearer managerpassword";"Content-Type"="application/json"} -Body '{"macAddress":"68:25:dd:bb:f3:a0"}'
Write-Host "`nChild Profile:" -ForegroundColor Green
$child.data | ConvertTo-Json

Write-Host "`n✅ Test complete!" -ForegroundColor Green
