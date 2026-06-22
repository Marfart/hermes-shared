import subprocess, sys

# 用 tasklist 查看 python 进程的命令行
result = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "Get-Process python | ForEach-Object { $p = $_.Id; $c = (Get-CimInstance Win32_Process -Filter \"ProcessId=$p\").CommandLine; Write-Output \"PID $p : $c\" }"],
    capture_output=True, text=True, timeout=15
)
lines = result.stdout.strip().split('\n')
for line in lines[:15]:
    print(line)
print(f"\nTotal python processes: {len(lines)}")
