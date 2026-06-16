# Hydra Native Install on Windows (THC-Hydra)

## Overview

THC-Hydra v9.0 pre-compiled Windows binary from [maaaaz/thc-hydra-windows](https://github.com/maaaaz/thc-hydra-windows). Supports SSH, MySQL, PostgreSQL, RDP, LDAP, HTTP form, HTTP GET, and 50+ other protocols via embedded Cygwin DLLs.

## Quick Install

```bash
# 1. Create tools dir
mkdir -p /c/Users/Admin/Tools/hydra/v9.0

# 2. Download v9.0 (v9.1 zip is corrupt on GitHub — 8.25MB all zeros)
curl -L -o "/c/Users/Admin/Tools/hydra/thc-hydra-v9.0.zip" \
  "https://github.com/maaaaz/thc-hydra-windows/releases/download/v9.0/thc-hydra-windows-v9.0.zip"

# 3. Extract (use Python, not git-bash unzip which has permission issues)
python -c "
import zipfile
zf_path = r'C:\Users\Admin\Tools\hydra\thc-hydra-v9.0.zip'
extract_to = r'C:\Users\Admin\Tools\hydra\v9.0'
with zipfile.ZipFile(zf_path) as zf:
    zf.extractall(extract_to)
"

# 4. Add to PATH
echo 'export PATH="\$PATH:/c/Users/Admin/Tools/hydra/v9.0"' >> ~/.bashrc
source ~/.bashrc
```

## Files (v9.0, ~5.2MB)

| File | Size | Purpose |
|------|------|---------|
| `hydra.exe` | 428 KB | Main brute-force engine |
| `pw-inspector.exe` | 50 KB | Password quality checker |
| `cygwin1.dll` + 15 DLLs | ~4.7 MB | Cygwin runtime + protocol modules |

## Protocols Available

- **SSH** (via libssh)
- **MySQL** (via libmysqlclient)
- **PostgreSQL** (via libpq)
- **LDAP** (via libldap)
- **HTTP** form/GET (built-in)
- **RDP, FTP, Telnet, SMTP, POP3, IMAP, SMB** and 50+ more

## Verify

```bash
hydra.exe -h
# → Hydra v9.0 (c) 2019 by van Hauser/THC
```

## Known Issues

### 1. v9.1 zip is corrupt (June 2026)
The `thc-hydra-windows-v9.1.zip` on GitHub's release page consistently downloads as 8,255,073 bytes of all zeros. All methods fail:
- PowerShell `Expand-Archive` — IOException "file is potentially corrupted"
- .NET `ZipFile.OpenRead` — same
- Python `zipfile.ZipFile` — Errno 22
- 7-Zip — access denied

**Fix:** Use v9.0 instead (5,454,455 bytes, valid PK zip header).

### 2. git-bash file permissions
Files downloaded via `curl -o` in git-bash may be created without read permission for the user. Symptom: `ls -la` shows the file but `unzip` or `xxd` says "Permission denied". **Fix:** Use `chmod +r <file>` or extract via Python's `zipfile` module.

### 3. git-bash /tmp vs Windows TEMP
git-bash's `/tmp` maps to `C:\Users\<user>\AppData\Local\Temp`, while Windows Python's `os.environ['TEMP']` points to the same directory. Files in `/tmp` are visible to Windows Python via the full path.

### 4. VC++ 2008 Redistributable
Required per README, but v9.0 seems to work without it on Windows 10. If hydra.exe fails with a missing DLL error, install from: https://www.microsoft.com/en-us/download/details.aspx?id=26368

## Usage Examples

```bash
# Single target, single user, password list
hydra.exe -l admin -P passwords.txt target.com ssh

# Multiple targets from file
hydra.exe -L users.txt -P rockyou.txt -M targets.txt http-post-form "/login:user=^USER^&pass=^PASS^:F=error"

# Restore crashed session
hydra.exe -R

# Service-specific modules
hydra.exe -U http-post-form  # show module options
```
