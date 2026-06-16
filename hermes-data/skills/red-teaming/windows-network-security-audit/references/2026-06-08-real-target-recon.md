# Real Target Reconnaissance Log (2026-06-08)

## Network: 192.168.1.0/24

### Initial Discovery: arp -a

**39 live hosts** found instantly. Key hosts identified by MAC OUI:

| IP | MAC | Vendor | Likely Device |
|----|-----|--------|--------------|
| .1 | 88:81:b9 | Huawei | **AX6 Router (WS8700-10)** |
| .41 | 08:00:27 | VirtualBox | VM (offline) |
| .124 | 00:0c:29 | VMware | **VM with SSH open** |
| .93 | f4:b5:20 | Intel | **This machine (attacker)** |
| .3/.9/.38/.51/.68/.96/.112/.113/.115/.131/.134/.135/.179/.213/.222/.229 | 00:e0:4c | Realtek | Windows machines with SMB |
| .172 | d0:ad:08 | Unconfirmed | **Synology NAS "BliiotData"** (Telnet + SSH + HTTP) |

---

## Target 1: Huawei AX6 Router (WS8700-10)

**IP:** 192.168.1.1  
**MAC:** 88:81:B9:4F:12:C2

### Open Ports
- 53/tcp — DNS (tcpwrapped)
- 80/tcp — HTTP (Huawei web UI)
- 443/tcp — HTTPS (HSTS, CSP headers)

### Unauthenticated Endpoints

```
GET /api/system/deviceinfo  → 200 (full device info, CSRF tokens)
GET /api/system/routerstatus → 200 (guide mode, repeater status)
GET /               → 200 (JS-only login page)
```

### /api/system/deviceinfo Exposed Data

```json
{
  "FriendlyName": "华为路由 AX6",
  "DeviceName": "WS8700-10",
  "HardwareVersion": "VER.A",
  "SerialNumber": "02f60da4",
  "UpTime": 2004604,
  "other": { "FirstLogin": 1, "IsNeedSalt": true, "guide": true },
  "csrf_param": "ImefFMQuvo/rOiYCQy5RlPhlSSbosz+e",
  "csrf_token": "j6Dm2dGssD7PPXwhTOnAricRBa6axCRw"
}
```

### Authentication

**SCRAM + RSA:** Password is never sent in plain text. Flow:
1. Login page HTML includes RSA public key in meta tags:
   - `<meta name="n" content="...hex...">` (RSA modulus)
   - `<meta name="e" content="010001">` (RSA exponent)
2. JS library `cat_enc.js.jgz` handles RSA encryption + SCRAM protocol
3. All login attempts with plain password return: `error: 2640003`

### Guide Mode
`/api/system/routerstatus` → `{"guide":true}` means router is in first-time setup wizard, which may have weaker security — worth checking during initial configuration.

### Failed Attacks
- All common passwords via POST to `/api/system/user_login` → error 2640003
- No unauthenticated config/wifi/password endpoints found (404 without session)

---

## Target 2: Synology NAS "BliiotData"

**IP:** 192.168.1.172  
**Web UI:** Port 5000 (DSM) + Port 5001 (HTTPS DSM)

### Open Ports
- 22/tcp — SSH
- 23/tcp — Telnet
- 80/tcp — HTTP (Synology Web Station)
- 443/tcp — HTTPS

### Authentication API

```
POST /webapi/auth.cgi?api=SYNO.API.Auth&version=6&method=login&account=admin&passwd=PASSWORD&session=DiskStation&format=cookie
```

### Error Codes
| Code | Meaning | Action |
|------|---------|--------|
| 400 | Invalid password | Try different password |
| 101 | Rate limited / no permission | Wait before retrying (cooldown needed) |

### Failed Attacks
- Common passwords (admin, 123456, password, etc.) → error 400
- Multiple rapid attempts → error 101 (rate limited)
- Telnet brute force with Hydra unreliable (Hydra's own warning)

---

## Target 3: VMware VM (192.168.1.124)

**MAC:** 00:0C:29:E4:D0:9C (VMware)

### Open Ports
- 22/tcp — SSH (OpenSSH 8.2p1 Ubuntu)

### Failed Attacks
- Common usernames (root, kali, ubuntu, admin, pi, etc.) with top passwords → all failed
- Hydra top 1000 on root took >2 minutes at 62 tries/min (SSH slow due to key exchange overhead)

---

## Target 4: Ubuntu Server (192.168.1.21)

**MAC:** 00:E0:9A:36:85:43 (Realtek)

### Open Ports
- 21/tcp — FTP (vsFTPd 3.0.5)
- 22/tcp — SSH (OpenSSH 8.2p1 Ubuntu)
- 80/tcp — HTTP (Apache2 Ubuntu Default Page)

### Failed Attacks
- Anonymous FTP → rejected (530 Login incorrect)

---

## Other Notable Hosts

| IP | Open Ports | Notes |
|----|-----------|-------|
| .30 | 22, 80, 443 | Web server + SSH |
| .78 | 80, 443, 8080 | HTTP + HTTPS + Proxy |
| .114 | 80, 445, 3389 | Windows with RDP |
| .97 | 445, 3389 | Windows with RDP |
| .15 | 22, 8080 | SSH + Proxy |
| Various | 445 | 13+ machines with SMB open |

---

## Key Lessons

1. **ARP table is the best first step** — 39 hosts revealed in <1s, passively
2. **MAC OUI tells you what it is** — Huawei=88:81:b9, VirtualBox=08:00:27, VMware=00:0c:29
3. **Huawei AX6 has strong auth** — SCRAM+RSA, no bypass found via unauthenticated endpoints
4. **Synopsis NAS rate-limits brute force** — error 101 after ~5 rapid attempts
5. **SSH brute force is slow** — 62 attempts/min with Hydra, better to try targeted passwords first via `sshpass`
6. **Always `--noproxy "*"`** on this machine — proxy blocks local network access
