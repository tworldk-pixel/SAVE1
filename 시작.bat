@echo off
py --version >nul 2>&1
if not errorlevel 1 (
    start http://localhost:8010
    py web_server.py
    pause
    exit /b 0
)
python --version >nul 2>&1
if not errorlevel 1 (
    start http://localhost:8010
    python web_server.py
    pause
    exit /b 0
)
echo [ERROR] Python not found. Please install Python 3.11+.
pause
