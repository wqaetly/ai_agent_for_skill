@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

REM ========================================
REM   Skill Agent - 统一停止脚本
REM ========================================

echo.
echo ========================================
echo   停止 Skill Agent 所有服务
echo ========================================
echo.

REM 停止 LangGraph Server (端口 2024)
call :stop_service 2024 "LangGraph Server"

REM 停止 LangGraph Dev Server (端口 8123)
call :stop_service 8123 "LangGraph Dev Server"

REM 停止 WebUI (端口 3000, 3001)
call :stop_service 3000 "WebUI"
call :stop_service 3001 "WebUI Dev"

REM 可选：清理特定进程名（更彻底的清理）
REM call :stop_process "node.exe" "Node.js"
REM call :stop_process "python.exe" "Python"

echo.
echo ========================================
echo 所有服务已停止
echo ========================================
echo.

pause
exit /b 0

REM ========================================
REM 函数：按端口停止服务
REM ========================================
:stop_service
set PORT=%1
set SERVICE_NAME=%~2
set FOUND=0

for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| find ":%PORT%" ^| find "LISTENING"') do (
    set FOUND=1
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo [停止] %SERVICE_NAME% (端口 %PORT%, PID: %%a)
    ) else (
        echo [失败] 无法停止 %SERVICE_NAME% (PID: %%a)
    )
)

if !FOUND! equ 0 (
    echo [跳过] %SERVICE_NAME% (端口 %PORT% 未使用)
)

exit /b 0

REM ========================================
REM 函数：按进程名停止服务
REM ========================================
:stop_process
set PROCESS_NAME=%~1
set SERVICE_NAME=%~2

tasklist | find /i "%PROCESS_NAME%" >nul 2>&1
if !errorlevel! equ 0 (
    echo [停止] %SERVICE_NAME% (进程: %PROCESS_NAME%)
    taskkill /F /IM "%PROCESS_NAME%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [成功] %SERVICE_NAME% 已停止
    ) else (
        echo [失败] 无法停止 %SERVICE_NAME%
    )
) else (
    echo [跳过] %SERVICE_NAME% (进程未运行)
)

exit /b 0
