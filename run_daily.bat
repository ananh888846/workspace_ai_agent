@echo off
setlocal EnableExtensions

REM Workspace AI Agent - daily local sync/start script
REM Safe by default: never resets Git, never deletes data, never recreates volumes.

cd /d "%~dp0"

set "PYTHON=python"
set "VENV=.venv"
set "PYTHON_EXE=%VENV%\Scripts\python.exe"
set "PIP_EXE=%VENV%\Scripts\pip.exe"

call :step "Checking Git working tree"
git status --short
if errorlevel 1 goto :fail

call :step "Updating repository from origin/main"
git fetch origin main
if errorlevel 1 goto :fail

git pull --ff-only origin main
if errorlevel 1 goto :fail

if not exist ".env" (
    echo [WARN] .env does not exist. Create it from .env.example before starting the Agent.
    echo [WARN] The script will continue with Docker services only.
) else (
    echo [OK] .env found.
)

call :step "Checking Python"
%PYTHON% --version
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH.
    goto :fail
)

if not exist "%PYTHON_EXE%" (
    call :step "Creating Python virtual environment"
    %PYTHON% -m venv "%VENV%"
    if errorlevel 1 goto :fail
)

call :step "Updating Python dependencies"
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

call :step "Starting PostgreSQL and Qdrant"
docker compose up -d
if errorlevel 1 goto :fail

call :step "Showing service status"
docker compose ps

call :step "Running Agent API smoke check"
where curl >nul 2>&1
if not errorlevel 1 (
    curl -fsS --max-time 5 http://127.0.0.1:8000/health >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Agent API is not responding on http://127.0.0.1:8000/health.
        echo [INFO] Start the FastAPI application separately if it is not already running.
    ) else (
        echo [OK] Agent API health endpoint responded.
    )
) else (
    echo [INFO] curl not available; skipped HTTP smoke check.
)

call :step "Final Git status"
git status --short

echo.
echo ============================================================
echo Workspace AI Agent daily sync completed.
echo PostgreSQL : 127.0.0.1:5433
echo Qdrant     : 127.0.0.1:6333
 echo Agent API  : 127.0.0.1:8000
echo ============================================================
exit /b 0

:step
echo.
echo [STEP] %~1
exit /b 0

:fail
echo.
echo [ERROR] Daily sync stopped because a required step failed.
echo [INFO] No Git reset/force operation or Docker volume deletion was performed.
exit /b 1
