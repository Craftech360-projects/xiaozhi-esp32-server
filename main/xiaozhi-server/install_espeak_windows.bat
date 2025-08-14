@echo off
echo Installing eSpeak-NG for KittenTTS on Windows...
echo.

REM Check if winget is available
winget --version >nul 2>&1
if %errorlevel% == 0 (
    echo Using Windows Package Manager (winget) to install eSpeak-NG...
    winget install espeak-ng
    if %errorlevel% == 0 (
        echo ✅ eSpeak-NG installed successfully!
        echo.
        echo Now run: python install_kittentts.py
        pause
        exit /b 0
    ) else (
        echo ❌ winget installation failed, trying alternative methods...
    )
)

REM Check if chocolatey is available
choco --version >nul 2>&1
if %errorlevel% == 0 (
    echo Using Chocolatey to install eSpeak...
    choco install espeak
    if %errorlevel% == 0 (
        echo ✅ eSpeak installed successfully!
        echo.
        echo Now run: python install_kittentts.py
        pause
        exit /b 0
    ) else (
        echo ❌ Chocolatey installation failed...
    )
)

REM Manual installation instructions
echo.
echo ❌ Automatic installation failed or package managers not available.
echo.
echo 📋 Please install eSpeak-NG manually:
echo 1. Go to: https://github.com/espeak-ng/espeak-ng/releases
echo 2. Download the latest Windows installer (.msi file)
echo 3. Run the installer and follow the setup wizard
echo 4. Restart your command prompt
echo 5. Run: python install_kittentts.py
echo.
echo Opening the download page in your browser...
start https://github.com/espeak-ng/espeak-ng/releases

pause