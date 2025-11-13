@echo off
REM skill_agent WebUI Startup Script (Real-time Logs Version)
chcp 65001 >nul

echo.
echo ============================================================
echo    skill_agent System - Real-time Logs Launcher
echo ============================================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
set SKILLRAG_DIR=%SCRIPT_DIR%
set WEBUI_DIR=%SCRIPT_DIR%..\webui

echo Directory: %SKILLRAG_DIR%
echo WebUI: %WEBUI_DIR%
echo.
echo ============================================================
echo.

REM ============================================
REM Step 1: Prepare Python Environment
REM ============================================
echo [1/5] Preparing Python environment...
cd /d "%SKILLRAG_DIR%"

REM Check virtual environment
if not exist "venv" (
    echo    Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo    ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo    Virtual environment created
) else (
    echo    Virtual environment exists
)

echo.
echo [2/5] Installing Python dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip first
python -m pip install --upgrade pip -q

REM Install all dependencies from requirements.txt
pip install -q -r requirements.txt
if errorlevel 1 (
    echo    ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo    Python dependencies installed
echo.
echo ============================================================
echo.

REM ============================================
REM Step 2.5: Check and Download Embedding Model
REM ============================================
echo [2.5/5] Checking Qwen3 embedding model...
echo.

REM Run model check script with auto-download flag
python check_and_download_model.py --auto
if errorlevel 1 (
    echo.
    echo    ERROR: Model check failed
    echo    Please ensure the model is downloaded correctly
    pause
    exit /b 1
)

echo.
echo ============================================================
echo.

REM ============================================
REM Step 3: Start LangGraph Server
REM ============================================
echo [3/5] Starting LangGraph Server (Port 2024)...
echo.
echo    LangGraph Server will start in a new window
echo    Logs will be displayed in real-time
echo.

REM Start LangGraph server in new window
start "LangGraph Server - http://localhost:2024" cmd /k "cd /d "%SKILLRAG_DIR%" && call venv\Scripts\activate.bat && python langgraph_server.py"

echo    Waiting for LangGraph Server to start...
echo    (This may take 5-10 seconds for first-time initialization)
echo.

REM Initial wait for server startup
timeout /t 3 /nobreak >nul

REM Health check
set MAX_RETRIES=20
set RETRY_COUNT=0

:CHECK_LANGGRAPH
set /a RETRY_COUNT+=1

REM Show progress dots
set /p "=." <nul

if %RETRY_COUNT% gtr %MAX_RETRIES% (
    echo.
    echo    ERROR: LangGraph Server startup timeout
    echo    Please check the LangGraph Server window for errors
    pause
    exit /b 1
)

REM Use PowerShell for health check
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:2024/health' -UseBasicParsing -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto CHECK_LANGGRAPH
)

echo.

echo    LangGraph Server started successfully
echo    API Docs: http://localhost:2024/docs
echo.
echo ============================================================
echo.

REM ============================================
REM Step 3: Prepare WebUI Environment
REM ============================================
echo [4/5] Preparing WebUI environment...
cd /d "%WEBUI_DIR%"

REM Check .env file
if not exist ".env" (
    echo    Creating .env file...
    copy "%SKILLRAG_DIR%webui.env" .env >nul
    if errorlevel 1 (
        echo    ERROR: Failed to create .env file
        pause
        exit /b 1
    )
    echo    .env file created
) else (
    echo    .env file exists
)

REM Check node_modules
if not exist "node_modules" (
    echo.
    echo    Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo    ERROR: Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    echo    Node.js dependencies installed
) else (
    echo    Node.js dependencies installed
)
echo.
echo ============================================================
echo.

REM ============================================
REM Step 4: Start WebUI
REM ============================================
echo [5/5] Starting WebUI (Port 3000)...
echo.

REM Clean up port 3000 if occupied
echo    Checking port 3000...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do (
    echo    Port 3000 occupied by PID %%a, cleaning up...
    taskkill /F /PID %%a >nul 2>&1
    timeout /t 1 /nobreak >nul
)
echo    Port 3000 ready
echo.

