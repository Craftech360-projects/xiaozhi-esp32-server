@echo off
REM Setup Whisper Server (Windows)

echo 🚀 Setting up Remote Whisper Server
echo ====================================

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
echo 📦 Installing Python packages (this may take a few minutes)...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Create .env file
echo 📝 Creating .env file...
(
echo # Whisper Server Configuration
echo WHISPER_MODEL=base.en
echo HOST=0.0.0.0
echo PORT=8000
) > .env

echo ✅ .env file created

REM Create start script
echo 📝 Creating start script...
(
echo @echo off
echo call venv\Scripts\activate.bat
echo python whisper_server.py
) > start.bat

echo.
echo ✅ Setup complete!
echo.
echo 📝 Next steps:
echo 1. Start server: start.bat
echo 2. Test: curl http://localhost:8000/health
echo.
echo 💡 To change model, edit .env file:
echo    WHISPER_MODEL=tiny.en    (fastest, 500MB)
echo    WHISPER_MODEL=base.en    (recommended, 800MB)
echo    WHISPER_MODEL=small.en   (better quality, 1.2GB)

pause
