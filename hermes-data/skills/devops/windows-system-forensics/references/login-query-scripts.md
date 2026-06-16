# Login Query Script Templates

Ready-to-copy .ps1 script templates for Windows login/event forensics.

## 📁 Output Directory Convention

All temp output files go to `$env:TEMP\` (e.g. `C:\Users\Admin\AppData\Local\Temp\`).
**Never save temp scripts or output to the Desktop.**

For the agent (Hermes): organize reusable scripts under `~/AppData/Local/hermes/memories/脚本缓存/`
with subfolders by category (admin助手/, 系统查询/, etc.).

## 🛠 Reusable Elevation Helpers

The skill ships with reusable helpers in `scripts/`:

| Helper | Purpose |
|--------|---------|
| `scripts/run-admin.ps1` | Generic admin runner — pass -Command or -ScriptPath |
| `scripts/admin-ps.sh` | Bash wrapper, add to PATH for quick `admin-ps "command"` |

**Usage:**
```bash
# Run a PowerShell command as admin
admin-ps 'Get-WinEvent -FilterHashtable @{LogName="Security"; ID=4624} -MaxEvents 10'

# Run a .ps1 script as admin
admin-ps -f /path/to/script.ps1
```

## 1. All Interactive Logins (Last N)

```powershell
$events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 200
$out = @()
foreach ($evt in $events) {
    $logonType = $evt.Properties[8].Value
    if ($logonType -eq 2 -or $logonType -eq 10) {
        $time = $evt.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')
        $user = $evt.Properties[5].Value
        $typeName = if ($logonType -eq 2) { '交互式' } else { '远程' }
        $out += "$time | $user | $typeName"
    }
}
$outFile = Join-Path $env:TEMP "login_results.txt"
$out | Out-File $outFile -Encoding UTF8
Write-Output "Results saved to: $outFile"
```

## 2. Full Session Timeline (Lock/Unlock/Logoff + Logins)

```powershell
$logins = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 200
$sessions = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4800,4801,4802,4803,4647} -MaxEvents 50
$shutdowns = Get-WinEvent -FilterHashtable @{LogName='System'; ID=1074,6006} -MaxEvents 10
$boots = Get-WinEvent -FilterHashtable @{LogName='System'; ID=12,6005} -MaxEvents 5

$out = @()
$out += "=== BOOT EVENTS ==="
foreach ($e in $boots) {
    $desc = if ($e.Id -eq 12) { 'Boot(OS启动)' } else { 'EventLog已启动' }
    $out += ($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + " | " + $desc)
}

$out += "=== INTERACTIVE LOGINS ==="
foreach ($evt in $logins) {
    $t = $evt.Properties[8].Value
    if ($t -eq 2 -or $t -eq 10) {
        $out += ($evt.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + " | " + $evt.Properties[5].Value)
    }
}

$out += '=== SESSION EVENTS ==='
$lookup = @{
    4800 = '工作站锁定'
    4801 = '工作站解锁'
    4802 = '屏幕保护启动'
    4803 = '屏幕保护关闭'
    4647 = '用户注销'
}
foreach ($e in $sessions) {
    $desc = if ($lookup.ContainsKey($e.Id)) { $lookup[$e.Id] } else { 'ID:' + $e.Id }
    $out += ($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + " | " + $desc)
}

$out += '=== SHUTDOWN EVENTS ==='
foreach ($e in $shutdowns) {
    $desc = if ($e.Id -eq 1074) { '关机启动' } else { 'EventLog停止(关机完成)' }
    $out += ($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss') + " | " + $desc)
}

$outFile = Join-Path $env:TEMP "timeline.txt"
$out | Out-File $outFile -Encoding UTF8
Write-Output "Results saved to: $outFile"
```

## 3. Quick Check (No Elevation Required)

When admin elevation is unavailable, use these WMI/CIM fallbacks:

```powershell
# Last logon time per user
Get-CimInstance Win32_NetworkLoginProfile | Format-Table Name, LastLogon -AutoSize

# Current active sessions
Get-CimInstance Win32_LogonSession | Where-Object { $_.LogonType -in @(2,10) } | Format-Table StartTime, LogonType, UserName -AutoSize

# System boot time
(Get-CimInstance Win32_OperatingSystem).LastBootUpTime
```

## Interpreting Results

**Normal daily pattern:**
```
08:31   | Boot(OS启动)                    # Computer turned on
08:31   | UMFD-1                          # Login screen ready
08:31   | 工作站解锁                       # User unlocks (enters password)
08:32   | Admin (Type:2)                  # User logged in
... (workday) ...
18:06   | CodexSandboxOffline (Type:2)     # Codex CLI agent activity (if used)
18:20   | 用户注销                         # User logged off
18:20   | 关机启动                         # Shutdown initiated
18:20   | EventLog停止(关机完成)           # System shut down
```

**Things to look for:**
- `CodexSandboxOffline` logons → someone used Codex CLI (AI coding agent)
- Late-night interactive logons → possible unauthorized access
- Type 10 (RemoteInteractive) logons → RDP connections
- Missing shutdown event (ID 6008/41) → unexpected power loss or crash
