<#
.SYNOPSIS
    NetEase Cloud Music Continuous Player with commentary
    Auto-plays next song with artist intro and appreciation

.EXAMPLE
    .\PlayJazz.ps1
    .\PlayJazz.ps1 -Query "Buddha Bar lounge"
#>

param(
    [string]$Query = "Buddha Bar lounge"
)

Add-Type -AssemblyName System.Web
$ErrorActionPreference = "Continue"
$script:totalPlayed = 0

$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    "Referer"    = "https://music.163.com/"
}

function Get-SongDetail {
    param([string]$songId)
    try {
        $url = "https://music.163.com/api/song/detail?ids=[$songId]"
        $r = Invoke-RestMethod -Uri $url -Headers $headers -TimeoutSec 8
        if ($r.code -eq 200 -and $r.songs.Count -gt 0) { return $r.songs[0] }
    } catch { }
    return $null
}

function Get-Appreciation {
    param($song, $detail, $query)
    
    # Genre detection
    if ($query -match "Buddha|Bar|lounge|chill") {
        $pool = @(
            "Lounge/Chillout, downtempo beats with ambient textures, perfect for relaxing, reading, or sipping a drink.",
            "Slow-burn electronic with exotic samples, creating that signature high-end lounge bar spatial depth.",
            "Steady bassline with hypnotic synth layers -- the classic Buddha-Bar elegant chill.",
            "Lazy groove yet rich in rhythmic texture, works as background music but rewards close listening too.",
            "Eastern motifs fused with Western electronic beats -- the unique magic that made Buddha-Bar a global phenomenon."
        )
    } elseif ($query -match "jazz|piano jazz|saxophone") {
        $pool = @(
            "The improvisational spirit of jazz shines through every phrase -- the dialogue between musicians is electric yet intimate.",
            "Elegant piano voicings with just the right swing feel, a masterclass in classic jazz aesthetics.",
            "Melodic lines flow as naturally as sunlight through Venetian blinds -- warm, never harsh.",
            "This is jazz at its most captivating: finding freedom of expression within a disciplined framework.",
            "Warm, burnished tone throughout, every note shaped with care. Best enjoyed with full attention."
        )
    } elseif ($query -match "classical|orchestra|symphony") {
        $pool = @(
            "Exquisite orchestration weaving intricate sonic tapestries -- new details emerge with every listen.",
            "From delicate pianissimo to thunderous fortissimo, the dynamic range drives emotional intensity forward.",
            "Classical formalism meets romantic sensibility, revealing a composer of profound craft and unique voice."
        )
    } elseif ($query -match "bossa|nova|bossa nova") {
        $pool = @(
            "That signature bossa nova syncopation -- lazy, elastic, instantly transporting you to a Rio beachside cafe.",
            "Soft Portuguese vowels draped over warm nylon-string guitar tones -- the most poetic expression of South American music.",
            "Deceptively simple arrangement, endlessly nuanced. The subtle guitar-percussion interplay creates an unrepeatable mood of relaxation."
        )
    } elseif ($query -match "electronic|ambient|techno|house") {
        $pool = @(
            "Layered synth pads and precise production create an immersive soundscape that rewards both active and passive listening.",
            "The producer demonstrates masterful control of space and texture, each element given room to breathe in the mix.",
            "A sonic journey that evolves subtly over its duration, rewarding patient listeners with intricate details and emotional depth."
        )
    } else {
        $pool = @(
            "Richly layered arrangement with meticulous production, revealing new details with every listen.",
            "Melody that sticks without being cloying, backed by top-tier production that speaks to real artistry.",
            "Genuine emotional expression balanced with technical precision -- the mark of a musician at the top of their craft."
        )
    }
    return $pool | Get-Random
}

function Get-PlayablePlaylist {
    param([string]$query, [int]$desiredCount = 10)
    $playlist = @()
    $encodedQuery = [System.Web.HttpUtility]::UrlEncode($query)
    $searchUrl = "https://music.163.com/api/search/get?s=$encodedQuery&type=1&limit=60"
    try {
        $searchResult = Invoke-RestMethod -Uri $searchUrl -Headers $headers -TimeoutSec 10
    } catch { return $playlist }
    if ($searchResult.code -ne 200 -or -not $searchResult.result.songs) { return $playlist }

    foreach ($song in $searchResult.result.songs) {
        if ($playlist.Count -ge $desiredCount) { break }
        # Skip songs shorter than 3 minutes (180000ms)
        if ($song.duration -lt 180000) { continue }
        $songId = $song.id
        $urlApi = "https://music.163.com/api/song/enhance/player/url?id=$songId&ids=[$songId]&br=320000"
        try {
            $urlResult = Invoke-RestMethod -Uri $urlApi -Headers $headers -TimeoutSec 5
            if ($urlResult.code -eq 200 -and $urlResult.data[0].url) {
                $playlist += @{
                    Id       = $songId
                    Name     = $song.name
                    Artist   = if ($song.artists) { $song.artists[0].name } else { "Unknown" }
                    Album    = if ($song.album) { $song.album.name } else { "" }
                    Url      = $urlResult.data[0].url
                    Bitrate  = $urlResult.data[0].br
                    Duration = $song.duration
                }
            }
        } catch { }
        Start-Sleep -Milliseconds 100
    }
    return $playlist
}

