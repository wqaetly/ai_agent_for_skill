@echo off
chcp 65001 >nul
echo ========================================
echo   SkillRAG 服务器启动脚本
echo ========================================
echo.

cd /d "%~dp0Python"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python！请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] 检查依赖包...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 依赖包未安装，正在安装...
    echo 这可能需要几分钟时间，请耐心等待...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败！
        pause
        exit /b 1
    )
    echo [完成] 依赖安装成功
) else (
    echo [完成] 依赖包已安装
)
echo.

echo [3/3] 启动RAG服务器...
echo.
echo ========================================
echo   服务器启动中...
echo   API文档: http://127.0.0.1:8765/docs
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.

python server.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 服务器启动失败！
    echo 请检查:
    echo   1. Qwen3模型是否已下载到 Data/models/Qwen3-Embedding-0.6B/
    echo   2. 端口8765是否被占用
    echo   3. config.yaml配置是否正确
    echo   4. 技能目录路径是否存在
    echo.
    echo 模型下载: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
    echo.
    pause
)
