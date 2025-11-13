@echo off
REM skill_agent WebUI 启动脚本（Windows）
chcp 65001 >nul

echo 🚀 启动 skill_agent 技能分析系统...
echo.

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set SKILLRAG_DIR=%SCRIPT_DIR%
set WEBUI_DIR=%SCRIPT_DIR%..\webui

echo 📁 skill_agent 目录: %SKILLRAG_DIR%
echo 📁 WebUI 目录: %WEBUI_DIR%
echo.

REM 1. 启动 LangGraph 服务器
echo 1️⃣ 启动 LangGraph 服务器...
cd /d "%SKILLRAG_DIR%"

REM 检查虚拟环境
if not exist "venv" (
    echo ⚠️  未找到虚拟环境，正在创建...
    python -m venv venv
)

call venv\Scripts\activate.bat

REM 安装依赖
echo 📦 安装 Python 依赖...
pip install -q -r requirements_langchain.txt

REM 启动 LangGraph 服务器
echo 🔧 启动 LangGraph 服务器 (端口 2024)...
start "LangGraph Server" /B python langgraph_server.py > langgraph_server.log 2>&1
echo ✅ LangGraph 服务器已启动
echo.

REM 等待服务器启动
timeout /t 3 /nobreak >nul

REM 2. 配置并启动 WebUI
echo 2️⃣ 配置并启动 WebUI...
cd /d "%WEBUI_DIR%"

REM 检查 .env 文件
if not exist ".env" (
    echo ⚠️  未找到 .env 文件，正在创建...
    copy "%SKILLRAG_DIR%webui.env" .env
    echo ✅ 已创建 .env 文件
)

REM 安装依赖
if not exist "node_modules" (
    echo 📦 安装 Node.js 依赖...
    call npm install
)

REM 启动 WebUI
echo 🌐 启动 WebUI (端口 3000)...
start "WebUI" /B npm run dev
echo ✅ WebUI 已启动
echo.

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo ✨ skill_agent 技能分析系统已启动！
echo.
echo 📊 LangGraph 服务器: http://localhost:2024
echo 🌐 WebUI 界面: http://localhost:3000
echo.
echo 📝 日志文件: %SKILLRAG_DIR%langgraph_server.log
echo.
echo ⏹️  停止服务: stop_webui.bat
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM 等待WebUI启动
echo 等待 WebUI 启动完成...
timeout /t 8 /nobreak >nul

REM 自动打开浏览器
echo 🌐 正在打开浏览器...
start http://localhost:3000/rag
echo.

echo 按任意键退出（服务将继续在后台运行）...
pause >nul
