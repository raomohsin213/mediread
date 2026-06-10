@echo off
title AI Medicine Assistant Launcher
echo =======================================================================
echo              AI Medicine Assistant - Automatic Startup Script
echo =======================================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.9+ and check "Add Python to PATH" during setup.
    echo Download Python from: https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

:: Create virtual environment if it does not exist
if not exist "venv" (
    echo [INFO] Creating Python virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b
    )
)

:: Activate the virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b
)

:: Install / Update dependencies
echo [INFO] Checking and installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b
)

:: Run the application
echo [INFO] Starting the AI Medicine Assistant...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Application closed with errors.
    pause
)

echo.
echo [INFO] Shutdown complete.
pause
