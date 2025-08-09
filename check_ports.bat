@echo off
echo Checking if MQTT gateway is listening on port 1883...
netstat -an | findstr :1883

echo.
echo Checking if xiaozhi-server is listening on port 8000...
netstat -an | findstr :8000

echo.
echo Testing connection to localhost:1883...
telnet localhost 1883