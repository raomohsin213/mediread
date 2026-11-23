@echo off
setlocal enabledelayedexpansion
title AI Medicine Assistant Launcher
color 0b

echo =======================================================================
echo          AI MEDICINE ASSISTANT - ONE-CLICK AUTO-SETUP ^& LAUNCHER
echo              (Bilingual: Urdu Default with English Toggle)
echo =======================================================================
echo.

:: 1. Detect Python (try 'python' then 'py')
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
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo.
    echo Please install Python 3.9, 3.10, or 3.11 from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Make sure to check the box "Add python.exe to PATH" during installation!
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PY_CMD% --version 2^>^&1') do echo [FOUND] System %%v

:: 2. Check or create Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo.
    echo [INFO] First-time setup detected: Creating Python virtual environment...
    echo [INFO] Creating "venv" folder...
    %PY_CMD% -m venv venv
    if !errorlevel! neq 0 (
        color 0c
        echo [ERROR] Failed to create virtual environment with %PY_CMD%.
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created successfully.
)

:: 3. Verify and install libraries if missing
set "NEED_INSTALL=0"
if not exist "venv\.installed" (
    set "NEED_INSTALL=1"
) else (
    venv\Scripts\python.exe -c "import cv2, ultralytics, easyocr, PIL, bs4, requests, pygame, piper" >nul 2>&1
    if !errorlevel! neq 0 (
        set "NEED_INSTALL=1"
    )
)

if "%NEED_INSTALL%"=="1" (
    echo.
    echo =======================================================================
    echo   [FIRST-TIME SETUP] Installing required AI and vision libraries...
    echo   This is a one-time process and may take 2-4 minutes. Please wait...
    echo =======================================================================
    echo.
    echo [1/3] Upgrading pip, setuptools, and wheel...
    venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel --quiet

    echo [2/3] Installing all required dependencies from requirements.txt...
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        color 0c
        echo.
        echo [ERROR] An error occurred while installing packages.
        echo Please ensure you have an active internet connection and try running again.
        pause
        exit /b 1
    )

    echo [3/3] Verifying library integrity...
    venv\Scripts\python.exe -c "import cv2, ultralytics, easyocr, PIL, bs4, requests, pygame, piper; print('[SUCCESS] Core packages verified.')"
    if !errorlevel! equ 0 (
        echo Successfully installed on %date% %time% > "venv\.installed"
        echo [SUCCESS] All libraries installed and verified!
    ) else (
        echo [WARNING] Verification finished with non-critical warnings.
    )
    echo.
)

:: 4. Launch the application
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Launching AI Medicine Assistant...
echo.
python main.py

if !errorlevel! neq 0 (
    echo.
    echo [NOTE] Application closed.
    pause
)
