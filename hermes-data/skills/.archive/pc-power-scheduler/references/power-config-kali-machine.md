# Kali 电脑电源配置记录

> 2026-06-02 验证，Windows 10.0.26200.8457

## powercfg /a 输出

```
此系统上有以下睡眠状态:
    待机 (S3)

此系统上没有以下睡眠状态:
    待机 (S1)    — 系统固件不支持
    待机 (S2)    — 系统固件不支持
    休眠         — 尚未启用休眠
    待机(S0 低电量待机) — 系统固件不支持
    混合睡眠     — 休眠不可用
    快速启动     — 休眠不可用
```

## RTC 唤醒设置

```
电源方案: 381b4222-f694-41f0-9685-ff5bb260df2e (平衡)
子组: 238c9fa8-0aad-41ed-83f4-97be242c8f20 (睡眠)
  设置: bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d (允许使用唤醒定时器)
    索引 000: 禁用
    索引 001: 启用           ← **当前 AC 电源: 已启用**
    索引 002: 仅限重要的唤醒计算器
    当前直流电源设置索引: 0x00000000 (禁用)
```

**结论：** AC 电源下 RTC 唤醒已启用，DC 电池下禁用。正常使用场景（插电）没问题。

## schtasks Hermes_AutoWake 任务示例

```
文件夹: \
主机名:  PS2022MIXSNJQO
任务名:  \Hermes_AutoWake
下次运行时间: 2026-06-04 8:00:00
模式:    就绪
登录状态: 只使用交互方式
要运行的任务: python C:\Users\Admin\AppData\Local\hermes\scripts\wakeup_check.py
计划任务状态: 已启用
电源管理: 在电池模式停止, 不用电池启动
计划类型: 一次性
开始时间: 8:00:00
```

## 验证命令（PowerShell 方式）

```powershell
# 检查电源状态
powercfg /a

# 检查 RTC 唤醒
powercfg /query SCHEME_CURRENT SUB_SLEEP RTCWAKE

# 查看已注册的唤醒定时器
powercfg /waketimers

# 查看 Hermes 唤醒任务
schtasks /query /tn Hermes_AutoWake /fo LIST /v

# 删除任务
schtasks /delete /tn Hermes_AutoWake /f

# 创建任务
schtasks /create /tn Hermes_AutoWake /tr "python C:\Users\Admin\AppData\Local\hermes\scripts\wakeup_check.py" /sc once /st 08:00 /sd 2026/06/03 /f
```

## 启动文件夹内容

```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
├── CuaDriver.lnk
├── Hermes_Gateway.cmd          ← Hermes 启动
├── Hermes_Live_Sync_Startup.cmd  ← 实时同步守护
└── Hermes_Sync_Startup.cmd     ← 旧版同步（可能已废弃）
```

## Registry 自启项

```
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
├── WXWork
├── TradeMessenger2.0
├── org.openvpn.client
├── doubao
├── BingSvc
├── YoudaoDict
├── BaiduYunDetect
├── BaiduYunGuanjia
├── cloudmusic
├── Listary
├── Teams
├── GoogleDriveFS
├── electron.app.比心云
├── CC Switch
├── Spotify
├── Grammarly
├── MicrosoftEdgeAutoLaunch_...
```