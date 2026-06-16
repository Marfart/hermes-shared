Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll", SetLastError=true)]
    public static extern IntPtr GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
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

$results = @()
$callback = [WinAPI+EnumWindowsProc]{
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 512
    [WinAPI]::GetWindowText($hWnd, $sb, 512) | Out-Null
    $title = $sb.ToString()
    $pid = 0
    [WinAPI]::GetWindowThreadProcessId($hWnd, [ref]$pid) | Out-Null
    if ($pid -eq 30324 -or $pid -eq 29984) {
        $visible = [WinAPI]::IsWindowVisible($hWnd)
        $results.Add([PSCustomObject]@{HWnd=$hWnd; Title=$title; Pid=$pid; Visible=$visible}) | Out-Null
    }
    return $true
}
[WinAPI]::EnumWindows($callback, [IntPtr]::Zero) | Out-Null
$results | Format-Table -AutoSize