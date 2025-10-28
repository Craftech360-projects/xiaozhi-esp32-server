@echo off
REM TEN VAD Windows Installation Script
REM This script installs TEN VAD and copies the Windows DLL

echo ========================================
echo TEN VAD Windows Installation
echo ========================================
echo.

REM Check if virtual environment is activated
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please activate your virtual environment first.
    echo Run: .\env\Scripts\activate
    pause
    exit /b 1
)

echo Step 1: Installing TEN VAD from GitHub...
pip install -U git+https://github.com/TEN-framework/ten-vad.git
if %errorlevel% neq 0 (
    echo ERROR: Failed to install TEN VAD
    pause
    exit /b 1
)

echo.
echo Step 2: Cloning TEN VAD repository to get Windows DLL...
git clone --depth 1 https://github.com/TEN-framework/ten-vad.git temp_ten_vad
if %errorlevel% neq 0 (
    echo ERROR: Failed to clone repository
    pause
    exit /b 1
)

echo.
echo Step 3: Copying Windows DLL to site-packages...
REM Get site-packages path
for /f "delims=" %%i in ('python -c "import site; print(site.getsitepackages()[0])"') do set SITE_PACKAGES=%%i

REM Create ten_vad_library directory if it doesn't exist
if not exist "%SITE_PACKAGES%\ten_vad_library" mkdir "%SITE_PACKAGES%\ten_vad_library"

REM Copy DLL
copy /Y "temp_ten_vad\lib\Windows\x64\ten_vad.dll" "%SITE_PACKAGES%\ten_vad_library\ten_vad.dll"
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy DLL
    pause
    exit /b 1
)

echo.
echo Step 4: Cleaning up temporary files...
rmdir /S /Q temp_ten_vad

echo.
echo Step 5: Verifying installation...
python -c "from ten_vad import TenVad; vad = TenVad(hop_size=160, threshold=0.3); print('SUCCESS: TEN VAD installed and working on Windows!')"
if %errorlevel% neq 0 (
    echo ERROR: TEN VAD verification failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo TEN VAD Installation Complete!
echo ========================================
echo.
echo You can now run: python groq_voice_agent.py
echo.
pause
