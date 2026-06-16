# hashcat v6.2.6 — Windows Install & Usage

## Overview

hashcat is the world's fastest password recovery tool, supporting GPU-accelerated (OpenCL/CUDA) cracking for 320+ hash types including WPA/WPA2 (mode 2500/22000), MD5, SHA1, NTLM, bcrypt, and more.

## Quick Install

```bash
# 1. Create tools dir
mkdir -p /c/Users/Admin/Tools/hashcat

# 2. Download hashcat (v6.2.6, ~20MB .7z archive)
#    Use --noproxy "*" to bypass Vortex proxy (known to stall large downloads)
curl --noproxy "*" -L -o /tmp/hashcat.7z \
  "https://hashcat.net/files/hashcat-6.2.6.7z"
#    Alternative: GitHub release
#  https://github.com/hashcat/hashcat/releases/download/v6.2.6/hashcat-6.2.6.7z

# 3. Download 7zr.exe for extraction (577KB standalone 7-Zip extractor)
curl --noproxy "*" -L -o /tmp/7zr.exe \
  "https://github.com/ip7z/7zip/releases/download/24.08/7zr.exe"

# 4. Extract hashcat
chmod +x /tmp/7zr.exe
/tmp/7zr.exe x /tmp/hashcat.7z -o/c/Users/Admin/Tools/hashcat/ -y

# 5. Flatten directory (hashcat unpacks into hashcat-6.2.6/)
cp -r /c/Users/Admin/Tools/hashcat/hashcat-6.2.6/* /c/Users/Admin/Tools/hashcat/
rm -rf /c/Users/Admin/Tools/hashcat/hashcat-6.2.6/

# 6. Add to PATH
echo 'export PATH=$PATH:/c/Users/Admin/Tools/hashcat' >> ~/.bashrc
source ~/.bashrc
```

## Critical: Running hashcat on Windows

**hashcat MUST be run from its own directory.** The OpenCL runtime path is resolved relative to the executable.

```bash
# ✅ DO THIS — run from hashcat dir
cd /c/Users/Admin/Tools/hashcat && hashcat -I

# ❌ DON'T DO THIS — fails with "./OpenCL/: No such file or directory"
hashcat -I          # fails!
cd /somewhere && hashcat -I   # also fails!
```

## Verify Installation

### Check GPU detection
```bash
cd /c/Users/Admin/Tools/hashcat && hashcat -I
```
Expected output includes OpenCL devices. On this laptop: **Intel UHD Graphics 630** (OpenCL 3.0).

### Run a benchmark
```bash
cd /c/Users/Admin/Tools/hashcat && hashcat -b --benchmark-all
```

### Test crack a known hash
```bash
# Create demo: SHA256 of known password
echo -n "wifi12345" | md5sum | cut -d' ' -f1 > /tmp/demo_hash.txt

# Dictionary with the password
cat > /tmp/demo_dict.txt << 'EOF'
admin
12345678
password
welcome
wifi12345
abcdefg
EOF

# Crack it
cd /c/Users/Admin/Tools/hashcat && hashcat -m 0 /tmp/demo_hash.txt /tmp/demo_dict.txt --force
# Expected: f8ee34fa2fe8f95075eb69cc177498ee:wifi12345
```

## Proxy Issues During Download

The Vortex proxy (`127.0.0.1:7897`) is unreliable for large file downloads. Symptoms:
- Curl stalls at 0 bytes for 30+ seconds
- Speed drops to 23 KB/s (vs. expected multi-MB/s)
- Connection resets mid-download

**Fix:** Always use `--noproxy "*"` with curl for raw downloads from GitHub / hashcat.net.

```bash
# With proxy bypass
curl --noproxy "*" -L -o output.zip "https://..."
```

## GPU Acceleration

hashcat auto-detects OpenCL devices at runtime. This laptop's GPU:

| Device | Type | OpenCL | Memory |
|--------|------|--------|--------|
| Intel UHD Graphics 630 | GPU | OpenCL 3.0 | 6485 MB (1621 MB allocatable) |

**To check available backends:**
```bash
cd /c/Users/Admin/Tools/hashcat && hashcat -I
```

## Usage Examples

### MD5 cracking (mode 0)
```bash
cd /c/Users/Admin/Tools/hashcat
hashcat -m 0 hashes.txt rockyou.txt
hashcat -m 0 hashes.txt --show  # show cracked
```

### WPA/WPA2 WiFi cracking (mode 22000)
```bash
cd /c/Users/Admin/Tools/hashcat
hashcat -m 22000 capture.22000 rockyou.txt
hashcat -m 22000 capture.22000 -a 3 ?d?d?d?d?d?d?d?d?d  # brute force 9-digit
hashcat -m 22000 capture.22000 --show
```

### Dictionary + rules
```bash
cd /c/Users/Admin/Tools/hashcat
hashcat -m 0 hashes.txt rockyou.txt -r rules/best64.rule
```

### NTLM Windows password hashes (mode 1000)
```bash
cd /c/Users/Admin/Tools/hashcat
hashcat -m 1000 ntlm_hashes.txt rockyou.txt
```

## Wordlists

| File | Path | Size |
|------|------|------|
| rockyou.txt | `C:\Users\Admin\Tools\wordlists\rockyou.txt.gz` (rename to .txt, it's not actually gzipped) | ~1.4 billion passwords |
| test_passwords.txt | `C:\Users\Admin\Tools\wordlists\test_passwords.txt` | 20 common passwords |

## Related

- `windows-network-security-audit` — umbrella skill covering the full penetration testing workflow
- WiFi cracking requires a handshake capture first (see SKILL.md "WiFi Cracking on Windows" section)
