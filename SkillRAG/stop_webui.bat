@echo off
REM SkillRAG WebUI 停止脚本（Windows）
chcp 65001 >nul

echo ⏹️  停止 SkillRAG 技能分析系统...
echo.

REM 停止 LangGraph 服务器（通过端口）
echo 🛑 停止 LangGraph 服务器...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":2024" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ LangGraph 服务器已停止 (PID: %%a)
    )
)

REM 停止 WebUI（通过端口）
echo 🛑 停止 WebUI...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ WebUI 已停止 (PID: %%a)
    )
)

REM 停止所有 node 进程（可选，如果上面的方法不起作用）
REM taskkill /F /IM node.exe >nul 2>&1

REM 停止所有 python 进程（可选，如果上面的方法不起作用）
REM taskkill /F /IM python.exe >nul 2>&1

echo.
echo ✅ 所有服务已停止
pause
