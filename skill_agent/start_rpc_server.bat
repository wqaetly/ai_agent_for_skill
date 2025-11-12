@echo off
REM Unity RPC Server 启动脚本 (Windows)
REM 用于Unity与Python的双向通信

echo ========================================
echo Unity RPC Server Launcher
echo ========================================
echo.

REM 切换到脚本所在目�?cd /d "%~dp0"

REM 检查Python是否可用
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Python未安装或未添加到PATH
    echo 请先安装Python 3.8+并添加到系统PATH
    pause
    exit /b 1
)

echo [信息] Python环境检查通过
echo.

REM 检�?env文件（可选）
if not exist ".env" (
    echo [警告] 未找�?env文件
    echo 如需配置环境变量，请复制.env.example�?env
    echo.
)

REM 设置环境变量（可选）
if exist ".env" (
    echo [信息] 加载环境变量...
    REM Windows下需要手动设置，或使用python-dotenv
    echo 提示：确保已在系统环境变量中配置DEEPSEEK_API_KEY
    echo.
)

REM 设置默认端口
set RPC_PORT=8766
if defined UNITY_RPC_PORT (
    set RPC_PORT=%UNITY_RPC_PORT%
)

echo [信息] 启动Unity RPC服务�?..
echo [信息] 监听端口: %RPC_PORT%
echo [信息] 按Ctrl+C停止服务�?echo ========================================
echo.

REM 启动RPC服务�?cd Python
python start_unity_rpc.py

REM 捕获退出码
if %errorlevel% neq 0 (
    echo.
    echo [错误] RPC服务器异常退出，错误�? %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
echo [信息] RPC服务器已停止
pause
