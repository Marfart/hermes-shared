# Windows 系统取证

## 登录历史
- 安全事件日志: Event ID 4624(成功), 4625(失败)
- 登录类型: 2(本地), 10(RDP), 3(网络)
- `wevtutil qe Security /q:"*[System[EventID=4624]]" /c:10`

## 事件日志分析
```powershell
# 最近安全日志
Get-WinEvent -FilterHashtable @{LogName='Security'; StartTime=(Get-Date).AddDays(-7)} -MaxEvents 50

# PowerShell操作日志
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'} -MaxEvents 20
```

## 注册表取证
- HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run — 自启动
- HKLM\SYSTEM\CurrentControlSet\Services — 服务/驱动
- HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs — 最近文档
- SAM数据库 — 用户信息(需SYSTEM权限)

## 文件系统时间线
```powershell
# 最近7天修改的文件
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue |
  Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) } |
  Select-Object FullName, LastWriteTime, Length |
  Sort-Object LastWriteTime -Descending
```

## 进程分析
```powershell
# 所有网络连接
Get-NetTCPConnection | Where-Object {$_.State -eq 'Established'}

# 进程命令行
Get-CimInstance Win32_Process | Select-Object Name, ProcessId, CommandLine
```

## 用户账户
```powershell
# 本地用户
Get-LocalUser | Select-Object Name, Enabled, LastLogon

# 组成员
Get-LocalGroupMember Administrators
```

## 网络配置
```powershell
# DNS缓存
Get-DnsClientCache

# 防火墙规则
Get-NetFirewallRule | Where-Object {$_.Enabled -eq 'True'} | Format-Table Name, Direction, Action
```

## 已安装软件
```powershell
# 已安装程序
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
  Where-Object {$_.DisplayName} |
  Select-Object DisplayName, Publisher, InstallDate, UninstallString
```
