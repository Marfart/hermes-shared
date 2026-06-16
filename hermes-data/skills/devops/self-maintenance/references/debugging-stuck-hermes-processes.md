# Debugging Stuck / Multiple Hermes Processes (Windows)

When the user says "另一个 Hermes 卡机了" or a Hermes process seems stuck, use this reference.

## Finding Multiple Hermes Instances

```bash
# Quick scan - check how many hermes.exe are running
tasklist | grep -i hermes

# Or more detailed with wmic
powershell -NoProfile -Command "Get-Process -Name hermes | Select-Object Id, CPU, StartTime, Threads, Responding | Format-Table -AutoSize"
```

**Normal running state:**
- A Hermes CLI waiting for user input: **~2 threads, CPU near 0, Responding=True**
- A Hermes actively processing: **CPU > 0, more threads**

If you see a Hermes with 2 threads and 0 CPU but the user thinks it's "stuck" — it's not stuck, it's just waiting for input in another console window.

## Identifying Which Console Belongs to Which Process

```bash
# Get detailed process info including parent PID
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter 'Name=\"hermes.exe\"' | Select-Object ProcessId,Name,CommandLine,ParentProcessId,CreationDate | Format-List"
```

The **ParentProcessId** tells you which shell (PowerShell, CMD, git-bash) launched it. Then:

```bash
# Check what the parent process looks like
powershell -NoProfile -Command "Get-Process -Id <ParentPid> | Select-Object Id,Name,MainWindowTitle,StartTime | Format-Table -AutoSize"
```

## Checking Console Window Owner by PID

Use EnumWindows + GetWindowThreadProcessId to find visible windows:

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    [DllImport("user32.dll", SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
"@
# Use $procId NOT $pid (PowerShell reserved variable!)
$targetPid = 30324
$results = [System.Collections.ArrayList]::new()
$callback = [WinAPI+EnumWindowsProc]{
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 512
    [WinAPI]::GetWindowText($hWnd, $sb, 512) | Out-Null
    $title = $sb.ToString()
    $procId = 0
    [WinAPI]::GetWindowThreadProcessId($hWnd, [ref]$procId) | Out-Null
    if ($procId -eq $targetPid) {
        [void]$results.Add([PSCustomObject]@{HWnd=$hWnd; Title=$title; Pid=$procId})
    }
    return $true
}
[WinAPI]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
$results | Format-Table -AutoSize
```

**⚠️ CRITICAL:** PowerShell has `$pid` as a **reserved read-only variable** (it returns the PowerShell process's own PID). Never use `$pid` in P/Invoke callbacks — use `$procId` instead, or you'll get `SessionStateUnauthorizedAccessException` spam.

## Attempting to Send Input to Another Console

Four approaches, in order of reliability:

### 1. SendKeys (window focus needed)
```powershell
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.SendKeys]::SendWait("your message{ENTER}")
```
**Limitations:** 
- Requires window to be foreground (`SetForegroundWindow` or click)
- Curly braces `{}` are special chars in SendKeys — escape them or avoid
- If the window is an orphaned/minimized console, focus may not work

### 2. WM_CHAR PostMessage
```python
user32.PostMessageW(hwnd, 0x0102, ord('a'), 0)  # WM_CHAR
```
**Limitations:**
- Console windows (conhost.exe) may not process WM_CHAR into their stdin buffer
- Works for GUI apps but not reliably for console apps

### 3. AttachConsole + WriteConsoleInputW (correct approach)
```python
kernel32.AttachConsole(target_pid)
hStdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
# Write INPUT_RECORD with KEY_EVENT
kernel32.WriteConsoleInputW(hStdin, records, 1, byref(written))
kernel32.FreeConsole()
```
**Limitations:**
- Error 5 (Access Denied): Process is in a different session or you lack permissions
- Error 6 (Invalid Handle): Console handle is stale or the console is in a weird state (orphaned process, detached)
- Only works from a process that was NOT already attached to a console

### 4. Kill and restart (last resort)
```bash
taskkill //F //PID 29984
```

## Telltale Signs of a Genuinely Dead Process

| Symptom | Meaning |
|---------|---------|
| 2 threads, 0 CPU | Alive, just waiting for input — NOT stuck |
| MainWindowTitle is empty string | Console window exists but may be orphaned/detached |
| Responding=True but no window visible | Background process, no interaction possible |
| Process exists but parent (PowerShell) is gone | Zombie process — kill it |

## The Clean Kill

When the user agrees:
```bash
taskkill //F //PID <pid>
# Verify it's gone
tasklist | grep hermes
```