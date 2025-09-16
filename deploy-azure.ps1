# Azure Deployment Script for xiaozhi-esp32-server
param(
    [Parameter(Mandatory=$true)]
    [string]$Environment,

    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "xiaozhi-rg",

    [Parameter(Mandatory=$false)]
    [string]$Location = "East US"
)

Write-Host "Deploying xiaozhi-esp32-server to Azure ($Environment environment)" -ForegroundColor Green

# Set Azure subscription (modify as needed)
# az account set --subscription "your-subscription-id"

# Create resource group if it doesn't exist
Write-Host "Creating resource group: $ResourceGroup" -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location

# Deploy infrastructure using Bicep
Write-Host "Deploying Azure infrastructure..." -ForegroundColor Yellow
$deploymentResult = az deployment group create `
    --resource-group $ResourceGroup `
    --template-file "azure-infrastructure.bicep" `
    --parameters environment=$Environment `
    --parameters appName="xiaozhi" `
    --query "properties.outputs" `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Error "Infrastructure deployment failed!"
    exit 1
}

Write-Host "Infrastructure deployed successfully!" -ForegroundColor Green

# Extract service URLs
$managerApiUrl = $deploymentResult.managerApiUrl.value
$managerWebUrl = $deploymentResult.managerWebUrl.value
$mqttGatewayUrl = $deploymentResult.mqttGatewayUrl.value

Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "Manager API: $managerApiUrl" -ForegroundColor White
Write-Host "Manager Web: $managerWebUrl" -ForegroundColor White
Write-Host "MQTT Gateway: $mqttGatewayUrl" -ForegroundColor White

# Build and deploy each component
Write-Host "`nBuilding and deploying applications..." -ForegroundColor Yellow

# 1. Deploy Manager API (Java)
Write-Host "Building Manager API..." -ForegroundColor Yellow
Set-Location "main/manager-api"
mvn clean package -DskipTests
if ($LASTEXITCODE -ne 0) {
    Write-Error "Manager API build failed!"
    exit 1
}

Write-Host "Deploying Manager API..." -ForegroundColor Yellow
az webapp deploy `
    --resource-group $ResourceGroup `
    --name "xiaozhi-$Environment-manager-api" `
    --src-path "target/xiaozhi-esp32-api.jar" `
    --type jar

Set-Location "../.."

# 2. Deploy Manager Web (Vue.js)
Write-Host "Building Manager Web..." -ForegroundColor Yellow
Set-Location "main/manager-web"
npm ci --legacy-peer-deps
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Manager Web build failed!"
    exit 1
}

Write-Host "Deploying Manager Web..." -ForegroundColor Yellow
Compress-Archive -Path "dist/*" -DestinationPath "manager-web.zip" -Force
az webapp deploy `
    --resource-group $ResourceGroup `
    --name "xiaozhi-$Environment-manager-web" `
    --src-path "manager-web.zip" `
    --type zip

Remove-Item "manager-web.zip"
Set-Location "../.."

# 3. Deploy MQTT Gateway (Node.js)
Write-Host "Building MQTT Gateway..." -ForegroundColor Yellow
Set-Location "main/mqtt-gateway"
npm install --omit=dev
if ($LASTEXITCODE -ne 0) {
    Write-Error "MQTT Gateway build failed!"
    exit 1
}

Write-Host "Deploying MQTT Gateway..." -ForegroundColor Yellow
Compress-Archive -Path "*" -DestinationPath "mqtt-gateway.zip" -Force
az webapp deploy `
    --resource-group $ResourceGroup `
    --name "xiaozhi-$Environment-mqtt-gateway" `
    --src-path "mqtt-gateway.zip" `
    --type zip

Remove-Item "mqtt-gateway.zip"
Set-Location "../.."

Write-Host "`nDeployment completed successfully!" -ForegroundColor Green
Write-Host "Access your applications at the URLs shown above." -ForegroundColor Cyan

# Health checks
Write-Host "`nPerforming health checks..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

try {
    $apiHealth = Invoke-WebRequest -Uri "$managerApiUrl/actuator/health" -TimeoutSec 10
    Write-Host "✓ Manager API is healthy" -ForegroundColor Green
} catch {
    Write-Host "✗ Manager API health check failed" -ForegroundColor Red
}

try {
    $webHealth = Invoke-WebRequest -Uri $managerWebUrl -TimeoutSec 10
    Write-Host "✓ Manager Web is accessible" -ForegroundColor Green
} catch {
    Write-Host "✗ Manager Web health check failed" -ForegroundColor Red
}

try {
    $gatewayHealth = Invoke-WebRequest -Uri "$mqttGatewayUrl/health" -TimeoutSec 10
    Write-Host "✓ MQTT Gateway is healthy" -ForegroundColor Green
} catch {
    Write-Host "✗ MQTT Gateway health check failed" -ForegroundColor Red
}

Write-Host "`nDeployment Summary:" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor White
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor White
Write-Host "Manager API: $managerApiUrl" -ForegroundColor White
Write-Host "Manager Web: $managerWebUrl" -ForegroundColor White
Write-Host "MQTT Gateway: $mqttGatewayUrl" -ForegroundColor White