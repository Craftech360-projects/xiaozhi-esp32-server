#!/usr/bin/env pwsh
# Simplified LiveKit Agent Startup Script

Write-Host "🚀 Starting Simplified LiveKit Agent..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if simple.env exists
if (-not (Test-Path "simple.env")) {
    Write-Host "❌ simple.env file not found" -ForegroundColor Red
    Write-Host "Please copy simple.env.example to simple.env and configure it" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "📁 Working directory: $(Get-Location)" -ForegroundColor Cyan
Write-Host "🔧 Environment file: simple.env" -ForegroundColor Cyan
Write-Host "🤖 Starting agent..." -ForegroundColor Cyan
Write-Host ("-" * 50) -ForegroundColor Gray

try {
    # Run the simple agent
    python simple_main.py dev
} catch {
    Write-Host "❌ Error running agent: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}