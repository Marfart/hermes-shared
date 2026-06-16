#!/usr/bin/env bash
# 小马管理员助手 - 以管理员权限执行 PowerShell 命令
# 用法: admin-ps "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 10 | Format-Table TimeCreated, Id -AutoSize"
# 用法: admin-psf /path/to/script.ps1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELPER_PS1="$SCRIPT_DIR/run-admin.ps1"

if [ $# -eq 0 ]; then
    echo "用法: admin-ps 'PowerShell命令'"
    echo "      admin-psf '/path/to/script.ps1'"
    exit 1
fi

if [ "$1" = "-f" ] && [ -n "$2" ]; then
    # 执行脚本文件
    powershell.exe -Command "& '$HELPER_PS1' -ScriptPath '$2'"
else
    # 执行命令
    powershell.exe -Command "& '$HELPER_PS1' -Command \"$1\""
fi
