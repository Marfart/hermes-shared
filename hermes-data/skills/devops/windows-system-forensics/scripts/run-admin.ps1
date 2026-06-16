#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Universal admin elevation runner for git-bash/MSYS environments.
.DESCRIPTION
    Launches a PowerShell command or script with SYSTEM-level privileges
    via Start-Process -Verb RunAs. Output is written to a temp file and
    read back to stdout so the non-elevated parent can capture results.
.PARAMETER Command
    PowerShell command string to execute as admin.
.PARAMETER ScriptPath
    Path to a .ps1 script file to execute as admin.
.EXAMPLE
    .\run-admin.ps1 -Command "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 10 | Format-Table TimeCreated, Id -AutoSize"
.EXAMPLE
    .\run-admin.ps1 -ScriptPath "C:\scripts\query_logins.ps1"
#>

param(
    [string]$Command = "",
    [string]$ScriptPath = ""
)

# Validate inputs
if ([string]::IsNullOrEmpty($Command) -and [string]::IsNullOrEmpty($ScriptPath)) {
    Write-Error "请提供 -Command 或 -ScriptPath"
    exit 1
}

# Temp file for output
$outputFile = Join-Path $env:TEMP "admin_out_$([System.IO.Path]::GetRandomFileName()).txt"

# Build argument list
if ($ScriptPath -ne "") {
    $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
} else {
    $argList = "-NoProfile -ExecutionPolicy Bypass -Command $Command | Out-File `"$outputFile`" -Encoding UTF8"
}

# Launch elevated and wait
$proc = Start-Process powershell -Verb RunAs -ArgumentList $argList -WindowStyle Hidden -PassThru
$proc | Wait-Process

# Read and return output
if (Test-Path $outputFile) {
    Get-Content $outputFile
    Remove-Item $outputFile -Force
} elseif ($ScriptPath -ne "") {
    Write-Warning "脚本执行完毕，但未生成输出文件（脚本可能自行处理了输出）"
}
