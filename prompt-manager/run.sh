#!/bin/sh
# 启动 提示词管理（macOS / Linux 通用；Windows 请用 run.bat）
# 首次使用先建虚拟环境：python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cd "$(dirname "$0")" || exit 1
if [ ! -x ./.venv/bin/python ]; then
    echo "未找到 .venv，请先建虚拟环境并装依赖： python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi
exec ./.venv/bin/python main.py
