@echo off
echo Fixing eSpeak for KittenTTS on Windows...
echo This script needs to run as Administrator.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This script must be run as Administrator!
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo ✅ Running as Administrator

REM Check if eSpeak-NG is installed
if not exist "C:\Program Files\eSpeak NG\espeak-ng.exe" (
    echo ❌ eSpeak-NG not found at expected location
    echo Please install eSpeak-NG first from: https://github.com/espeak-ng/espeak-ng/releases
    pause
    exit /b 1
)

echo ✅ Found eSpeak-NG at: C:\Program Files\eSpeak NG\espeak-ng.exe

REM Create espeak.exe copy
echo Creating espeak.exe for phonemizer compatibility...
copy "C:\Program Files\eSpeak NG\espeak-ng.exe" "C:\Program Files\eSpeak NG\espeak.exe"

if %errorlevel% == 0 (
    echo ✅ Successfully created espeak.exe
    echo.
    echo Testing espeak command...
    "C:\Program Files\eSpeak NG\espeak.exe" --version
    
    if %errorlevel% == 0 (
        echo ✅ espeak.exe is working correctly!
        echo.
        echo Now you can run: python test_kittentts.py
    ) else (
        echo ❌ espeak.exe test failed
    )
) else (
    echo ❌ Failed to create espeak.exe
    echo Please check permissions and try again
)

echo.
pause