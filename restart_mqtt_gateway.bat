@echo off
echo Stopping any existing mqtt-gateway processes...
taskkill /f /im node.exe 2>nul

echo Starting mqtt-gateway...
cd main\mqtt-gateway
node app.js