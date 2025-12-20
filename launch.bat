@echo off
setlocal EnableDelayedExpansion
REM Skill Agent Launcher - English version to avoid encoding issues

REM Ensure window stays open: if not already in /k mode, restart with /k
if not defined LAUNCHER_PERSIST (
    set "LAUNCHER_PERSIST=1"
    cmd /k "%~f0" %*
    exit /b
)

title Skill Agent Launcher
cd /d "%~dp0"

set MODE=%1

if "%MODE%"=="" goto show_menu
goto run_mode

:show_menu
cls
echo.
echo ========================================
echo    Skill Agent Launcher
echo ========================================
echo.
echo [1] Full System (Server + WebUI)
echo [2] Development Mode (Dev Server + WebUI)
echo [3] Backend Only (Production Server)
echo [4] Backend Only (Dev Server)
echo [5] Frontend Only (WebUI)
echo [6] Stop All Services
echo [0] Exit
echo.
echo ========================================
echo.

ver >nul
set /p CHOICE=Choose [0-6]:

if errorlevel 1 (
    echo.
    echo [FATAL] No input stream detected. Please run this script in a terminal window.
    if "%1"=="" pause
    exit /b 1
)

if "%CHOICE%"=="" (
    echo Invalid option!
    timeout /t 1 >nul
    goto show_menu
)

if "%CHOICE%"=="1" set MODE=full
if "%CHOICE%"=="2" set MODE=dev
if "%CHOICE%"=="3" set MODE=server
if "%CHOICE%"=="4" set MODE=devserver
if "%CHOICE%"=="5" set MODE=webui
if "%CHOICE%"=="6" set MODE=stop
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
if /i "%MODE%"=="dev" goto mode_dev
if /i "%MODE%"=="server" goto mode_server
if /i "%MODE%"=="devserver" goto mode_devserver
if /i "%MODE%"=="webui" goto mode_webui
if /i "%MODE%"=="stop" goto mode_stop

echo Error: Unknown mode %MODE%
pause
exit /b 1

:mode_full
echo [Mode] Full System (Production)
echo ========================================
call :clean_port 2024
call :clean_port 3000
call :launch_server
if errorlevel 1 (
    echo.
    echo ========================================
    echo [FAILED] Backend failed to start. WebUI will NOT be started.
    echo ========================================
    if "%1"=="" pause
    exit /b 1
)
timeout /t 3 /nobreak >nul
call :launch_webui
goto done_full

:done_full
echo.
echo ========================================
echo Started successfully!
echo.
echo Server: http://localhost:2024
echo WebUI: http://localhost:3000
echo API Docs: http://localhost:2024/docs
echo.
echo Stop: launch.bat stop or stop_all.bat
echo ========================================
if "%1"=="" pause
exit /b 0

:mode_dev
echo [Mode] Development
echo ========================================
call :clean_port 8123
call :clean_port 3000
call :launch_devserver
if errorlevel 1 (
    echo.
    echo ========================================
    echo [FAILED] Dev backend failed to start. WebUI will NOT be started.
    echo ========================================
    if "%1"=="" pause
    exit /b 1
)
timeout /t 5 /nobreak >nul
call :launch_webui_dev
goto done_dev

:done_dev
echo.
echo ========================================
echo Started successfully!
echo.
echo Dev Server: http://localhost:8123
echo WebUI: http://localhost:3000
echo API Docs: http://localhost:8123/docs
echo Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123
echo.
echo Stop: launch.bat stop or stop_all.bat
echo ========================================
if "%1"=="" pause
exit /b 0

:mode_server
echo [Mode] Backend Only (Production)
echo ========================================
call :clean_port 2024
call :launch_server
if errorlevel 1 (
    echo.
    echo ========================================
    echo [FAILED] Backend failed to start.
    echo ========================================
    if "%1"=="" pause
    exit /b 1
)
goto done_server

:done_server
echo.
echo ========================================
echo Started successfully!
echo.
echo Server: http://localhost:2024
echo API Docs: http://localhost:2024/docs
echo.
echo Stop: launch.bat stop or stop_all.bat
echo ========================================
if "%1"=="" pause
exit /b 0

:mode_devserver
echo [Mode] Backend Only (Development)
echo ========================================
call :clean_port 8123
call :launch_devserver
if errorlevel 1 (
    echo.
    echo ========================================
    echo [FAILED] Dev backend failed to start.
    echo ========================================
    if "%1"=="" pause
    exit /b 1
)
goto done_devserver

