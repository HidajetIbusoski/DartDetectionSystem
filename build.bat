@echo off
title OfflineDarts — Build
echo ============================================================
echo   OfflineDarts — Build Standalone Executable
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

:: Run build script
echo Starting build process...
echo ============================================================
python build.py

:: Deactivate on exit
deactivate
pause
