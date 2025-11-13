@echo off
REM Setup script for remote PC (Windows)

echo 🚀 Setting up Remote Whisper + Piper Servers
echo ==============================================

REM Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Please install Python 3.8+
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install requirements
echo 📦 Installing Python packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Download Piper
echo 📥 Downloading Piper...
if not exist "piper" mkdir piper
cd piper
if not exist "piper.exe" (
    echo Downloading Piper for Windows...
    curl -L https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_windows_amd64.zip -o piper.zip
    tar -xf piper.zip
    del piper.zip
    echo ✅ Piper installed
) else (
    echo ✅ Piper already exists
)
cd ..

REM Download Piper model
echo 📥 Downloading Piper model...
if not exist "piper_models" mkdir piper_models
cd piper_models

if not exist "en_US-amy-medium.onnx" (
    curl -L https://github.com/rhasspy/piper/releases/download/v0.0.2/en_US-amy-medium.onnx -o en_US-amy-medium.onnx
    curl -L https://github.com/rhasspy/piper/releases/download/v0.0.2/en_US-amy-medium.onnx.json -o en_US-amy-medium.onnx.json
    echo ✅ Piper model downloaded
) else (
    echo ✅ Piper model already exists
)

cd ..

REM Create .env file
echo 📝 Creating .env file...
(
echo # Whisper Server Configuration
echo WHISPER_MODEL=base.en
echo HOST=0.0.0.0
echo WHISPER_PORT=8000
echo.
echo # Piper Server Configuration
echo PIPER_BINARY=piper\piper.exe
echo PIPER_MODEL=piper_models\en_US-amy-medium.onnx
echo PIPER_VOICE=en_US-amy-medium
echo SAMPLE_RATE=22050
echo PIPER_PORT=8001
) > .env

echo ✅ .env file created

REM Create start scripts
echo 📝 Creating start scripts...

(
echo @echo off
echo call venv\Scripts\activate.bat
echo set PORT=8000
echo python whisper_server.py
) > start_whisper.bat

(
echo @echo off
echo call venv\Scripts\activate.bat
echo set PORT=8001
echo set PIPER_BINARY=piper\piper.exe
echo python piper_server.py
) > start_piper.bat

(
echo @echo off
echo echo 🚀 Starting all services...
echo start "Whisper Server" cmd /k start_whisper.bat
echo start "Piper Server" cmd /k start_piper.bat
echo echo ✅ Services started
echo echo    Whisper: http://0.0.0.0:8000
echo echo    Piper:   http://0.0.0.0:8001
) > start_all.bat

echo.
echo ✅ Setup complete!
echo.
echo 📝 Next steps:
echo 1. Start Whisper server: start_whisper.bat
echo 2. Start Piper server:   start_piper.bat
echo 3. Or start both:        start_all.bat
echo.
echo 🧪 Test endpoints:
echo    curl http://localhost:8000/health
echo    curl http://localhost:8001/health

pause
