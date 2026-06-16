# Guard State Management Reference

## v2 State File Schema

```json
{
  "armed": false,
  "lastBoot": "2026-06-05 12:57:02",
  "knownSessions": ["Admin|2026-06-05 12:57:02"],
  "notifiedBoot": false,
  "notifiedSessions": [],
  "notifiedUnlocks": [],
  "notifiedUSB": [],
  "notifiedRemoteDesktop": [],
  "notifiedWake": [],
  "notifiedRemoteSoftware": false,
  "remoteSoftwareDetected": false,
  "version": 2
}
```

| Field | Type | Description |
|-------|------|-------------|
| `armed` | bool | Guard active? |
| `lastBoot` | string | Last known boot time (`yyyy-MM-dd HH:mm:ss`) |
| `knownSessions` | string[] | Previously seen `User\|timestamp` session IDs |
| `notifiedBoot` | bool | Already sent reboot alert? |
| `notifiedSessions` | string[] | Session IDs already alerted |
| `notifiedUnlocks` | string[] | Screen unlock timestamps already alerted |
| `notifiedUSB` | string[] | USB device serials already alerted |
| `notifiedRemoteDesktop` | string[] | RDP session signatures already alerted |
| `notifiedWake` | string[] | Wake-from-sleep timestamps already alerted |
| `notifiedRemoteSoftware` | bool | Remote software alert already sent |
| `remoteSoftwareDetected` | bool | Currently detecting remote software running |
| `version` | int | Schema version (2) |

## v1 → v2 Migration

When upgrading from v1, add these fields with empty defaults:

```json
{
  "notifiedUnlocks": [],
  "notifiedUSB": [],
  "notifiedRemoteDesktop": [],
  "notifiedWake": [],
  "notifiedRemoteSoftware": false,
  "remoteSoftwareDetected": false
}
```

The PowerShell script auto-creates a v2 state if one doesn't exist. If the file already has v1 schema, the new detection types (3-7) will be missing their `notified*` arrays and the script will crash. **Always check schema version before running.**

## Safe State Writes (Atomic Pattern)

```powershell
$tmp = $StateFile + ".tmp"
$json = $state | ConvertTo-Json -Compress
Set-Content -Path $tmp -Value $json -Encoding UTF8
Move-Item -Path $tmp -Destination $StateFile -Force
```

## Notified List Growth Management

All `notified*` arrays grow unbounded over time. Prune to the last 50 entries on each cron run:

```powershell
foreach ($prop in @('notifiedSessions','notifiedUnlocks','notifiedUSB','notifiedRemoteDesktop','notifiedWake')) {
    if ($state.$prop.Count -gt 50) {
        $state.$prop = @($state.$prop[-50..-1])
    }
}
```

## False Positive Prevention on First Arm

When arming for the first time, ALL currently connected USB devices appear as "new." The arm script should record current USB serials before setting `armed=true`:

```powershell
# During arm, record existing USBs
$existingUSBs = @()
$usbKey = "HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR"
if (Test-Path $usbKey) {
    foreach ($dev in (Get-ChildItem $usbKey)) {
        foreach ($ser in (Get-ChildItem "$usbKey\$($dev.PSChildName)")) {
            $existingUSBs += "usb|$($dev.PSChildName)|$($ser.PSChildName)"
        }
    }
}
$state.notifiedUSB = $existingUSBs
```

## Delivery IDs

From `channel_directory.json`:

```json
{
  "weixin": [
    { "id": "o9cq8...@im.wechat", "type": "dm" }
  ],
  "telegram": [
    { "id": "8314311281", "type": "dm" }
  ]
}
```

Cron `deliver` values:
- WeChat only: `weixin:o9cq8...@im.wechat`
- Telegram only: `telegram:8314311281`
- All channels: `all`
- Origin + all: `origin,all`