@echo off
setlocal EnableDelayedExpansion
REM Skill Agent Launcher (v3 — Langflow + OpenAI Compat Adapter; Lobe Chat is the desktop exe, started by the user)

REM Ensure window stays open: if not already in /k mode, restart with /k
if not defined LAUNCHER_PERSIST (
    set "LAUNCHER_PERSIST=1"
    cmd /k "%~f0" %*
    exit /b
)

title Skill Agent Launcher (Langflow + Adapter)
cd /d "%~dp0"

set MODE=%1

if "%MODE%"=="" goto show_menu
goto run_mode

:show_menu
cls
echo.
echo ========================================
echo    Skill Agent Launcher (v3.0)
echo    Stack: Langflow + Adapter
echo    (Lobe Chat: launch the desktop exe yourself)
echo ========================================
echo.
echo [1] Full Backend (Langflow + Adapter)
echo [2] Backend Only (alias of [1], kept for backward compat)
echo [4] Stop All Services
echo [0] Exit
echo.
echo ========================================
echo.

ver >nul
set /p CHOICE=Choose [0,1,2,4]:

if errorlevel 1 (
    echo.
    echo [FATAL] No input stream detected. Run this script in a terminal window.
    if "%1"=="" pause
    exit /b 1
)

if "%CHOICE%"=="" (
    echo Invalid option!
    timeout /t 1 >nul
    goto show_menu
)

if "%CHOICE%"=="1" set MODE=full
if "%CHOICE%"=="2" set MODE=backend
if "%CHOICE%"=="4" set MODE=stop
if "%CHOICE%"=="0" exit /b 0

if "%MODE%"=="" (
    echo Invalid option!
    timeout /t 2 >nul
    goto show_menu
)

:run_mode
echo.
echo ========================================

if /i "%MODE%"=="full" goto mode_full
if /i "%MODE%"=="backend" goto mode_backend
if /i "%MODE%"=="stop" goto mode_stop

echo Error: Unknown mode %MODE%
pause
exit /b 1

REM =====================================================================
REM  Mode: Full Backend (Langflow + Adapter). Lobe Chat is the desktop exe.
REM =====================================================================
:mode_full
echo [Mode] Full Backend (Langflow + Adapter)
echo ========================================
call :preflight_checks
if errorlevel 1 goto fatal_exit
call :clean_port 7860
call :clean_port 2024

call :launch_langflow
if errorlevel 1 goto fatal_exit
call :launch_adapter
if errorlevel 1 goto fatal_exit

echo.
echo ========================================
echo Started successfully!
echo.
echo Langflow:        http://localhost:7860
echo OpenAI Adapter:  http://localhost:2024  (health: /health)
echo.
echo Front-end: launch the Lobe Chat desktop app yourself, then in
echo   Settings -> Language Model -> OpenAI -> add a custom provider with:
echo     API Endpoint: http://localhost:2024/v1
echo     API Key:      skill-agent-local   (any non-empty string works)
echo   See README.md § "Lobe Chat 桌面版配置指南" for the full model list.
echo.
echo First-time only: run `python langflow\scripts\upload_flows.py`
echo to upload langflow\flows\*.json into the running Langflow.
echo.
echo Stop: launch.bat stop  (or `[4] Stop All Services` from the menu)
echo ========================================
if "%1"=="" pause
exit /b 0

REM =====================================================================
REM  Mode: Backend Only (alias of Full — historically the same thing now
REM  that Lobe Chat is no longer launched by this script).
REM =====================================================================
:mode_backend
echo [Mode] Backend Only (alias of Full)
echo ========================================
goto mode_full

REM =====================================================================
REM  Mode: Stop All
REM =====================================================================
:mode_stop
echo [Mode] Stop All
echo ========================================
echo [Stop] Langflow native server (window + port 7860)...
taskkill /F /FI "WINDOWTITLE eq Langflow-Backend*" >nul 2>&1
call :stop_port 7860
call :stop_port 2024
echo.
echo Skill Agent backend stopped. Close the Lobe Chat desktop app yourself if running.
if "%1"=="" pause
exit /b 0

