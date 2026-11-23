@echo off
setlocal enabledelayedexpansion
title AI Medicine Assistant - Complete Setup & Diagnostic Tester
color 0a

echo =======================================================================
echo          AI MEDICINE ASSISTANT - SETUP & VERIFICATION SCRIPT
echo =======================================================================
echo.

:: 1. Detect Python
set "PY_CMD="
python --version >nul 2>&1
if !errorlevel! equ 0 (
    set "PY_CMD=python"
) else (
    py --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    color 0c
    echo [ERROR] Python was not found on your system!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to tick "Add Python to PATH".
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PY_CMD% --version 2^>^&1') do echo [FOUND] System %%v

:: 2. Create Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Creating Python virtual environment (venv)...
    %PY_CMD% -m venv venv
    if !errorlevel! neq 0 (
        color 0c
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: 3. Install/Update all dependencies
echo.
echo [INFO] Upgrading pip, setuptools, wheel...
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel --quiet

echo [INFO] Installing/Verifying all requirements from requirements.txt...
venv\Scripts\python.exe -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    color 0c
    echo [ERROR] Package installation failed. Please check internet connection.
    pause
    exit /b 1
)

echo Successfully installed on %date% %time% > "venv\.installed"

:: 4. Run System Verification Suite
echo.
echo =======================================================================
echo               RUNNING DIAGNOSTIC TEST HARNESS (8 MODULES)
echo =======================================================================
echo.
venv\Scripts\python.exe test_runner.py

echo.
echo =======================================================================
echo [SUCCESS] Setup and verification complete!
echo You can now double-click "run_app.bat" anytime to launch the assistant.
echo =======================================================================
echo.
pause
