@echo off
title OfflineDarts
echo ============================================================
echo   OfflineDarts — Offline Automatic Dart Scoring
echo ============================================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check/create virtual environment
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.

:: Run the application
echo Starting OfflineDarts...
echo ============================================================
python main.py

:: Deactivate on exit
deactivate