REM =====================================================================
REM  Pre-flight checks (Langflow fork submodule, uv toolchain, venv,
REM  API key, embedding model)
REM =====================================================================
:preflight_checks
echo [Check] Pre-flight checks...

if not exist "external\langflow\pyproject.toml" (
    echo [Error] external\langflow submodule not initialised.
    echo Run: git submodule update --init --recursive
    exit /b 1
)

call :require_uv
if errorlevel 1 exit /b 1

call :ensure_venv
if errorlevel 1 exit /b 1
call :ensure_api_key
if errorlevel 1 exit /b 1
call :ensure_embedding_model
if errorlevel 1 exit /b 1

exit /b 0

:require_uv
where uv >nul 2>&1
if errorlevel 1 (
    echo [Error] `uv` is not installed or not on PATH.
    echo Install with one of:
    echo     pip install uv
    echo     winget install astral-sh.uv
    exit /b 1
)
exit /b 0

REM =====================================================================
REM  Service launchers
REM =====================================================================
:launch_langflow
echo [Start] Langflow @7860 (native via uv, no Docker)...
if not exist "%~dp0langflow\scripts\run_local.bat" (
    echo [Error] langflow\scripts\run_local.bat not found.
    exit /b 1
)
start "Langflow-Backend" cmd /k "call "%~dp0langflow\scripts\run_local.bat""
echo [OK] Langflow starting in new window.
echo       First-time `uv sync` inside external\langflow may take 5-10 minutes;
echo       subsequent starts are near-instant.
exit /b 0

:launch_adapter
echo [Start] OpenAI Compat Adapter @2024...
cd /d "%~dp0skill_agent"
if not exist "venv\Scripts\activate.bat" (
    echo [Error] Python venv missing.
    cd /d "%~dp0"
    exit /b 1
)
start "OpenAI Compat Adapter" cmd /k "venv\Scripts\activate.bat && python -m skill_agent.openai_compat.server"
cd /d "%~dp0"
echo [OK] Adapter started in new window.
exit /b 0

REM =====================================================================
REM  Port helpers
REM =====================================================================
:clean_port
set "PORT_NUM=%~1"
echo [Check] Port %PORT_NUM%...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%PORT_NUM%" ^| find "LISTENING"') do (
    echo [Clean] Stopping PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
exit /b 0

:stop_port
set "PORT_NUM=%~1"
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%PORT_NUM%" ^| find "LISTENING"') do (
    echo [Stop] Port %PORT_NUM% (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)
exit /b 0

REM =====================================================================
REM  Python venv & API key & embedding model bootstrap
REM =====================================================================
:ensure_venv
echo [Setup] Checking Python virtual environment...
set "PYTHON_CMD=%PYTHON_CMD%"
if "%PYTHON_CMD%"=="" set "PYTHON_CMD=python"
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=python3"
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo [Error] Python not found. Install Python 3.10+
        exit /b 1
    )
)

cd /d "%~dp0skill_agent"
if not exist "venv\Scripts\activate.bat" (
    echo [Setup] Creating virtual environment with %PYTHON_CMD% ...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo [Error] Failed to create virtual environment
        cd /d "%~dp0"
        exit /b 1
    )
)

set "DEPS_FLAG=venv\.deps_installed"
if not exist "%DEPS_FLAG%" (
    echo [Setup] Installing Python dependencies from requirements.txt ...
    call "venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    if errorlevel 1 (
        echo [Error] Failed to upgrade pip
        cd /d "%~dp0"
        exit /b 1
    )
    call "venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [Error] Failed to install dependencies. Check the log above.
        cd /d "%~dp0"
        exit /b 1
    )
    echo Installed on %DATE% %TIME% >"%DEPS_FLAG%"
)

