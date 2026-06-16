#!/usr/bin/env bash
# self_learning_v3_wrapper.sh — cron 包装
# 直接调 Python 脚本，确保 stdout 被 cron 捕获

cd "$(dirname "$0")"
python self_learning_v3.py 2>/dev/null || echo "脚本执行失败"