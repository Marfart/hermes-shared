# Weixin Disconnect Root Cause Analysis

Investigation conducted 2026-06-02 from gateway.log / errors.log traces.

## Investigation Methodology

When a user reports "微信断联" (WeChat disconnected), follow these steps:

### 1. Read the logs

```bash
# Gateway log — connection status changes, poll errors, send failures
grep -i "weixin\|ilink\|rate.limit" ~/AppData/Local/hermes/logs/gateway.log | tail -40

# Error log — full tracebacks and SSL errors
grep -i "ssl\|cert\|ilink\|weixin\|rate.limit" ~/AppData/Local/hermes/logs/errors.log | tail -40

# Gateway stdio — raw iLink API errors
grep -i "weixin\|ilink" ~/AppData/Local/hermes/logs/gateway-stdio.log | tail -40
```

### 2. Check live connectivity

```python
import ssl, socket
ctx = ssl.create_default_context()
ctx.check_hostname = True
ctx.verify_mode = ssl.CERT_REQUIRED
sock = socket.create_connection(("ilinkai.weixin.qq.com", 443), timeout=8)
ssock = ctx.wrap_socket(sock, server_hostname="ilinkai.weixin.qq.com")
ssock.close()
```

### 3. Distinguish root causes

| Symptom | Likely Cause |
|---------|-------------|
| Single platform down | Platform-specific (Weixin token/session, TG protocol err) |
| Multiple platforms down at same timestamp | Network-level (DNS flapping, proxy drop, routing glitch) |
| SSL verify fail but TLS works | Certifi/system CA bundle outdated |
| Rate-limited only during cron | Multiple cron jobs firing simultaneously |
| "Server disconnected" | iLink server-side connection reset (transient) |

### 4. Check the cert

```python
import ssl, socket
from cryptography import x509
from cryptography.hazmat.backends import default_backend

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
sock = socket.create_connection(("ilinkai.weixin.qq.com", 443), timeout=10)
ssock = ctx.wrap_socket(sock, server_hostname="ilinkai.weixin.qq.com")
cert_der = ssock.getpeercert(binary_form=True)
cert = x509.load_der_x509_certificate(cert_der, default_backend())
print("Issuer:", cert.issuer.rfc4514_string())
```

## Root Causes Found

### 1. Host network blip (most frequent, ~3-5x/day)
- **Pattern:** Telegram + Weixin + Discord all disconnect within the same 1-2 second window
- **Log:** `[Weixin] poll error (1/3): Cannot connect to host ilinkai.weixin.qq.com:443 ssl:default [None]`
- **Log (alternate):** `[Weixin] poll error (1/3): Server disconnected` (connection-side reset)
- **Resolution:** `ipconfig /flushdns` + 1s wait works immediately ~90% of the time
- **Evidence:** After flush, `check_https()` succeeds instantly
- **Root mechanism:** Windows DNS resolver flapping / routing glitch. `ping 8.8.8.8` works fine, but DNS/name resolution drops briefly. Flush fixes.

### 2. SSL certificate verification failure (~1-2x/day)
- **Pattern:** Only Weixin affected, SSL verify fails but TCP/TLS handshake succeeds
- **Log:** `SSLCertVerificationError: (1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain (_ssl.c:1016)')`
- **Cert chain:** `CN=DigiCert Secure Site OV G2 TLS CN RSA4096 SHA256 2022 CA1,O=DigiCert\, Inc.,C=US`
- **Resolution:** `pip install --upgrade certifi` refreshes the Mozilla CA bundle
- **Verification:** `certifi` package at `venv\Lib\site-packages\certifi\cacert.pem` (137 CA certs in bundle)
- **Diagnostic:** Disable SSL verify temporarily to distinguish SSL issue from network:
  ```python
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE  # TLS works → SSL cert issue, not network
  ```

### 3. iLink rate limiting from cron bursts
- **Pattern:** Multiple cron jobs fire around the same time (daily-update 12:00, finance 08:30, evolution 10:00)
- **Log:** `iLink sendmessage rate limited: ret=-2 errcode=None errmsg=rate limited` repeated 4x with 3s backoff
- **Resolution:** No action needed — wait 30-60s, iLink resets the rate limit window
- **Note:** The `_is_stale_session_ret()` function in weixin.py treats `ret=-2 + errmsg="unknown error"` as a stale session, NOT a rate limit — so some -2 errors are session expiry masquerading as rate limits