@echo off
echo 🚀 Starting Simplified LiveKit Agent...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if simple.env exists
if not exist "simple.env" (
    echo ❌ simple.env file not found
    echo Please copy simple.env.example to simple.env and configure it
    pause
    exit /b 1
)

REM Run the simple agent
python simple_main.py dev

pause