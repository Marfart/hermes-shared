import subprocess, os, tempfile

# 写一个 ps1 脚本
ps1 = r"""
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $p = $_.Id
    try {
        $c = (Get-CimInstance Win32_Process -Filter "ProcessId=$p" -ErrorAction SilentlyContinue).CommandLine
        Write-Output "PID $p : $c"
    } catch {
        Write-Output "PID $p : (no cmdline)"
    }
}
"""
with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False, encoding='utf-8') as f:
    f.write(ps1)
    ps1_path = f.name

result = subprocess.run(
    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps1_path],
    capture_output=True, text=True, timeout=15
)
os.unlink(ps1_path)

lines = result.stdout.strip().split('\n')
for line in lines[:20]:
    print(line)
print(f"\nTotal: {len(lines)} python processes")