function Get-ArtistInfo {
    param($songDetail)
    $info = @{ Bio = ""; Alias = ""; PublishYear = ""; Label = ""; AlbumName = "" }
    if (-not $songDetail) { return $info }
    if ($songDetail.ar -and $songDetail.ar.Count -gt 0) {
        $artistId = $songDetail.ar[0].id
        try {
            $r = Invoke-RestMethod -Uri "https://music.163.com/api/artist/$artistId" -Headers $headers -TimeoutSec 5
            if ($r.code -eq 200 -and $r.artist -and $r.artist.briefDesc) {
                $info.Bio = $r.artist.briefDesc
            }
            if ($r.artist.alias -and $r.artist.alias.Count -gt 0) {
                $info.Alias = ($r.artist.alias -join ", ")
            }
        } catch { }
    }
    if ($songDetail.al) {
        $info.AlbumName = $songDetail.al.name
        if ($songDetail.al.publishTime) {
            $dt = [DateTimeOffset]::FromUnixTimeMilliseconds($songDetail.al.publishTime)
            $info.PublishYear = $dt.Year
        }
        if ($songDetail.al.company) { $info.Label = $songDetail.al.company }
    }
    return $info
}

function Format-Duration {
    param([int]$ms)
    $totalSec = [Math]::Floor($ms / 1000)
    $min = [Math]::Floor($totalSec / 60)
    $sec = $totalSec % 60
    return "$($min):$($sec.ToString('00'))"
}

function Play-OneSong {
    param($song)
    $script:totalPlayed++
    $detail = Get-SongDetail -songId $song.Id
    $artistInfo = Get-ArtistInfo -songDetail $detail
    $appreciation = Get-Appreciation -song $song -detail $detail -query $Query
    $duration = if ($song.Duration) { Format-Duration $song.Duration } else { "?" }
    $bitrate = if ($song.Bitrate) { "$($song.Bitrate/1000)kbps" } else { "" }

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Magenta
    Write-Host "  #$($script:totalPlayed)  NOW PLAYING" -ForegroundColor Magenta
    Write-Host "============================================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  Title : $($song.Name)" -ForegroundColor Yellow
    Write-Host "  Artist: $($song.Artist)" -ForegroundColor White
    if ($song.Album) { Write-Host "  Album : $($song.Album)" -ForegroundColor Gray }
    if ($artistInfo.PublishYear) { Write-Host "  Year  : $($artistInfo.PublishYear)" -ForegroundColor Gray }
    if ($artistInfo.Label) { Write-Host "  Label : $($artistInfo.Label)" -ForegroundColor Gray }
    Write-Host "  Time  : $duration  |  Quality: $bitrate" -ForegroundColor Gray
    Write-Host ""

    if ($artistInfo.Bio) {
        Write-Host "  --- Artist Background ---" -ForegroundColor Cyan
        $bio = $artistInfo.Bio
        if ($bio.Length -gt 300) { $bio = $bio.Substring(0, 300) + "..." }
        Write-Host "  $bio" -ForegroundColor DarkCyan
        Write-Host ""
    }

    Write-Host "  --- Appreciation ---" -ForegroundColor Cyan
    Write-Host "  $appreciation" -ForegroundColor Green
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Magenta
    Write-Host ""

    # Download MP3 to temp file with proper headers, then play locally
    $tempFile = "$env:TEMP\netease_$($song.Id).mp3"
    Write-Host "  Downloading..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $song.Url -Headers $headers -OutFile $tempFile -TimeoutSec 60
        $fileSize = [Math]::Round((Get-Item $tempFile).Length / 1MB, 1)
        Write-Host "  Downloaded: ${fileSize}MB  Playing..." -ForegroundColor Green
    } catch {
        Write-Host "  [SKIP] Download failed: $_" -ForegroundColor Yellow
        return
    }

    Get-Process wmplayer -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Milliseconds 500
    $proc = Start-Process "wmplayer.exe" -ArgumentList "`"$tempFile`"" -PassThru
    Start-Sleep -Seconds 3
    while (-not $proc.HasExited) { Start-Sleep -Seconds 3 }
    Start-Sleep -Milliseconds 500
    Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
}

# ============ MAIN ============
Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  NetEase Continuous Player" -ForegroundColor Magenta
Write-Host "  Genre: $Query" -ForegroundColor Magenta
Write-Host "  Press Ctrl+C to stop" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$rotateQueries = @($Query, "$Query style", "$Query collection", "$Query mood")
$queryIndex = 0

while ($true) {
    $currentQuery = $rotateQueries[$queryIndex % $rotateQueries.Count]
    Write-Host "Searching: $currentQuery ..." -ForegroundColor Yellow
    $playlist = Get-PlayablePlaylist -query $currentQuery -desiredCount 10

    if ($playlist.Count -eq 0) {
        Write-Host "No playable songs, retrying..." -ForegroundColor Yellow
        $queryIndex++
        Start-Sleep -Seconds 2
        continue
    }

    Write-Host "Loaded $($playlist.Count) songs" -ForegroundColor Green
    foreach ($song in $playlist) { Play-OneSong -song $song }
    $queryIndex++
}
