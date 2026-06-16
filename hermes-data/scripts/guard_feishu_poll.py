#!/usr/bin/env python3
"""Guardian for feishu_poll.py - restarts it if not running"""
import subprocess
import sys

PROCESS_NAME = "feishu_poll.py"

# Check if feishu_poll.py is running
result = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
    capture_output=True, text=True, timeout=10
)

# Also check python3.exe
result2 = subprocess.run(
    ["tasklist", "/FI", "IMAGENAME eq python3.exe", "/FO", "CSV"],
    capture_output=True, text=True, timeout=10
)

running = False
for output in [result.stdout, result2.stdout]:
    if PROCESS_NAME in output:
        running = True
        break

if running:
    sys.exit(0)  # Silent - process is alive

# Process not running, restart it
import os
script_path = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "hermes", "scripts", "feishu_poll.py"
)

if not os.path.exists(script_path):
    print(f"ERROR: {script_path} not found")
    sys.exit(1)

# Start the process in background
subprocess.Popen(
    [sys.executable, script_path],
    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
    close_fds=True
)
print(f"Restarted {PROCESS_NAME}")