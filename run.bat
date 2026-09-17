@echo off
title Nexus-AI Platform Launcher
cd /d "%~dp0"
echo ==========================================================
echo        NEXUS-AI: Autonomous Multimodal Platform
echo ==========================================================
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ from python.org
    pause
    exit /b
)

echo Starting Nexus-AI server...
python run.py
pause
