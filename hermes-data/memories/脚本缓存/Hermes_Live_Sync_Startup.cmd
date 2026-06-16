@echo off
REM Hermes 实时同步守护进程启动器
REM 后台静默运行，无窗口

setlocal enabledelayedexpansion
set "PYTHON=%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
set "SCRIPT=%USERPROFILE%\AppData\Local\hermes\scripts\hermes_live_sync.py"

if not exist "%PYTHON%" (
    set "PYTHON=python"
)

:: 先检查是否已经在运行
set "PID_FILE=%USERPROFILE%\AppData\Local\hermes\.hermes_live_sync.pid"
if exist "%PID_FILE%" (
    set /p OLD_PID=<"%PID_FILE%"
    tasklist /fi "PID eq !OLD_PID!" 2>nul | find "!OLD_PID!" >nul
    if !errorlevel! equ 0 (
        exit /b 0
    )
)

:: 后台启动（无窗口）
start /B "" "%PYTHON%" "%SCRIPT%" > "%USERPROFILE%\AppData\Local\hermes\logs\live_sync.log" 2>&1