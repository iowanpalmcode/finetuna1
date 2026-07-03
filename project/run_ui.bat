@echo off
REM AI Agent UI Startup Script for Windows

echo.
echo ======================================================================
echo                    AI Agent Personality Builder
echo ======================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing required dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting AI Agent Web UI Server...
echo.
echo 🚀 Opening http://localhost:5000 in your browser...
echo.
echo Press Ctrl+C to stop the server
echo.
echo ======================================================================

REM Change to project directory
cd /d "%~dp0"

REM Start the server
python ui_server.py
