import subprocess, sys, time, os

# 用 WMI 监控进程创建事件60秒
# 只关注可能弹窗的进程

TARGETS = ['python', 'cmd', 'powershell', 'bash', 'mintty', 'conhost', 'node', 'wscript', 'cscript']

print(f"[{time.strftime('%H:%M:%S')}] Monitoring process creation for 60s...")
print(f"Targets: {', '.join(TARGETS)}")
print("---")

# 用 PowerShell 的 Get-WinEvent 查最近进程创建
# 先记录当前所有进程ID
result = subprocess.run(
    ['powershell', '-NoProfile', '-Command', 
     'Get-Process | Select-Object Id, ProcessName | ConvertTo-Json'],
    capture_output=True, text=True, timeout=10
)

import json
try:
    current_procs = json.loads(result.stdout)
    current_ids = {p['Id'] for p in current_procs}
except:
    current_ids = set()

# 等60秒，每5秒检查一次新进程
for i in range(12):
    time.sleep(5)
    result = subprocess.run(
        ['powershell', '-NoProfile', '-Command', 
         'Get-Process | Select-Object Id, ProcessName, @{N="CmdLine";E={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine}} | ConvertTo-Json'],
        capture_output=True, text=True, timeout=15
    )
    try:
        procs = json.loads(result.stdout)
        if not isinstance(procs, list):
            procs = [procs]
        for p in procs:
            pid = p.get('Id', 0)
            name = p.get('ProcessName', '')
            if pid not in current_ids and any(t in name.lower() for t in TARGETS):
                cmd = p.get('CmdLine', '')[:150]
                print(f"[{time.strftime('%H:%M:%S')}] NEW: {name} PID={pid}")
                print(f"  CMD: {cmd}")
                print()
            current_ids.add(pid)
    except Exception as e:
        pass

print(f"[{time.strftime('%H:%M:%S')}] Done monitoring.")
