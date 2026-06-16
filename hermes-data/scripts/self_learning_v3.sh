#!/usr/bin/env bash
# self_learning_v3.sh — cron入口包装

PYTHON="/c/Users/Admin/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe"
if [ ! -f "$PYTHON" ]; then
    PYTHON="/c/Users/Admin/AppData/Local/Programs/Python/Python311/python.exe"
fi
if [ ! -f "$PYTHON" ]; then
    PYTHON="python.exe"
fi

cd "$(dirname "$0")" || exit 1
"$PYTHON" self_learning_v3.py 2>/dev/null