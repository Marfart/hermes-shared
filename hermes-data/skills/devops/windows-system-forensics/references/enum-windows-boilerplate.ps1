# EnumWindows Boilerplate — Find visible/invisible windows for a given PID
# PowerShell 5.1 / 7.x compatible
# 
# Usage: replace <TARGET_PID> and <PARENT_PID> with actual PIDs
# 
# CRITICAL: Do NOT use $pid as a local variable name — it is an automatic
# read-only variable in PowerShell (always holds the current process ID).
# Using $pid = 0 as a local variable causes
# SessionStateUnauthorizedAccessException. Always use $procId or $pIdOut.

Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll")]
    public static extern IntPtr GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
    
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    
    [DllImport("user32.dll", CharSet=CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
}
"@

$results = [System.Collections.ArrayList]::new()
$callback = [WinAPI+EnumWindowsProc]{ 
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 512
    [WinAPI]::GetWindowText($hWnd, $sb, 512) | Out-Null
    $procId = 0  # ← DO NOT name this $pid !
    [void][WinAPI]::GetWindowThreadProcessId($hWnd, [ref]$procId)
    if ($procId -eq <TARGET_PID> -or $procId -eq <PARENT_PID>) {
        [void]$results.Add([PSCustomObject]@{
            Title   = $sb.ToString()
            Pid     = $procId
            Visible = [WinAPI]::IsWindowVisible($hWnd)
        })
    }
    return $true
}
[WinAPI]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
$results | Format-Table -AutoSize