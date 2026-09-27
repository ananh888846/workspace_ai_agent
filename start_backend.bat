@echo off
title Workspace AI Agent - Backend
cd /d "%~dp0"

echo ==========================================
echo   Workspace AI Agent - Backend
echo ==========================================
echo.
echo Python:
.venv\Scripts\python.exe --version
echo.
echo Starting Agent API on http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo Backend stopped.
pause
