<#
.SYNOPSIS
    NetEase Cloud Music Background Auto Player
    Searches for a song and plays it in the background without any UI interaction

.PARAMETER SearchQuery
    The song name to search and play

.PARAMETER SongId
    Direct song ID to play (bypasses search if provided)

.EXAMPLE
    .\netease_bg_player.ps1 -SearchQuery "Take Five Dave Brubeck"
    .\netease_bg_player.ps1 -SongId 22091746
#>

param(
    [string]$SearchQuery = "爵士乐 Take Five Dave Brubeck",
    [string]$SongId = ""
)

$ErrorActionPreference = "Continue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============================================================
# Helper Functions
# ============================================================

function Get-NeteaseSongUrl {
    param([string]$songId)

    $headers = @{
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        "Referer" = "https://music.163.com/"
        "Origin" = "https://music.163.com"
        "Accept" = "*/*"
        "Accept-Language" = "zh-CN,zh;q=0.9,en;q=0.8"
    }

    # Try multiple API endpoints for getting playable URLs
    $endpoints = @(
        # Standard player URL API - most reliable
        @{
            Url = "https://music.163.com/api/song/enhance/player/url?id=$songId&ids=[$songId]&br=320000"
            Method = "GET"
        },
        # Alternative: song detail API
        @{
            Url = "https://music.163.com/api/song/detail?ids=[$songId]"
            Method = "GET"
        },
        # Try with CSRF token bypass
        @{
            Url = "https://music.163.com/weapi/song/enhance/player/url?csrf_token="
            Method = "POST"
        },
        # Simplified URL API
        @{
            Url = "https://music.163.com/api/song/url?id=$songId"
            Method = "GET"
        }
    )

    foreach ($ep in $endpoints) {
        try {
            Write-Host "  Trying: $($ep.Url.Substring(0, [Math]::Min(60, $ep.Url.Length)))..."

            $session = [Microsoft.PowerShell.Commands.WebRequestSession]::new()
            $cookie = [System.Net.Cookie]::new("appver", "1.5.2")
            $session.Cookies.Add(([uri]"https://music.163.com"), $cookie)
            $cookie2 = [System.Net.Cookie]::new("os", "pc")
            $session.Cookies.Add(([uri]"https://music.163.com"), $cookie2)

            if ($ep.Method -eq "POST") {
                $body = @{
                    ids = "[$songId]"
                    br = 320000
                    csrf_token = ""
                } | ConvertTo-Json
                $response = Invoke-RestMethod -Uri $ep.Url -Method POST -Body $body -Headers $headers -WebSession $session -TimeoutSec 10 -ContentType "application/x-www-form-urlencoded"
            } else {
                $response = Invoke-RestMethod -Uri $ep.Url -Method GET -Headers $headers -WebSession $session -TimeoutSec 10
            }

            if ($response.code -eq 200) {
                Write-Host "  OK: code=200"
                # Extract URL from response
                $url = $null
                if ($response.data.url) {
                    $url = $response.data.url
                } elseif ($response.data[0].url) {
                    $url = $response.data[0].url
                } elseif ($response.songs[0].mp3Url) {
                    $url = $response.songs[0].mp3Url
                }

                if ($url) {
                    Write-Host "  Got URL: $($url.Substring(0, [Math]::Min(80, $url.Length)))..."
                    return @{
                        Url = $url
                        Size = $response.data.size
                        BitRate = $response.data.br
                        Type = $response.data.type
                    }
                } else {
                    Write-Host "  API returned 200 but no URL (likely requires login)"
                }
            } else {
                Write-Host "  Failed: code=$($response.code)"
            }
        } catch {
            Write-Host "  Error: $_"
        }
    }

    return $null
}

function Search-NeteaseSong {
    param([string]$query)

    $headers = @{
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        "Referer" = "https://music.163.com/"
    }

    $encodedQuery = [System.Web.HttpUtility]::UrlEncode($query)
    $searchUrl = "https://music.163.com/api/search/get?s=$encodedQuery&type=1&limit=5"

    try {
        $response = Invoke-RestMethod -Uri $searchUrl -Headers $headers -TimeoutSec 10
        if ($response.code -eq 200 -and $response.result.songs) {
            return $response.result.songs
        }
    } catch {
        Write-Host "Search error: $_"
    }

    return @()
}

