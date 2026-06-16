<# 
.NOTES
    NetEase Cloud Music auto-play helper for browser-media-playback skill.
    
    CRITICAL RULE: NEVER bring windows to foreground, move mouse cursor, or
    maximize windows. The user finds this extremely disruptive.
    
    Strategy (in order):
      1. orpheus://song?id=X — direct desktop client launch (BEST, no windows)
      2. Start Chrome MINIMIZED — page auto-redirects to client on load
      3. Do nothing — just report the page is open, user clicks ▶️
    
    Usage: powershell -ExecutionPolicy Bypass -File netease-auto-play.ps1 -SongId "2538829" -SongTitle "Misty"
    
    History:
      V1: Tried SendKeys(' ') — failed (window was minimized, Space went nowhere)
      V2: Added window-restore + mouse-click — user said "还是没操作对" and 
          explicitly forbade foregrounding windows or moving the mouse
      V3: Uses orpheus:// protocol as primary method. Never touches foreground.
#>
param(
    [string]$SongId = "",
    [string]$SongTitle = "163"
)

# === METHOD 1: Try orpheus:// protocol (direct client launch, no window needed) ===
if ($SongId -ne "") {
    Write-Output "Method 1: Launching via orpheus://song?id=$SongId"
    try {
        Start-Process "orpheus://song?id=$SongId"
        Write-Output "DISPLAY: 已通过 orpheus 协议打开歌曲，客户端应该会自动播放～"
        Start-Sleep -Milliseconds 2000
        exit 0
    } catch {
        Write-Output "orpheus:// protocol failed: $_"
    }
}

# === METHOD 2: Open Chrome minimized (page will auto-redirect to client) ===
$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if ($SongId -ne "" -and (Test-Path $chromePath)) {
    Write-Output "Method 2: Opening song page in MINIMIZED Chrome"
    try {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $chromePath
        $psi.Arguments = "https://music.163.com/#/song?id=$SongId"
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
        [System.Diagnostics.Process]::Start($psi) | Out-Null
        Write-Output "DISPLAY: 页面已在后台打开，会自动跳转到客户端播放～"
        exit 0
    } catch {
        Write-Output "Chrome launch failed: $_"
    }
}

# === METHOD 3: Check if page is already open, report status ===
$procs = Get-Process chrome -ErrorAction SilentlyContinue
foreach ($p in $procs) {
    $title = $p.MainWindowTitle
    if ($title -like '*163*' -or $title -like '*netease*' -or $title -like "*$SongTitle*") {
        Write-Output "Found existing Chrome window: $title"
        Write-Output "DISPLAY: 页面已经打开了，点一下 ▶️ 播放按钮就能听啦～"
        exit 0
    }
}

Write-Output "FAIL: Could not find or open song '$SongId' / '$SongTitle'."
Write-Output "DISPLAY: 没找到播放页面，主人能帮我点开吗？(´;ω;｀)"
exit 1
