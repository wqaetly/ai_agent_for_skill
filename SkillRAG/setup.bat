@echo off
chcp 65001 >nul
echo ========================================
echo   SkillRAG 安装脚本
echo ========================================
echo.

cd /d "%~dp0Python"

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python！
    echo.
    echo 请先安装Python 3.8或更高版本：
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并安装Python
    echo   3. 安装时勾选 "Add Python to PATH"
    echo   4. 重启命令行后重新运行此脚本
    echo.
    pause
    exit /b 1
)
python --version
echo [完成] Python环境检查通过
echo.

echo [2/4] 检查pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] pip未正确安装！
    pause
    exit /b 1
)
echo [完成] pip可用
echo.

echo [3/3] 安装Python依赖包...
echo 这可能需要5-10分钟，取决于网络速度...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [错误] 依赖包安装失败！
    echo.
    echo 可能的原因:
    echo   1. 网络连接问题
    echo   2. pip源速度慢
    echo.
    echo 解决方案:
    echo   使用国内pip镜像源加速安装:
    echo   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    pause
    exit /b 1
)

echo [完成] 依赖包安装成功
echo.

echo.
echo ========================================
echo   依赖安装完成！
echo ========================================
echo.
echo 下一步:
echo   1. 确保已下载Qwen3模型到: Data/models/Qwen3-Embedding-0.6B/
echo   2. 编辑 Python/config.yaml 配置技能目录路径
echo   3. 运行 start_rag_server.bat 启动服务器
echo   4. 在Unity中打开 技能系统 ^> RAG查询窗口
echo.
echo 重要提示:
echo   - 系统使用本地模型，需要先手动下载 Qwen3-Embedding-0.6B 模型
echo   - 模型下载: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
echo   - 或使用: git lfs clone https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
echo   - 确保模型文件在: Data/models/Qwen3-Embedding-0.6B/ 目录下
echo.
echo 详细使用说明请查看:
echo   - README.md (完整文档)
echo   - QUICK_START.md (快速开始)
echo.
pause
