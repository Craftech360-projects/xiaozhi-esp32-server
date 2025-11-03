# Script to start all services in separate Command Prompt windows
# This script uses dynamic paths and will work for all team members

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Starting All Services" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Get the directory where this script is located
$scriptRoot = $PSScriptRoot

# Path to virtual environment activation script (relative to script location)
$envActivate = Join-Path $scriptRoot "main\env\Scripts\activate.bat"

# Check if virtual environment exists
if (-Not (Test-Path $envActivate)) {
    Write-Host "ERROR: Virtual environment not found at: $envActivate" -ForegroundColor Red
    Write-Host "Please ensure the virtual environment is set up before running this script." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Virtual environment found!" -ForegroundColor Green
Write-Host ""

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Starting Docker containers..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    $dockerCheck = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
        Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit
    }
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker is not installed or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop and try again." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Start MySQL and Redis containers
Write-Host ""
Write-Host "Starting MySQL database (port 3307)..." -ForegroundColor Cyan
docker-compose up -d manager-api-db 2>&1 | Out-Null

Write-Host "Starting Redis cache (port 6380)..." -ForegroundColor Cyan
docker-compose up -d manager-api-redis 2>&1 | Out-Null

Write-Host ""
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "[OK] Docker containers started" -ForegroundColor Green
Write-Host ""

Write-Host "=====================================" -ForegroundColor Yellow
Write-Host "  Terminating existing services..." -ForegroundColor Yellow
Write-Host "=====================================" -ForegroundColor Yellow
Write-Host ""

# Define ports used by each service (excluding Docker ports 3307, 6380)
$ports = @(8002, 8080, 8081, 1883, 7880, 3000, 8884)

# Step 1: Kill all processes on the required ports using taskkill
Write-Host "Step 1: Killing processes by port..." -ForegroundColor Cyan
foreach ($port in $ports) {
    Write-Host "Checking port $port..." -ForegroundColor Gray

    try {
        $connections = netstat -ano | Select-String -Pattern ":\s*$port\s"
        $killedPids = @()

        foreach ($line in $connections) {
            # Extract PID from end of line - handles both TCP and UDP
            if ($line -match '\s+(\d+)\s*$') {
                $pid = $matches[1]
                if ($pid -ne "0" -and $killedPids -notcontains $pid) {
                    try {
                        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                        if ($proc) {
                            Write-Host "  Killing PID $pid ($($proc.ProcessName)) on port $port" -ForegroundColor Yellow
                            $killResult = taskkill /F /PID $pid 2>&1
                            $killedPids += $pid
                            Start-Sleep -Milliseconds 500
                        }
                    } catch {
                        # Process might already be dead
                    }
                }
            }
        }

        if ($killedPids.Count -gt 0) {
            Write-Host "  [OK] Killed $($killedPids.Count) process(es) on port $port" -ForegroundColor Green
        }
    } catch {
        # Silently continue
    }
}

Write-Host ""
Write-Host "Step 2: Killing service processes by name..." -ForegroundColor Cyan

# Kill any remaining Python processes (livekit-server)
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
foreach ($proc in $pythonProcs) {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cmdLine -like "*main.py*" -or $cmdLine -like "*livekit*") {
        Write-Host "  Killing Python process: PID $($proc.Id)" -ForegroundColor Yellow
        taskkill /F /PID $proc.Id 2>$null | Out-Null
    }
}

# Kill any Java processes (manager-api - Spring Boot)
$javaProcs = Get-Process java -ErrorAction SilentlyContinue
foreach ($proc in $javaProcs) {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cmdLine -like "*spring-boot*" -or $cmdLine -like "*manager-api*") {
        Write-Host "  Killing Java process: PID $($proc.Id)" -ForegroundColor Yellow
        taskkill /F /PID $proc.Id 2>$null | Out-Null
    }
}

# Kill any Node processes (manager-web, mqtt-gateway)
$nodeProcs = Get-Process node -ErrorAction SilentlyContinue
foreach ($proc in $nodeProcs) {
    $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)" -ErrorAction SilentlyContinue).CommandLine
    if ($cmdLine -like "*manager-web*" -or $cmdLine -like "*mqtt-gateway*" -or $cmdLine -like "*app.js*" -or $cmdLine -like "*vue*") {
        Write-Host "  Killing Node process: PID $($proc.Id)" -ForegroundColor Yellow
        taskkill /F /PID $proc.Id 2>$null | Out-Null
    }
}

Write-Host ""
Write-Host "Waiting for processes to fully terminate..." -ForegroundColor Cyan
Start-Sleep -Seconds 4

