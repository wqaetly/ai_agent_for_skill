@echo off
cd /d "%~dp0"
venv\Scripts\python.exe langgraph_server.py > server_output.log 2>&1
