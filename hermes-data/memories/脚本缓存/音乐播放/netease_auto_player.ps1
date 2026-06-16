# NetEase Cloud Music Auto Player - Research & Implementation
# Goal: Fully automate searching and playing a song without any user interaction

param(
    [string]$SearchQuery = "Take Five Dave Brubeck",
    [string]$MusicPath = "C:\Program Files\NetEase\CloudMusic\cloudmusic.exe"
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logFile = "$scriptDir\netease_auto_player_log.txt"

function Log {
    param([string]$msg)
    $timestamp = Get-Date -Format "HH:mm:ss"
    $line = "[$timestamp] $msg"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

Log "========== NetEase Auto Player Research =========="
Log "Search query: $SearchQuery"

# ============================================================
# Phase 1: Environment Discovery
# ============================================================
Log ""
Log "=== Phase 1: Environment Discovery ==="

# Check if cloudmusic is installed
if (Test-Path $MusicPath) {
    Log "[OK] CloudMusic found at: $MusicPath"
} else {
    Log "[FAIL] CloudMusic not found at $MusicPath"
    # Try to find it
    $found = Get-ChildItem -Path "$env:ProgramFiles", "${env:ProgramFiles(x86)}", "$env:LOCALAPPDATA" -Filter "cloudmusic.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        $MusicPath = $found.FullName
        Log "[OK] Found at: $MusicPath"
    }
}

# Check available runtimes
$hasNode = Get-Command node -ErrorAction SilentlyContinue
$hasPython = Get-Command python -ErrorAction SilentlyContinue
$hasPython3 = Get-Command python3 -ErrorAction SilentlyContinue
Log "Node.js: $($hasNode -ne $null)"
Log "Python: $($hasPython -ne $null -or $hasPython3 -ne $null)"

# Check .NET version
try {
    $netVersion = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full" -ErrorAction SilentlyContinue).Version
    Log ".NET Framework: $netVersion"
} catch {
    Log ".NET Framework: check failed"
}

# ============================================================
# Phase 2: Port & API Discovery
# ============================================================
Log ""
Log "=== Phase 2: Port & API Discovery ==="

# Get all TCP listeners for cloudmusic processes
$cloudPids = Get-Process -Name cloudmusic -ErrorAction SilentlyContinue | ForEach-Object { $_.Id }
Log "CloudMusic PIDs: $($cloudPids -join ', ')"

$allPorts = @()
if ($cloudPids) {
    $netstat = netstat -ano | Select-String "LISTENING"
    foreach ($line in $netstat) {
        foreach ($cpid in $cloudPids) {
            if ($line -match "\s+$cpid$" -or $line -match "\s+$cpid\s*$") {
                if ($line -match "127\.0\.0\.1:(\d+)" -or $line -match "0\.0\.0\.0:(\d+)") {
                    $port = [int]$Matches[1]
                    $allPorts += $port
                    Log "CloudMusic listening on port: $port"
                }
            }
        }
    }
}

# Test each port for HTTP/API
foreach ($port in $allPorts) {
    Log "Testing port $port..."

    # Test HTTP
    $endpoints = @(
        "/", "/api", "/api/v1", "/player", "/status",
        "/player/play", "/player/pause", "/player/next",
        "/song", "/song/url", "/search"
    )

    foreach ($ep in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port$ep" -TimeoutSec 1 -ErrorAction Stop
            Log "  HTTP GET $ep => $($response.StatusCode) : $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))"
        } catch {
            # Silently skip
        }
    }
}

# ============================================================
# Phase 3: orpheus Protocol Research
# ============================================================
Log ""
Log "=== Phase 3: orpheus Protocol ==="

# Check registry for orpheus handler
$orpheusReg = Get-Item "HKLM:\SOFTWARE\Classes\orpheus" -ErrorAction SilentlyContinue
if ($orpheusReg) {
    $commandKey = Get-ItemProperty "HKLM:\SOFTWARE\Classes\orpheus\shell\open\command" -ErrorAction SilentlyContinue
    Log "orpheus handler: $($commandKey.'(default)')"
}

