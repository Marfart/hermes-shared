# Non-Elevated Forensics Quick Checklist

Use this when user asks "有人动过我电脑吗？" — **no admin elevation required**.

## Order of Checks (fastest → slowest)

1. **Uptime** → was it rebooted?
2. **Desktop file timestamps** → strongest evidence of user activity pattern
3. **Network connections** → any external IPs?
4. **Remote software processes** → TeamViewer/AnyDesk/VNC/GV running?
5. **Startup registry** → new autoruns added?
6. **Chrome data timestamps** → Chrome/History file modification time
7. **Guard/watchdog state** → if deployed, check for alerts

## Gotchas

- **Chrome History DB locked**: When Chrome is running, copying `History` file fails with "file in use". Skip it or close Chrome first.
- **wevtutil from non-elevated**: Returns zero events for Security/System logs with complex XML queries. Use the quick checks instead — they cover 90% of cases.
- **query session / qwinsta**: Not available from git-bash MSYS ("command not found"). Use tasklist+netstat+desktop timestamps as proxy.
- **process list**: PowerShell `where-object` with complex filtering works fine, but `tasklist` via subprocess in Python is simpler.
- **Desktop path normalization**: In git-bash, use `/c/Users/Admin/Desktop` or `os.path.expanduser('~/Desktop')` in Python.
- **GameViewer logs**: Located at `~/Desktop/规格书/GameViewer/log/`. Empty log files = no remote sessions recorded.

## When to Escalate to Elevated

Only if quick checks show:
- Desktop files modified **outside user's known working hours**
- Unknown files appeared on Desktop
- Network connection to external IP
- Remote software process found running
- New startup item appeared
- User explicitly says "我昨晚没开电脑" but boot time says otherwise

Then proceed to the elevated PowerShell forensics in the main SKILL.md.