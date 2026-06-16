#!/usr/bin/env bash
# 小马电脑卫士 - cron监控脚本 (no_agent模式)
# 每2分钟运行一次，检查是否有异常活动
# 注意: MSYS bash下$USERPROFILE可能含正斜杠，PowerShell -File必须用Windows路径

PS_SCRIPT="C:\\Users\\Admin\\AppData\\Local\\hermes\\memories\\scripts_cache\\guard_monitor.ps1"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS_SCRIPT"
