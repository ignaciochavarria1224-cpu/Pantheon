@echo off
echo Starting Pantheon Apollo...

set PYTHON=C:\Users\Ignac\AppData\Local\Python\bin\python.exe
set APOLLO=C:\Users\Ignac\Dropbox\TBD\Pantheon\apps\apollo
set UI=%APOLLO%\ui

:: Start Apollo backend
start "Apollo Backend" cmd /k "cd /d %APOLLO% && %PYTHON% -m uvicorn main:app --port 8001"
timeout /t 4

:: Start Apollo UI (Reflex)
start "Apollo UI" cmd /k "cd /d %UI% && %PYTHON% -m reflex run"

echo.
echo Pantheon Apollo is starting...
echo Web UI:   http://localhost:3000
echo API:      http://localhost:8001
echo Health:   http://localhost:8001/health
echo.