cd /d "%~dp0"
exit /b 0

:ensure_api_key
echo [Setup] Checking API Key configuration...
set "ENV_FILE=%~dp0skill_agent\.env"

if exist "%ENV_FILE%" (
    findstr /C:"DEEPSEEK_API_KEY=" "%ENV_FILE%" >nul 2>&1
    if not errorlevel 1 (
        findstr /C:"DEEPSEEK_API_KEY=your_api_key_here" "%ENV_FILE%" >nul 2>&1
        if errorlevel 1 (
            for /f "tokens=2 delims==" %%a in ('findstr /C:"DEEPSEEK_API_KEY=" "%ENV_FILE%"') do (
                set "KEY_VALUE=%%a"
            )
            if defined KEY_VALUE (
                if not "!KEY_VALUE!"=="" (
                    echo [OK] DEEPSEEK_API_KEY configured
                    exit /b 0
                )
            )
        )
    )
)

echo.
echo ========================================
echo  First-time Setup: API Key Required
echo ========================================
echo.
echo DEEPSEEK_API_KEY is required for skill generation.
echo Get your API key from: https://platform.deepseek.com/
echo.
set /p "USER_API_KEY=Please enter your DEEPSEEK_API_KEY: "

if "%USER_API_KEY%"=="" (
    echo.
    echo [Error] API Key cannot be empty!
    exit /b 1
)

echo # DeepSeek API Key>"%ENV_FILE%"
echo DEEPSEEK_API_KEY=%USER_API_KEY%>>"%ENV_FILE%"

echo.
echo [OK] API Key saved to skill_agent\.env
echo.
exit /b 0

:ensure_embedding_model
echo [Setup] Checking embedding model (Qwen3-Embedding-0.6B)...
set "MODEL_DIR=%~dp0skill_agent\Data\models\Qwen3-Embedding-0.6B"

if exist "%MODEL_DIR%\model.safetensors" (
    echo [OK] Embedding model found
    exit /b 0
)
if exist "%MODEL_DIR%\pytorch_model.bin" (
    echo [OK] Embedding model found
    exit /b 0
)

echo [Setup] Embedding model not found, downloading from HuggingFace...
cd /d "%~dp0skill_agent"

call "venv\Scripts\python.exe" -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-Embedding-0.6B', local_dir='Data/models/Qwen3-Embedding-0.6B', local_dir_use_symlinks=False, resume_download=True)"
if errorlevel 1 (
    echo [Error] Failed to download embedding model
    echo Manual download: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
    cd /d "%~dp0"
    exit /b 1
)

echo [OK] Embedding model downloaded
cd /d "%~dp0"
exit /b 0

REM =====================================================================
REM  Common error handler
REM  Reached when a preflight check or service launcher returned a
REM  non-zero errorlevel from one of the `goto fatal_exit` jumps in
REM  :mode_full. Prints a clear failure message, pauses so the user
REM  can read the log scrolled above, then exits with errorlevel 1.
REM =====================================================================
:fatal_exit
echo.
echo ========================================
echo [FATAL] Startup aborted.
echo.
echo One of the preflight checks or service launchers above failed.
echo Scroll up to read the [Error] line(s) for the root cause.
echo.
echo Common fixes:
echo   - external\langflow submodule missing
echo       =^> git submodule update --init --recursive
echo   - `uv` not on PATH
echo       =^> pip install uv   (or)   winget install astral-sh.uv
echo   - Python venv / dependencies install failed
echo       =^> delete skill_agent\venv and re-run this script
echo   - DEEPSEEK_API_KEY missing or placeholder
echo       =^> edit skill_agent\.env, set DEEPSEEK_API_KEY=...
echo   - Embedding model download failed
echo       =^> manual: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
echo ========================================
echo.
if "%1"=="" pause
exit /b 1
