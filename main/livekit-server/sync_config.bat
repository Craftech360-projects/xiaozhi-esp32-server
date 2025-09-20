@echo off
echo Syncing LiveKit configuration from dashboard...
python sync_config.py

echo.
echo Configuration synced!
echo.
echo To apply changes, restart the LiveKit agent:
echo   python main.py dev
echo.
pause