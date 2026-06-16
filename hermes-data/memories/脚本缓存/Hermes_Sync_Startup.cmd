@echo off
REM Hermes 开机同步 — 启动时自动同步到 Desktop/Working/Hermes/
%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe "%USERPROFILE%\AppData\Local\hermes\memories\脚本缓存\hermes_startup_sync.py"