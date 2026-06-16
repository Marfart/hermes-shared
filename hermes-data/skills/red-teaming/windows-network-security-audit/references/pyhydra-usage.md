# PyHydra — Brute-Force Engine Reference

## Built-in Wordlists

| List Name | Contents | Command Flag |
|-----------|----------|-------------|
| `users` | admin, root, kali, manager, user, test, operator, guest | no `-U` specified |
| `top10` | admin, root, kali, manager, test | `--wordlist users` |
| `passwords` | 15 common passwords | no `-P` specified |
| `demo` | wrong, test, P@ssw0rd!, hunter2 | `-p demo` |

## Custom Wordlist Format

Plain text, one entry per line:
```
# comments are skipped
admin
root
kali
manager
```

## CLI Reference

```
usage: pyhydra.py http-form://target [-h] [-u USER] [-U USERLIST] [-p PASS] [-P PASSLIST]
                                     [-F FAIL] [-S SUCCESS] [-t THREADS] [--delay DELAY]
                                     [--user-field FIELD] [--pass-field FIELD] [--data DATA]
                                     [--no-stop]

positional arguments:
  target          Target URL scheme:
                    http-form://URL    POST form login
                    http-get://URL     GET parameter login
                    ssh://host:port    SSH port check

options:
  -u, --username      Single username
  -U, --userlist      Username dictionary file
  -p, --password      Single password
  -P, --passlist      Password dictionary file
  -F, --fail          Fail keywords (comma-separated)
                      Default: 错误,失败,Error,Invalid,incorrect
  -S, --success       Success keywords (comma-separated)
                      Default: (empty = any non-fail is success)
  -t, --threads       Thread count (default: 4)
  --delay             Request interval in seconds
  --user-field        Username form field name (default: username)
  --pass-field        Password form field name (default: password)
  --data              Extra POST data (key=val&key2=val2)
  --no-stop           Don't stop on first found credential
```

## Response Analysis

### Success Detection
PyHydra checks HTTP response body for keywords:
- **Success keywords** (`-S`): Response must contain at least one
- **Fail keywords** (`-F`): If no `-S` given, response must NOT contain any

### Token/Data Extraction
When a success response contains `token=xxx` or `token: xxx`, it's extracted into the result detail.

## Performance Tuning

| Context | Recommended Threads | Expected Rate |
|---------|-------------------|---------------|
| localhost | 200 | 300+ req/s |
| LAN target | 50-100 | 100-200 req/s |
| Internet target | 10-20 | 20-50 req/s |
| Ratelimited target | 1 + `--delay 1` | 1 req/s |

## Attack Verification

```bash
# Verify target is up
curl -s -o /dev/null -w "%{http_code}" http://target.com/login

# Quick single-user test
python pyhydra.py http-form://target/login -u admin -p test123 -F "Invalid"

# Full sweep with custom keywords
python pyhydra.py http-form://target/login -U users.txt -P rockyou.txt \
  -F "Invalid,incorrect,wrong" -S "Welcome,Dashboard" -t 20
```