function Play-Mp3Url {
    param([string]$url, [string]$title)

    Write-Host "Playing: $title"

    # Strategy 1: Use Windows Media Player COM object (background playback)
    try {
        $wmp = New-Object -ComObject "WMPlayer.OCX"
        $wmp.settings.volume = 70
        $wmp.settings.autoStart = $true
        $wmp.URL = $url
        Write-Host "  [OK] Playing via Windows Media Player COM"
        return $wmp
    } catch {
        Write-Host "  WMP COM failed: $_"
    }

    # Strategy 2: System.Media.SoundPlayer (limited format support)
    try {
        $wc = New-Object System.Net.WebClient
        $tempFile = [System.IO.Path]::GetTempFileName() + ".mp3"
        $wc.DownloadFile($url, $tempFile)
        $player = New-Object System.Media.SoundPlayer($tempFile)
        $player.Play()
        Write-Host "  [OK] Playing via SoundPlayer (downloaded to temp)"
        return $player
    } catch {
        Write-Host "  SoundPlayer failed: $_"
    }

    # Strategy 3: Start mplay32.exe or wmplayer.exe in background
    try {
        $proc = Start-Process "wmplayer.exe" -ArgumentList "/play /close `"$url`"" -WindowStyle Hidden -PassThru
        Write-Host "  [OK] Playing via wmplayer.exe (hidden)"
        return $proc
    } catch {
        Write-Host "  wmplayer.exe failed: $_"
    }

    return $null
}

function Invoke-OrpheusPlay {
    param([string]$songId)

    $orpheusUrl = "orpheus://song/$songId/?autoplay=1"

    # Method 1: Direct process call
    $cloudmusicPath = "C:\Program Files\NetEase\CloudMusic\cloudmusic.exe"
    if (Test-Path $cloudmusicPath) {
        try {
            Start-Process -FilePath $cloudmusicPath -ArgumentList "--webcmd=`"$orpheusUrl`"" -WindowStyle Hidden
            Write-Host "  Sent orpheus command to cloudmusic.exe"
        } catch {
            Write-Host "  orpheus command failed: $_"
        }
    }

    # Method 2: Create hidden IE to trigger protocol
    try {
        $ie = New-Object -ComObject "InternetExplorer.Application"
        $ie.Visible = $false
        $ie.Navigate2($orpheusUrl)
        Start-Sleep -Seconds 2
        $ie.Quit()
        Write-Host "  Triggered orpheus via hidden IE"
    } catch {
        Write-Host "  IE approach: $_"
    }
}

# ============================================================
# Main Execution
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NetEase Cloud Music Background Player" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get song ID
if ($SongId) {
    $targetSong = @{ id = $SongId; name = "Direct Song ID" }
    Write-Host "Using provided Song ID: $SongId"
} else {
    Write-Host "Searching for: $SearchQuery"
    $songs = Search-NeteaseSong -query $SearchQuery

    if ($songs.Count -eq 0) {
        Write-Host "[FAIL] No songs found for query: $SearchQuery"

        # Fallback: use known jazz song IDs
        $knownJazzSongs = @(
            @{ id = "22091746"; name = "Take Five - Dave Brubeck Quartet" },
            @{ id = "1087887"; name = "Fly Me To The Moon - Frank Sinatra" },
            @{ id = "18678679"; name = "So What - Miles Davis" },
            @{ id = "22555654"; name = "Autumn Leaves - Bill Evans" }
        )

        Write-Host "Using fallback jazz songs..."
        $targetSong = $knownJazzSongs | Get-Random
        Write-Host "Selected: $($targetSong.name) (ID: $($targetSong.id))"
    } else {
        $targetSong = $songs[0]
        Write-Host "Found: $($targetSong.name) - $($targetSong.artists[0].name) (ID: $($targetSong.id))"
    }
}

# Step 2: Get playable URL
Write-Host ""
Write-Host "Getting playable URL..."
$songUrl = Get-NeteaseSongUrl -songId $targetSong.id

# Step 3: Play or fallback
if ($songUrl -and $songUrl.Url) {
    Write-Host ""
    Write-Host "[SUCCESS] Got playable URL!" -ForegroundColor Green
    $player = Play-Mp3Url -url $songUrl.Url -title $targetSong.name

    Write-Host ""
    Write-Host "Now playing: $($targetSong.name)" -ForegroundColor Green
    Write-Host "The music is playing in the background (no visible window)."
    Write-Host "Press Ctrl+C to stop playback."

    # Keep script running to maintain playback
    try {
        while ($true) {
            Start-Sleep -Seconds 5
            # Refresh if needed
        }
    } catch {
        Write-Host "Playback stopped."
    }
} else {
    Write-Host ""
    Write-Host "[WARN] Could not get direct playable URL (API requires authentication)" -ForegroundColor Yellow
    Write-Host "Falling back to orpheus protocol (will open NetEase Cloud Music client)..." -ForegroundColor Yellow
    Write-Host ""

    # Step 3: Try orpheus protocol (opens client app, might need user interaction)
    Invoke-OrpheusPlay -songId $targetSong.id

    Write-Host ""
    Write-Host "Attempted to play via orpheus:// protocol." -ForegroundColor Yellow
    Write-Host "If the NetEase Cloud Music client is running, it should now play:" -ForegroundColor Yellow
    Write-Host "  >> $($targetSong.name) <<" -ForegroundColor Green
    Write-Host ""
    Write-Host "Note: If the client doesn't auto-play, try:"
    Write-Host "  1. Make sure NetEase Cloud Music is running"
    Write-Host "  2. Open https://music.163.com/#/song?id=$($targetSong.id) in browser"
    Write-Host "  3. Click the 'Open in client' button"
}