# Verify ports are free
Write-Host ""
Write-Host "Step 3: Verifying all ports are free..." -ForegroundColor Cyan
$portsStillInUse = @()
foreach ($port in $ports) {
    try {
        $netstatCheck = netstat -ano | Select-String -Pattern ":\s*$port\s" | Where-Object { $_ -match "LISTENING|ESTABLISHED|\*:\*" }
        if ($netstatCheck) {
            Write-Host "  [WARN] Port $port is STILL in use!" -ForegroundColor Red
            $portsStillInUse += $port
            # Show what's using it
            foreach ($line in $netstatCheck) {
                if ($line -match '\s+(\d+)\s*$') {
                    $pid = $matches[1]
                    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                    if ($proc) {
                        Write-Host "    -> PID $pid ($($proc.ProcessName))" -ForegroundColor Red
                    }
                }
            }
        } else {
            Write-Host "  [OK] Port $port is free" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [OK] Port $port is free" -ForegroundColor Green
    }
}

Write-Host ""
if ($portsStillInUse.Count -gt 0) {
    Write-Host "WARNING: Could not free all ports: $($portsStillInUse -join ', ')" -ForegroundColor Red
    Write-Host "Services using these ports may fail to start." -ForegroundColor Yellow
    Write-Host "Continuing anyway in 3 seconds... (Press Ctrl+C to cancel)" -ForegroundColor Yellow
    Start-Sleep -Seconds 3
} else {
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "  All ports cleared successfully!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting services in 2 seconds..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  Launching services..." -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Start livekit-server
Write-Host "[1/4] Starting livekit-server..." -ForegroundColor Cyan
$livekitPath = Join-Path $scriptRoot "main\livekit-server"
$cmd1 = 'call "' + $envActivate + '" && cd /d "' + $livekitPath + '" && echo LiveKit Server Starting... && python main.py dev'
Start-Process cmd -ArgumentList "/k", $cmd1

# Add delay between service starts
Start-Sleep -Seconds 2

# Start manager-api
Write-Host "[2/4] Starting manager-api..." -ForegroundColor Cyan
$managerApiPath = Join-Path $scriptRoot "main\manager-api"
$cmd2 = 'call "' + $envActivate + '" && cd /d "' + $managerApiPath + '" && echo Manager API Starting... && mvn spring-boot:run "-Dspring-boot.run.arguments=--spring.profiles.active=dev"'
Start-Process cmd -ArgumentList "/k", $cmd2

# Add delay between service starts
Start-Sleep -Seconds 2

# Start manager-web
Write-Host "[3/4] Starting manager-web..." -ForegroundColor Cyan
$managerWebPath = Join-Path $scriptRoot "main\manager-web"
$cmd3 = 'call "' + $envActivate + '" && cd /d "' + $managerWebPath + '" && echo Manager Web Starting... && npm run serve'
Start-Process cmd -ArgumentList "/k", $cmd3

# Add delay between service starts
Start-Sleep -Seconds 2

# Start mqtt-gateway
Write-Host "[4/4] Starting mqtt-gateway..." -ForegroundColor Cyan
$mqttGatewayPath = Join-Path $scriptRoot "main\mqtt-gateway"
$cmd4 = 'call "' + $envActivate + '" && cd /d "' + $mqttGatewayPath + '" && echo MQTT Gateway Starting... && node app.js'
Start-Process cmd -ArgumentList "/k", $cmd4

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "  All services started successfully!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Running Services:" -ForegroundColor Cyan
Write-Host "  - MySQL Database: localhost:3307 (Docker)" -ForegroundColor Gray
Write-Host "  - Redis Cache: localhost:6380 (Docker)" -ForegroundColor Gray
Write-Host "  - LiveKit Server: CMD Window" -ForegroundColor Gray
Write-Host "  - Manager API: CMD Window (http://localhost:8002)" -ForegroundColor Gray
Write-Host "  - Manager Web: CMD Window (http://localhost:3000)" -ForegroundColor Gray
Write-Host "  - MQTT Gateway: CMD Window" -ForegroundColor Gray
Write-Host ""
Write-Host "To RESTART all services:" -ForegroundColor Cyan
Write-Host "  Simply run this script again!" -ForegroundColor Yellow
Write-Host ""
Write-Host "To STOP all services:" -ForegroundColor Cyan
Write-Host "  1. Close each Command Prompt window" -ForegroundColor Yellow
Write-Host "  2. Run: docker-compose down" -ForegroundColor Yellow
Write-Host ""
Write-Host "This window will close in 5 seconds..." -ForegroundColor Gray
Start-Sleep -Seconds 5