:done_devserver
echo.
echo ========================================
echo Started successfully!
echo.
echo Dev Server: http://localhost:8123
echo API Docs: http://localhost:8123/docs
echo Studio: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8123
echo.
echo Stop: launch.bat stop or stop_all.bat
echo ========================================
if "%1"=="" pause
exit /b 0

:mode_webui
echo [Mode] Frontend Only
echo ========================================
call :clean_port 3000
call :launch_webui
goto done_webui

:done_webui
echo.
echo ========================================
echo Started successfully!
echo.
echo WebUI: http://localhost:3000
echo.
echo Note: Backend service must be running
echo.
echo Stop: launch.bat stop or stop_all.bat
echo ========================================
if "%1"=="" pause
exit /b 0

:mode_stop
echo [Mode] Stop All Services
echo ========================================
call :stop_port 2024
call :stop_port 8123
call :stop_port 3000
call :stop_port 3001
echo.
echo All services stopped
if "%1"=="" pause
exit /b 0

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

:ensure_venv
echo [Setup] Checking Python virtual environment...
set "PYTHON_CMD=%PYTHON_CMD%"
if "%PYTHON_CMD%"=="" set "PYTHON_CMD=python"
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    set "PYTHON_CMD=python3"
    %PYTHON_CMD% --version >nul 2>&1
    if errorlevel 1 (
        echo [Error] Python not found. Please install Python 3.10+
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

set "REQUIREMENTS_FILE=requirements.txt"
if exist "requirements_langchain.txt" set "REQUIREMENTS_FILE=requirements_langchain.txt"
set "DEPS_FLAG=venv\.deps_installed"

if not exist "%DEPS_FLAG%" (
    echo [Setup] Installing Python dependencies from %REQUIREMENTS_FILE% ...
    call "venv\Scripts\python.exe" -m pip install --upgrade pip >nul
    if errorlevel 1 (
        echo [Error] Failed to upgrade pip inside venv
        cd /d "%~dp0"
        exit /b 1
    )
    call "venv\Scripts\python.exe" -m pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 (
        echo [Error] Failed to install dependencies. Check the log above.
        cd /d "%~dp0"
        exit /b 1
    )
    echo Installed on %DATE% %TIME% using %REQUIREMENTS_FILE% >"%DEPS_FLAG%"
)

cd /d "%~dp0"
exit /b 0

:ensure_api_key
echo [Setup] Checking API Key configuration...
set "ENV_FILE=%~dp0skill_agent\.env"

REM Check if .env file exists and contains DEEPSEEK_API_KEY
if exist "%ENV_FILE%" (
    findstr /C:"DEEPSEEK_API_KEY=" "%ENV_FILE%" >nul 2>&1
    if not errorlevel 1 (
        REM Check if it's not the placeholder value
        findstr /C:"DEEPSEEK_API_KEY=your_api_key_here" "%ENV_FILE%" >nul 2>&1
        if errorlevel 1 (
            REM Key exists and is not placeholder
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

REM API Key not configured, prompt user
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
    echo Please get your key from https://platform.deepseek.com/
    exit /b 1
)

REM Create or update .env file
echo # DeepSeek API Key>"%ENV_FILE%"
echo DEEPSEEK_API_KEY=%USER_API_KEY%>>"%ENV_FILE%"
echo.>>"%ENV_FILE%"
echo # PostgreSQL connection (optional, defaults to localhost)>>"%ENV_FILE%"
echo # POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/skill_agent?sslmode=disable>>"%ENV_FILE%"

echo.
echo [OK] API Key saved to skill_agent\.env
echo.
exit /b 0

:ensure_embedding_model
echo [Setup] Checking embedding model (Qwen3-Embedding-0.6B)...
set "MODEL_DIR=%~dp0skill_agent\Data\models\Qwen3-Embedding-0.6B"

REM Check if model weights exist
if exist "%MODEL_DIR%\model.safetensors" (
    echo [OK] Embedding model found
    exit /b 0
)
if exist "%MODEL_DIR%\pytorch_model.bin" (
    echo [OK] Embedding model found
    exit /b 0
)

REM Model not found, download it
echo [Setup] Embedding model not found, downloading from HuggingFace...
cd /d "%~dp0skill_agent"

call "venv\Scripts\python.exe" -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-Embedding-0.6B', local_dir='Data/models/Qwen3-Embedding-0.6B', local_dir_use_symlinks=False, resume_download=True)"
if errorlevel 1 (
    echo [Error] Failed to download embedding model
    echo Please manually download from: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
    cd /d "%~dp0"
    exit /b 1
)

echo [OK] Embedding model downloaded successfully
cd /d "%~dp0"
exit /b 0

:ensure_pgvector
echo [Setup] Checking pgvector Postgres (localhost:5432)...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [FATAL] Docker not found.
    echo.
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop/
    echo After installation, restart your terminal and rerun this script.
    exit /b 1
)

set "PGVECTOR_COMPOSE=%~dp0skill_agent\docker-compose.pgvector.yml"
if not exist "%PGVECTOR_COMPOSE%" (
    echo [FATAL] Missing compose file: %PGVECTOR_COMPOSE%
    exit /b 1
)

echo [Setup] Starting pgvector Postgres container...
docker compose -f "%PGVECTOR_COMPOSE%" up -d
if errorlevel 1 (
    echo [FATAL] Failed to start pgvector Postgres. Please ensure Docker Desktop is running.
    exit /b 1
)

echo [OK] Postgres(pgvector) started
exit /b 0

:launch_server
echo [Start] LangGraph Server (port 2024)...
call :ensure_pgvector
if errorlevel 1 (
    echo.
    echo [ABORT] Backend start canceled due to pgvector Postgres failure.
    cd /d "%~dp0"
    if "%1"=="" pause
    exit /b 1
)
call :ensure_venv
if errorlevel 1 (
    pause
    exit /b 1
)
call :ensure_api_key
if errorlevel 1 (
    pause
    exit /b 1
)
call :ensure_embedding_model
if errorlevel 1 (
    pause
    exit /b 1
)
cd /d "%~dp0skill_agent"
if not exist "venv\Scripts\activate.bat" (
    echo [Error] Virtual environment not found
    pause
    exit /b 1
)
start "LangGraph Server" cmd /k "venv\Scripts\activate.bat && python langgraph_server.py"
cd /d "%~dp0"
echo [OK] Server started in new window
exit /b 0

:launch_devserver
echo [Start] LangGraph Dev Server (port 8123)...
call :ensure_pgvector
if errorlevel 1 (
    echo.
    echo [ABORT] Dev backend start canceled due to pgvector Postgres failure.
    cd /d "%~dp0"
    if "%1"=="" pause
    exit /b 1
)
call :ensure_venv
if errorlevel 1 (
    pause
    exit /b 1
)
call :ensure_api_key
if errorlevel 1 (
    pause
    exit /b 1
)
call :ensure_embedding_model
if errorlevel 1 (
    pause
    exit /b 1
)
cd /d "%~dp0skill_agent"
if not exist "venv\Scripts\activate.bat" (
    echo [Error] Virtual environment not found
    pause
    exit /b 1
)
start "LangGraph Dev" cmd /k "venv\Scripts\activate.bat && langgraph dev --port 8123"
cd /d "%~dp0"
echo [OK] Dev Server started in new window
exit /b 0

:launch_webui
echo [Start] WebUI (port 3000) - connecting to port 2024...
cd /d "%~dp0webui"
call :start_webui_process
exit /b 0

:launch_webui_dev
echo [Start] WebUI (port 3000) - connecting to port 8123...
cd /d "%~dp0webui"

REM Temporarily set API URL for dev mode
set NEXT_PUBLIC_API_URL=http://localhost:8123

call :start_webui_process
exit /b 0

:start_webui_process
REM Check for pnpm or npm by trying to run them
pnpm --version >nul 2>&1
if errorlevel 1 (
    REM pnpm not found, try npm
    npm --version >nul 2>&1
    if errorlevel 1 (
        echo [Error] Neither pnpm nor npm found
        echo Please install Node.js first
        cd /d "%~dp0"
        pause
        exit /b 1
    ) else (
        REM npm found, check if node_modules exists
        if not exist "node_modules" (
            echo [Setup] Installing WebUI dependencies with npm...
            npm install
            if errorlevel 1 (
                echo [Error] Failed to install WebUI dependencies
                cd /d "%~dp0"
                pause
                exit /b 1
            )
        )
        start "WebUI" cmd /k "set NEXT_PUBLIC_API_URL=%NEXT_PUBLIC_API_URL% && npm run dev"
    )
) else (
    REM pnpm found, check if node_modules exists
    if not exist "node_modules" (
        echo [Setup] Installing WebUI dependencies with pnpm...
        pnpm install
        if errorlevel 1 (
            echo [Error] Failed to install WebUI dependencies
            cd /d "%~dp0"
            pause
            exit /b 1
        )
    )
    start "WebUI" cmd /k "set NEXT_PUBLIC_API_URL=%NEXT_PUBLIC_API_URL% && pnpm run dev"
)

cd /d "%~dp0"
echo [OK] WebUI started in new window
exit /b 0
