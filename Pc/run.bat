@echo off
title Haven AI Server
cd /d "%~dp0"
echo Starting Haven AI in virtual environment...
call venv\Scripts\activate.bat
python main.py
if errorlevel 1 (
    echo.
    echo Server stopped with error.
    pause
)
