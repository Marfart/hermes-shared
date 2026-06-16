# Weixin iLink SSL Certificate Chain

## Certificate Info (as of 2026-06-02)

| Field | Value |
|-------|-------|
| Host | `ilinkai.weixin.qq.com:443` |
| Issuer (full) | `CN=DigiCert Secure Site OV G2 TLS CN RSA4096 SHA256 2022 CA1, O=DigiCert\, Inc., C=US` |
| Subject | Tencent / iLink server cert (masked by CDN) |
| Client OS | Windows 10, git-bash Python 3.11 |

## Known Failure Mode

```
SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]
  certificate verify failed: self-signed certificate in certificate chain
```

The `certifi` Mozilla CA bundle at `%LOCALAPPDATA%/hermes/hermes-agent/venv/Lib/site-packages/certifi/cacert.pem` may lag behind Tencent's certificate renewal cycle. Upgrading resolves it.

## Repair Command

From Hermes' venv (not system Python):

```bash
"$LOCALAPPDATA/hermes/hermes-agent/venv/Scripts/pip" install --upgrade certifi
```

Or from within watchdog code:

```python
subprocess.run([pip_path, "install", "--upgrade", "certifi"],
               capture_output=True, timeout=30)
```

## Diagnosis Steps

1. Check if TLS works with verification OFF:
   ```python
   ctx = ssl.create_default_context()
   ctx.check_hostname = False
   ctx.verify_mode = ssl.CERT_NONE
   sock = socket.create_connection((host, 443), timeout=8)
   ssock = ctx.wrap_socket(sock, server_hostname=host)
   # If this succeeds but create_default_context(cafile=certifi.where()) fails,
   # it's a CA bundle issue.
   ```

2. Check which CA issued the cert:
   ```python
   from cryptography import x509
   from cryptography.hazmat.backends import default_backend
   cert_der = ssock.getpeercert(binary_form=True)
   cert_obj = x509.load_der_x509_certificate(cert_der, default_backend())
   print(cert_obj.issuer.rfc4514_string())
   ```

3. Check `certifi` CA bundle size:
   ```python
   import certifi, ssl
   ctx = ssl.create_default_context(cafile=certifi.where())
   print(len(ctx.get_ca_certs()))  # Should be ~137
   ```