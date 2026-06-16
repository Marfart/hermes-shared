Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
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

Add-Type -AssemblyName System.Windows.Forms

$targetPid = 30324
$targetHwnd = [IntPtr]::Zero

$callback = {
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 512
    [WinAPI]::GetWindowText($hWnd, $sb, 512) | Out-Null
    $procId = 0
    [WinAPI]::GetWindowThreadProcessId($hWnd, [ref]$procId) | Out-Null
    if ($procId -eq $targetPid -and [WinAPI]::IsWindowVisible($hWnd)) {
        $script:targetHwnd = $hWnd
    }
    return $true
}

[WinAPI]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null

if ($targetHwnd -eq [IntPtr]::Zero) {
    Write-Host "NOT_FOUND"
    exit 1
}

Write-Host "FOUND $targetHwnd"

# Restore the window, bring to front
[WinAPI]::ShowWindow($targetHwnd, 9)
Start-Sleep -Milliseconds 500
[WinAPI]::SetForegroundWindow($targetHwnd) | Out-Null
Start-Sleep -Milliseconds 1000

# Send text with Enter
[System.Windows.Forms.SendKeys]::SendWait("wo yi jing gao ding le~ ke yi xia yi bu le!")
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait("~")
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait("~")

Write-Host "SENT"