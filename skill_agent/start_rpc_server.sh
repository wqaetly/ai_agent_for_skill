#!/bin/bash
# Unity RPC Server 启动脚本 (Linux/Mac)
# 用于Unity与Python的双向通信

set -e  # 遇到错误立即退�?
echo "========================================"
echo "Unity RPC Server Launcher"
echo "========================================"
echo ""

# 切换到脚本所在目�?SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python是否可用
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[错误] Python未安装或未添加到PATH"
    echo "请先安装Python 3.8+"
    exit 1
fi

# 优先使用python3
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "[信息] 使用Python: $($PYTHON_CMD --version)"
echo ""

# 检�?env文件（可选）
if [ ! -f ".env" ]; then
    echo "[警告] 未找�?env文件"
    echo "如需配置环境变量，请复制.env.example�?env"
    echo ""
else
    echo "[信息] 加载环境变量..."
    # 加载.env文件
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
    echo ""
fi

# 设置默认端口
RPC_PORT="${UNITY_RPC_PORT:-8766}"

echo "[信息] 启动Unity RPC服务�?.."
echo "[信息] 监听端口: $RPC_PORT"
echo "[信息] 按Ctrl+C停止服务�?
echo "========================================"
echo ""

# 捕获SIGINT和SIGTERM信号
trap 'echo ""; echo "[信息] 正在停止RPC服务�?.."; exit 0' INT TERM

# 启动RPC服务�?cd Python
$PYTHON_CMD start_unity_rpc.py

# 捕获退出码
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "[错误] RPC服务器异常退出，错误�? $EXIT_CODE"
    exit $EXIT_CODE
fi

echo ""
echo "[信息] RPC服务器已停止"
