@echo off
setlocal EnableExtensions

REM Workspace AI Agent - daily local sync/start script
REM Safe by default: never resets Git, never deletes data, never recreates volumes.

cd /d "%~dp0"

set "PYTHON=python"
set "VENV=.venv"
set "PYTHON_EXE=%VENV%\Scripts\python.exe"
set "PIP_EXE=%VENV%\Scripts\pip.exe"
set "AGENT_HOST=127.0.0.1"
set "AGENT_PORT=8000"
set "AGENT_URL=http://%AGENT_HOST%:%AGENT_PORT%"

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
    echo [WARN] The script will continue with Docker services, but FastAPI may not start correctly.
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

call :step "Showing Docker service status"
docker compose ps

call :step "Checking whether Agent API is already running"
where curl >nul 2>&1
if not errorlevel 1 (
    curl -fsS --max-time 3 "%AGENT_URL%/health" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Agent API is already running at %AGENT_URL%.
        goto :agent_ready
    )
) else (
    echo [INFO] curl not available; using port check only.
)

call :step "Checking whether Agent API port %AGENT_PORT% is already in use"
netstat -ano | findstr /R /C:":%AGENT_PORT% .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [WARN] Port %AGENT_PORT% is already in use by another process.
    echo [WARN] FastAPI was not started to avoid taking over an existing service.
    goto :agent_ready
)

call :step "Starting FastAPI Agent on %AGENT_URL%"
if not exist "app\api\chat.py" (
    echo [ERROR] Expected Agent API source was not found: app\api\chat.py
    goto :fail
)

start "Workspace AI Agent - FastAPI :8000" /MIN cmd /c "cd /d ""%~dp0"" && ""%PYTHON_EXE%"" -m uvicorn app.api.chat:app --host %AGENT_HOST% --port %AGENT_PORT% > ""agent_api.log"" 2>&1"
if errorlevel 1 (
    echo [ERROR] Failed to launch FastAPI process.
    goto :fail
)

echo [INFO] FastAPI process launched. Waiting for health endpoint...

:wait_agent
set /a WAIT_COUNT+=1
if %WAIT_COUNT% GTR 20 goto :agent_timeout

where curl >nul 2>&1
if not errorlevel 1 (
    curl -fsS --max-time 2 "%AGENT_URL%/health" >nul 2>&1
    if not errorlevel 1 goto :agent_started
) else (
    netstat -ano | findstr /R /C:":%AGENT_PORT% .*LISTENING" >nul 2>&1
    if not errorlevel 1 goto :agent_started
)

timeout /t 1 /nobreak >nul
goto :wait_agent

:agent_started
echo [OK] FastAPI Agent is running at %AGENT_URL%.
goto :agent_ready

:agent_timeout
echo [WARN] FastAPI process was launched, but readiness was not confirmed within 20 seconds.
echo [INFO] Check agent_api.log for the startup error if the API is unavailable.

goto :agent_ready

:agent_ready
call :step "Final Agent API smoke check"
where curl >nul 2>&1
if not errorlevel 1 (
    curl -fsS --max-time 5 "%AGENT_URL%/health" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Agent API health endpoint responded.
    ) else (
        echo [WARN] Agent API health endpoint did not respond.
        echo [INFO] Check agent_api.log.
    )
) else (
    netstat -ano | findstr /R /C:":%AGENT_PORT% .*LISTENING" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Agent API port %AGENT_PORT% is listening.
    ) else (
        echo [WARN] Agent API port %AGENT_PORT% is not listening.
    )
)

call :step "Final Git status"
git status --short

echo.
echo ============================================================
echo Workspace AI Agent daily sync completed.
echo PostgreSQL : 127.0.0.1:5433
echo Qdrant     : 127.0.0.1:6333
echo Agent API  : %AGENT_URL%
echo Agent log  : %~dp0agent_api.log
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
