@echo off
REM Skill Agent Launcher - English version to avoid encoding issues
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

set /p CHOICE=Choose [0-6]:

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
echo [Check] Port %1...
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%1" ^| find "LISTENING"') do (
    echo [Clean] Stopping PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)
exit /b 0

:stop_port
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%1" ^| find "LISTENING"') do (
    echo [Stop] Port %1 (PID: %%a)
    taskkill /F /PID %%a >nul 2>&1
)
exit /b 0

:launch_server
echo [Start] LangGraph Server (port 2024)...
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
        start "WebUI" cmd /k "set NEXT_PUBLIC_API_URL=%NEXT_PUBLIC_API_URL% && npm run dev"
    )
) else (
    start "WebUI" cmd /k "set NEXT_PUBLIC_API_URL=%NEXT_PUBLIC_API_URL% && pnpm run dev"
)

cd /d "%~dp0"
echo [OK] WebUI started in new window
exit /b 0
