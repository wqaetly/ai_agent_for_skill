@echo off
REM Qwen3 Embedding Model Download Script
REM 单独下载或更新嵌入模型
chcp 65001 >nul

echo.
echo ============================================================
echo    Qwen3-Embedding-0.6B 模型下载工具
echo ============================================================
echo.

REM Get script directory
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 错误: 虚拟环境不存在
    echo 请先运行 start_webui_with_logs.bat 初始化环境
    pause
    exit /b 1
)

REM Run model download script
python check_and_download_model.py

if errorlevel 1 (
    echo.
    echo 模型下载失败或被取消
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 操作完成！
echo ============================================================
echo.
pause
