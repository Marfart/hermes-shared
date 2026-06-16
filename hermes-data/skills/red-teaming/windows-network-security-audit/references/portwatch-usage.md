# PortWatch — Port Scanner + Monitor Reference

## Command Reference

```
usage: portwatch.py <command|url> [host] [ports] [options]

Commands:
  scan <host> <ports>       One-shot port scan
  watch <host> <ports>      Continuous monitoring (--once for single)
  http[s]://URL             HTTP service health check
  status                    Show scan history from state file
```

### Port Range Syntax

| Format | Example | Result |
|--------|---------|--------|
| Single | `22` | Port 22 only |
| List | `22,80,443` | Three ports |
| Range | `1-1024` | 1024 ports |
| Mixed | `22,80,443,8080-8090` | List + range |

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--interval`, `-i` | 60 | Watch interval in seconds |
| `--threads`, `-t` | 200 | Concurrent scan threads |
| `--timeout` | 2.0 | Per-port timeout in seconds |
| `--once` | false | Single scan, no continuous loop |

## Built-in Service Map (30+ ports)

```
21=FTP, 22=SSH, 23=Telnet, 25=SMTP, 53=DNS,
80=HTTP, 110=POP3, 135=RPC, 139=NetBIOS, 143=IMAP,
443=HTTPS, 445=SMB, 465=SMTPS, 587=SMTP, 993=IMAPS,
995=POP3S, 1433=MSSQL, 1521=Oracle, 2049=NFS,
3306=MySQL, 3389=RDP, 5432=PostgreSQL, 5900=VNC,
5985=WinRM-HTTPS, 5986=WinRM-HTTPS, 6379=Redis,
8080=HTTP-Ait, 8443=HTTPS-Alt, 27017=MongoDB
```

## High-Risk Ports (Flagged ⚠️)

| Port | Service | Risk |
|------|---------|------|
| 21 | FTP | Clear text credentials |
| 23 | Telnet | Clear text protocol |
| 135 | RPC | Remote code execution vector |
| 139 | NetBIOS | Legacy Windows sharing |
| 445 | SMB | EternalBlue, ransomware vector |
| 3389 | RDP | Brute-force target |
| 5900 | VNC | Often default/no password |
| 5985 | WinRM-HTTP | Clear text management |
| 5986 | WinRM-HTTPS | Management interface |

## State File Format

**Location:** `~/AppData/Local/hermes/memories/scripts_cache/portwatch_state.json`

```json
{
  "localhost": {
    "host": "localhost",
    "ports": {
      "22": {"port": 22, "service": "SSH", "state": "closed", "first_seen": "...", "last_seen": "..."},
      "80": {"port": 80, "service": "HTTP", "state": "open", "first_seen": "...", "last_seen": "..."},
      "443": {"port": 443, "service": "HTTPS", "state": "open", "first_seen": "...", "last_seen": "..."}
    },
    "last_scan": "2026-06-07T17:55:53.550079",
    "unreachable": false
  }
}
```

## Change Detection Logic

When running `watch` mode, PortWatch compares current scan against state file:

- **🟢 New port** — Was closed/absent before, now open → alert
- **🔴 Closed port** — Was open before, now closed → alert
- **No change** — Silent output (designed for cron-friendly operation)

## HTTP Monitor

The `http://` mode is a separate function for web service availability:

```bash
# Quick one-shot
python portwatch.py http://example.com --once

# Continuous check every 30 seconds
python portwatch.py http://example.com -i 30
```

Output format:
```
[17:54:37] ✅ http://127.0.0.1:5001/ → 200 (35ms)
[17:55:07] ❌ http://127.0.0.1:5001/ → Connection refused
```

## Practical Usage Scenarios

### BLIIoT Gateway Security Audit
```bash
# Scan all ports on a deployed gateway
python portwatch.py scan 192.168.1.100 1-65535 --threads 100 --timeout 1

# Watch critical management ports
python portwatch.py watch 192.168.1.100 22,80,443,8080,8443,3389 --interval 300
```

### Internal Network Discovery
```bash
python portwatch.py scan 10.0.0.1 22,80,443,445,3389,8080 --threads 50
python portwatch.py status
```