@echo off
setlocal enabledelayedexpansion

echo ================================
echo SmallTree Nursery Website
echo ================================
echo.

echo [1/3] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)
echo ✓ Python is installed

echo.
echo [2/3] Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some packages might not install correctly
    echo Continuing anyway...
)
echo ✓ Requirements processed

echo.
echo [3/3] Starting Flask application...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Run with auto-restart on crash
:restart
python run.py
if errorlevel 1 (
    echo.
    echo ERROR: Server crashed! Checking for common issues...
    echo.
    echo Common fixes:
    echo 1. Make sure no other server is running on port 5000
    echo 2. Check if all dependencies are installed
    echo 3. Verify database permissions
    echo.
    choice /C YN /M "Do you want to restart the server"
    if errorlevel 2 goto end
    if errorlevel 1 goto restart
)

:end
echo Server stopped normally.
pause
