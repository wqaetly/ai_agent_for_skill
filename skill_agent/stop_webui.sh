#!/bin/bash
# skill_agent WebUI 停止脚本（Linux/Mac�?
echo "⏹️  停止 skill_agent 技能分析系�?.."
echo ""

# 获取脚本所在目�?SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 读取 PID
LANGGRAPH_PID_FILE="$SCRIPT_DIR/.langgraph.pid"
WEBUI_PID_FILE="$SCRIPT_DIR/.webui.pid"

# 停止 LangGraph 服务�?if [ -f "$LANGGRAPH_PID_FILE" ]; then
    LANGGRAPH_PID=$(cat "$LANGGRAPH_PID_FILE")
    if ps -p $LANGGRAPH_PID > /dev/null 2>&1; then
        echo "🛑 停止 LangGraph 服务�?(PID: $LANGGRAPH_PID)..."
        kill $LANGGRAPH_PID
        echo "�?LangGraph 服务器已停止"
    else
        echo "⚠️  LangGraph 服务器未运行"
    fi
    rm "$LANGGRAPH_PID_FILE"
else
    echo "⚠️  未找�?LangGraph PID 文件"
    # 尝试通过端口查找并停�?    LANGGRAPH_PID=$(lsof -ti:2024)
    if [ ! -z "$LANGGRAPH_PID" ]; then
        echo "🛑 通过端口找到 LangGraph 服务�?(PID: $LANGGRAPH_PID)，正在停�?.."
        kill $LANGGRAPH_PID
        echo "�?LangGraph 服务器已停止"
    fi
fi

# 停止 WebUI
if [ -f "$WEBUI_PID_FILE" ]; then
    WEBUI_PID=$(cat "$WEBUI_PID_FILE")
    if ps -p $WEBUI_PID > /dev/null 2>&1; then
        echo "🛑 停止 WebUI (PID: $WEBUI_PID)..."
        kill $WEBUI_PID
        echo "�?WebUI 已停�?
    else
        echo "⚠️  WebUI 未运�?
    fi
    rm "$WEBUI_PID_FILE"
else
    echo "⚠️  未找�?WebUI PID 文件"
    # 尝试通过端口查找并停�?    WEBUI_PID=$(lsof -ti:3000)
    if [ ! -z "$WEBUI_PID" ]; then
        echo "🛑 通过端口找到 WebUI (PID: $WEBUI_PID)，正在停�?.."
        kill $WEBUI_PID
        echo "�?WebUI 已停�?
    fi
fi

echo ""
echo "�?所有服务已停止"
