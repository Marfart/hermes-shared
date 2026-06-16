#!/usr/bin/env pwsh
<#
.SYNOPSIS
    以管理员权限执行 PowerShell 命令并返回结果（小马专用助手）
.DESCRIPTION
    自动以 SYSTEM 权限执行指定的 PowerShell 命令，
    将结果写入临时文件并读取返回。
.PARAMETER Command
    要执行的 PowerShell 命令（用单引号包裹）
.PARAMETER ScriptPath
    可选：要执行的 .ps1 脚本路径
.EXAMPLE
    ./run-admin.ps1 "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 10"
#>

param(
    [string]$Command = "",
    [string]$ScriptPath = ""
)

$outputFile = "$env:TEMP\admin_out_$([System.IO.Path]::GetRandomFileName()).txt"

if ($ScriptPath -ne "") {
    $argList = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
} elseif ($Command -ne "") {
    $argList = "-NoProfile -ExecutionPolicy Bypass -Command $Command | Out-File `"$outputFile`" -Encoding UTF8"
} else {
    Write-Error "请提供 -Command 或 -ScriptPath"
    exit 1
}

$proc = Start-Process powershell -Verb RunAs -ArgumentList $argList -WindowStyle Hidden -PassThru
$proc | Wait-Process

if ($outputFile -and (Test-Path $outputFile)) {
    Get-Content $outputFile
    Remove-Item $outputFile -Force
}
