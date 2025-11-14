@echo off
REM LangGraph Server 启动脚本
REM 自动检测并清理占用端口的旧进程

echo ========================================
echo   SkillRAG LangGraph Server
echo ========================================
echo.

cd /d %~dp0
call venv\Scripts\activate.bat

echo Starting server...
python langgraph_server.py

pause
