@echo off
REM 重启 LangGraph 服务器的辅助脚本
chcp 65001 >nul

echo ============================================================
echo   LangGraph Server - Quick Restart
echo ============================================================
echo.

REM 检查端口占用
for /f "tokens=5" %%a in ('netstat -ano ^| find ":2024" ^| find "LISTENING"') do (
    echo [1/2] 发现运行中的服务 (PID: %%a^)
    echo       正在停止...
    taskkill /F /PID %%a >nul 2>&1
    echo       ✓ 已停止
    timeout /t 2 /nobreak >nul
    goto START_SERVER
)

echo [1/2] 端口 2024 未被占用

:START_SERVER
echo.
echo [2/2] 启动 LangGraph 服务器...
echo.
cd /d "%~dp0"
call venv\Scripts\activate.bat
python langgraph_server.py

pause