echo    WebUI Dev Server will start in a new window
echo    Next.js logs will be displayed in real-time
echo.

REM Start WebUI in new window
start "WebUI Dev Server - http://localhost:3000" cmd /k "cd /d "%WEBUI_DIR%" && npm run dev"

echo    Waiting for WebUI to start...
echo    (Next.js compilation may take 10-30 seconds)
echo.

REM Initial wait for WebUI startup
timeout /t 5 /nobreak >nul

REM Wait for WebUI
set WEBUI_RETRIES=0
:CHECK_WEBUI
set /a WEBUI_RETRIES+=1

REM Show progress dots
set /p "=." <nul

if %WEBUI_RETRIES% gtr 30 (
    echo.
    echo    WebUI is starting (check WebUI window for progress)
    goto WEBUI_STARTED
)

powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1

if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto CHECK_WEBUI
)

echo.
echo    WebUI started successfully
:WEBUI_STARTED
echo.
echo ============================================================
echo.

REM ============================================
REM Startup Complete
REM ============================================
echo.
echo ============================================================
echo                System Started Successfully
echo ============================================================
echo.
echo Access URLs:
echo    LangGraph API:  http://localhost:2024
echo    API Docs:       http://localhost:2024/docs
echo    WebUI Home:     http://localhost:3000
echo    RAG Query:      http://localhost:3000/rag
echo.
echo Real-time Log Windows:
echo    * LangGraph Server - Backend API logs
echo    * WebUI Dev Server - Frontend compilation logs
echo.
echo Usage Tips:
echo    - Three windows are running (Main Console + 2 Log Windows)
echo    - View real-time logs in service windows
echo    - Close service windows to stop services
echo.
echo Stop Services:
echo    Method 1: Run stop_webui.bat (Recommended)
echo    Method 2: Close all service windows
echo.
echo ============================================================
echo.

REM Auto-open browser
echo Opening browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000
echo.

REM Main console menu
echo ============================================================
echo           System Running - Main Console
echo ============================================================
echo.
echo This window monitors system status
echo View real-time logs in service windows
echo.
echo ============================================================
echo.
echo Quick Actions:
echo    [1] Open LangGraph API Docs
echo    [2] Open RAG Query Page
echo    [3] Check Service Health
echo    [Q] Exit (Services continue running)
echo    [S] Stop all services and exit
echo.

:MENU_LOOP
set /p CHOICE="Select option [1/2/3/Q/S]: "

if /i "%CHOICE%"=="1" (
    start http://localhost:2024/docs
    echo API Docs opened
    echo.
    goto MENU_LOOP
)

if /i "%CHOICE%"=="2" (
    start http://localhost:3000/rag
    echo RAG Query page opened
    echo.
    goto MENU_LOOP
)

if /i "%CHOICE%"=="3" (
    echo.
    echo Checking service health...
    echo.

    echo [LangGraph Server]
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:2024/health' -UseBasicParsing -TimeoutSec 2; Write-Host '   Status: Running' -ForegroundColor Green } catch { Write-Host '   Status: Not responding' -ForegroundColor Red }"

    echo.
    echo [WebUI Dev Server]
    powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 2; Write-Host '   Status: Running' -ForegroundColor Green } catch { Write-Host '   Status: Not responding' -ForegroundColor Red }"

    echo.
    goto MENU_LOOP
)

if /i "%CHOICE%"=="Q" (
    echo.
    echo Main console exited, services continue running
    echo Use stop_webui.bat to stop all services
    echo.
    timeout /t 2 /nobreak >nul
    exit /b 0
)

if /i "%CHOICE%"=="S" (
    echo.
    echo Stopping all services...
    call "%SKILLRAG_DIR%stop_webui.bat"
    echo.
    echo All services stopped
    timeout /t 2 /nobreak >nul
    exit /b 0
)

echo Invalid option, please try again
echo.
goto MENU_LOOP
