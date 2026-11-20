@echo off
chcp 65001 >nul
REM 启动 提示词管理（Windows）
REM 首次使用先建虚拟环境：py -3 -m venv .venv && .venv\Scripts\pip install -r requirements.txt
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo 未找到 .venv，请先建虚拟环境并装依赖：
    echo     py -3 -m venv .venv
    echo     .venv\Scripts\pip install -r requirements.txt
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" main.py