# Test orpheus URL formats
$songId = "22091746"  # Take Five
$orpheusFormats = @(
    "orpheus://song/$songId/?autoplay=1",
    "orpheus://song/$songId?autoplay=1",
    "orpheus://song/?id=$songId&autoplay=1",
    "orpheus://song?id=$songId&autoplay=1",
    "orpheus://play/$songId",
    "orpheus://play?songId=$songId"
)

Log "Testing orpheus URL formats..."
foreach ($fmt in $orpheusFormats) {
    try {
        $proc = Start-Process -FilePath $MusicPath -ArgumentList "--webcmd=`"$fmt`"" -PassThru
        Start-Sleep -Milliseconds 500
        if (-not $proc.HasExited) {
            Log "  [OK] $fmt (process running)"
        }
    } catch {
        Log "  [FAIL] $fmt : $_"
    }
}

# ============================================================
# Phase 4: API Based Approach
# ============================================================
Log ""
Log "=== Phase 4: Public API Search ==="

# Try the official NetEase search API (public, no auth needed for search)
try {
    $searchUrl = "https://music.163.com/api/search/get?s=" + [System.Web.HttpUtility]::UrlEncode($SearchQuery) + "&type=1&limit=5"
    $searchResult = Invoke-RestMethod -Uri $searchUrl -TimeoutSec 10
    if ($searchResult.code -eq 200 -and $searchResult.result.songs) {
        Log "Search API works! Found $($searchResult.result.songs.Count) songs"
        foreach ($song in $searchResult.result.songs | Select-Object -First 3) {
            Log "  Song: $($song.name) - $($song.artists[0].name) (ID: $($song.id))"
        }
    } else {
        Log "Search API failed: code=$($searchResult.code)"
    }
} catch {
    Log "Search API error: $_"
}

# ============================================================
# Phase 5: Window & Process Interaction
# ============================================================
Log ""
Log "=== Phase 5: Window Interaction ==="

# Get main cloudmusic window
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public class NAPWin32 {
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWinProc lpEnumFunc, IntPtr lParam);
    public delegate bool EnumWinProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr hWnd, out int lpdwProcessId);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool AllowSetForegroundWindow(int dwProcessId);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int X, int Y);
    [DllImport("user32.dll")] public static extern void mouse_event(int dwFlags, int dx, int dy, int dwData, int dwExtraInfo);
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT lpPoint);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vKey);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")] public static extern IntPtr FindWindowEx(IntPtr hWndParent, IntPtr hWndChildAfter, string lpszClass, string lpszWindow);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X; public int Y; }
}
"@

$cloudWindows = @()
$callback = {
    param($hwnd, $lparam)
    $procId = 0
    [NAPWin32]::GetWindowThreadProcessId($hwnd, [ref]$procId)
    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    if ($proc -and $proc.ProcessName -eq "cloudmusic") {
        $sb = New-Object System.Text.StringBuilder(256)
        $cb = New-Object System.Text.StringBuilder(256)
        [NAPWin32]::GetWindowText($hwnd, $sb, 256)
        [NAPWin32]::GetClassName($hwnd, $cb, 256)
        $visible = [NAPWin32]::IsWindowVisible($hwnd)
        $rect = New-Object NAPWin32+RECT
        [NAPWin32]::GetWindowRect($hwnd, [ref]$rect)
        $obj = @{
            HWND = $hwnd
            PID = $procId
            Title = $sb.ToString()
            Class = $cb.ToString()
            Visible = $visible
            Rect = "$($rect.Left),$($rect.Top) $($rect.Right)x$($rect.Bottom)"
        }
        $script:cloudWindows += $obj
        Log "Window: HWND=$hwnd PID=$procId Class=$($obj.Class) Title='$($obj.Title)' Visible=$visible"
    }
    return $true
}
$del = [NAPWin32+EnumWinProc]$callback
[NAPWin32]::EnumWindows($del, [IntPtr]::Zero)

$mainWindow = $cloudWindows | Where-Object { $_.Title.Length -gt 0 -and $_.Title -ne "Default IME" } | Select-Object -First 1
if (-not $mainWindow) {
    $mainWindow = $cloudWindows | Where-Object { $_.Class -eq "OrpheusBrowserHost" } | Select-Object -First 1
}
if (-not $mainWindow) {
    $mainWindow = $cloudWindows | Select-Object -First 1
}

if ($mainWindow) {
    Log "Using main window: $($mainWindow.Title) (Class: $($mainWindow.Class))"
}

# ============================================================
# Phase 6: Implementation Strategy
# ============================================================
Log ""
Log "=== Phase 6: Strategy Selection ==="
Log "Based on findings, selecting best approach..."

# Strategy 1: If search API works, get song URL and play directly
# Strategy 2: Use Chrome CDP with default profile
# Strategy 3: Direct window manipulation via keystrokes
# Strategy 4: Orpheus protocol with retry logic

# For now, let's try Strategy 3: Direct window interaction with SendKeys
# This is the most reliable fallback if we can get window focus

Log ""
Log "=== Phase 7: Attempting Automation ==="

if ($mainWindow) {
    $hwnd = $mainWindow.HWND
    $procId = $mainWindow.PID

    Log "Starting automation with window: $($mainWindow.Title)"

    # Bring window to front
    [NAPWin32]::AllowSetForegroundWindow($procId) | Out-Null
    [NAPWin32]::ShowWindow($hwnd, 5) | Out-Null
    Start-Sleep -Milliseconds 200
    [NAPWin32]::BringWindowToTop($hwnd) | Out-Null
    Start-Sleep -Milliseconds 100
    $fgResult = [NAPWin32]::SetForegroundWindow($hwnd)
    Log "SetForegroundWindow: $fgResult"

    # Simulate Alt key to help with foreground switching
    [NAPWin32]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 30
    [NAPWin32]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 200

    $fgResult = [NAPWin32]::SetForegroundWindow($hwnd)
    Log "SetForegroundWindow retry: $fgResult"

    if ($fgResult) {
        # Window is in foreground, now use SendKeys
        Add-Type -AssemblyName System.Windows.Forms

        # Step 1: Ctrl+F to focus search box
        Log "Pressing Ctrl+F for search..."
        [System.Windows.Forms.SendKeys]::SendWait("^f")
        Start-Sleep -Milliseconds 500

        # Step 2: Clear search box and type query
        [System.Windows.Forms.SendKeys]::SendWait("^a")
        Start-Sleep -Milliseconds 50
        [System.Windows.Forms.SendKeys]::SendWait("{DELETE}")
        Start-Sleep -Milliseconds 100
        [System.Windows.Forms.SendKeys]::SendWait($SearchQuery)
        Start-Sleep -Milliseconds 500

        # Step 3: Press Enter to search
        [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
        Log "Search sent"
        Start-Sleep -Milliseconds 1500

        # Step 4: Navigate to first result using mouse click
        # Get window rect to calculate click position
        $rect = New-Object NAPWin32+RECT
        [NAPWin32]::GetWindowRect($hwnd, [ref]$rect)
        Log "Window: $($rect.Left),$($rect.Top) - $($rect.Right),$($rect.Bottom)"

        # The search results area starts approximately at y=140 from window top
        # First song row is around y=200, with the playable area at x=250-500
        $clickX = $rect.Left + 300
        $clickY = $rect.Top + 220

        Log "Double-clicking at $clickX, $clickY"

        # Move mouse and double-click
        [NAPWin32]::SetCursorPos($clickX, $clickY)
        Start-Sleep -Milliseconds 100

        $MOUSEEVENTF_LEFTDOWN = 0x02
        $MOUSEEVENTF_LEFTUP = 0x04

        [NAPWin32]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 50
        [NAPWin32]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 200
        [NAPWin32]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        Start-Sleep -Milliseconds 50
        [NAPWin32]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

        Log "Double-click complete"
        Start-Sleep -Milliseconds 2000

        # Check if song changed
        $newTitle = (Get-Process -Id $procId -ErrorAction SilentlyContinue).MainWindowTitle
        Log "After attempt - Playing: $newTitle"
    } else {
        Log "[WARN] Could not set foreground window, trying alternative..."
        # Try using Chrome instead
        # ... (implement Chrome-based approach)
    }
}

Log "========== Research Complete =========="
Log "Full log saved to: $logFile"
