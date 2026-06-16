#!/usr/bin/env bash
# admin-ps — Windows admin elevation wrapper for git-bash/MSYS
#
# Usage from bash:
#   admin-ps 'Get-WinEvent -FilterHashtable @{LogName="Security"; ID=4624} -MaxEvents 10'
#   admin-ps -f /path/to/script.ps1
#
# Installed path: add to ~/.bashrc:
#   export PATH="$PATH:$HOME/AppData/Local/hermes/skills/devops/windows-system-forensics/scripts"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HELPER="$SCRIPT_DIR/run-admin.ps1"

if [ $# -eq 0 ]; then
    echo "Usage:"
    echo "  admin-ps 'PowerShell command'"
    echo "  admin-ps -f /path/to/script.ps1"
    exit 1
fi

if [ "$1" = "-f" ] && [ -n "$2" ]; then
    powershell.exe -Command "& '$HELPER' -ScriptPath '$2'"
else
    # Escape single quotes for PowerShell nesting
    escaped="${1//\'/\'\'}"
    powershell.exe -Command "& '$HELPER' -Command '$escaped'"
fi
