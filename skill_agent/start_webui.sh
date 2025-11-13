#!/bin/bash
# skill_agent WebUI 启动脚本（Linux/Mac）

echo "🚀 启动 skill_agent 技能分析系统..."
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 检查 Node.js 环境
if ! command -v node &> /dev/null; then
    echo "❌ 错误: 未找到 Node.js"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLRAG_DIR="$SCRIPT_DIR"
WEBUI_DIR="$SCRIPT_DIR/../../agent-chat-ui"

echo "📁 skill_agent 目录: $SKILLRAG_DIR"
echo "📁 WebUI 目录: $WEBUI_DIR"
echo ""

# 1. 启动 LangGraph 服务器
echo "1️⃣ 启动 LangGraph 服务器..."
cd "$SKILLRAG_DIR"

# 检查依赖
if [ ! -d "venv" ]; then
    echo "⚠️  未找到虚拟环境，正在创建..."
    python3 -m venv venv
fi

source venv/bin/activate

# 安装依赖
echo "📦 安装 Python 依赖..."
pip install -q -r requirements.txt

# 后台启动 LangGraph 服务器
echo "🔧 启动 LangGraph 服务器 (端口 2024)..."
python langgraph_server.py > langgraph_server.log 2>&1 &
LANGGRAPH_PID=$!
echo "✅ LangGraph 服务器已启动 (PID: $LANGGRAPH_PID)"
echo ""

# 等待服务器启动
sleep 3

# 2. 配置并启动 WebUI
echo "2️⃣ 配置并启动 WebUI..."
cd "$WEBUI_DIR"

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，正在创建..."
    cp "$SKILLRAG_DIR/webui.env" .env
    echo "✅ 已创建 .env 文件"
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装 Node.js 依赖..."
    pnpm install
fi

# 启动 WebUI
echo "🌐 启动 WebUI (端口 3000)..."
pnpm dev &
WEBUI_PID=$!
echo "✅ WebUI 已启动 (PID: $WEBUI_PID)"
echo ""

# 保存 PID 到文件
echo "$LANGGRAPH_PID" > "$SKILLRAG_DIR/.langgraph.pid"
echo "$WEBUI_PID" > "$SKILLRAG_DIR/.webui.pid"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ skill_agent 技能分析系统已启动！"
echo ""
echo "📊 LangGraph 服务器: http://localhost:2024"
echo "🌐 WebUI 界面: http://localhost:3000"
echo ""
echo "📝 日志文件: $SKILLRAG_DIR/langgraph_server.log"
echo ""
echo "⏹️  停止服务: ./stop_webui.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "按 Ctrl+C 停止所有服务..."

# 等待用户中断
wait
