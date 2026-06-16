# Test Target Setup for Network Security Testing

## Flask Login Target

A minimal HTTP login form for testing brute-force tools:

```python
from flask import Flask, request, render_template_string
import hmac

app = Flask(__name__)

USERS = {
    "admin": "P@ssw0rd!",
    "kali": "hunter2",
    "manager": "Welcome2024",
    "root": "toor1234!",
    "test": "test123",
}

HTML_FORM = """<!DOCTYPE html><html><body>
<h2>Login</h2>
<form method="POST">
  <label>Username: <input type="text" name="username"></label><br>
  <label>Password: <input type="password" name="password"></label><br>
  <input type="submit" value="Login">
</form>
{% if msg %}<p><strong>{{ msg }}</strong></p>{% endif %}
</body></html>"""

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        real_pw = USERS.get(u)
        if real_pw and hmac.compare_digest(real_pw, p):
            return f"Login OK! token=user-{u}-{hash(u)%10000:04d}"
        return render_template_string(HTML_FORM, msg="Login failed")
    return render_template_string(HTML_FORM, msg="")

if __name__ == "__main__":
    print(f"Target running: http://127.0.0.1:5001")
    print(f"Users: {list(USERS.keys())}")
    app.run(host="0.0.0.0", port=5001, debug=False)
```

## Starting the Target

```bash
# Start in background
python login_target.py &
# or use terminal(background=true)

# Verify
curl -s http://127.0.0.1:5001/
```

## Verifying Login

```bash
# Correct credentials → success token
curl -s -X POST -d "username=admin&password=P@ssw0rd!" http://127.0.0.1:5001/
# Login OK! token=user-admin-{0f3a7b91-5263}

# Wrong credentials → error message
curl -s -X POST -d "username=admin&password=wrong" http://127.0.0.1:5001/
# Login failed
```

## Attacking with PyHydra

```bash
# Full sweep (8 users × 15 passwords = 120 combos)
python pyhydra.py http-form://127.0.0.1:5001/ -F "failed" -S "Login OK"
# → ~0.3s, all 5 valid credentials found

# Chinese keyword match
python pyhydra.py http-form://127.0.0.1:5001/ -F "错误" -S "登录成功"
```

## Port Scan Verification

Cross-check port findings with nmap if installed:

```bash
nmap 127.0.0.1 -p 135,445,5000,5001
```

Expected: 5001 open (Flask target), plus any Windows system ports.

## Port Conflict Note

Windows may use port 5000 for the system process (PID 4). Always use port 5001+ for test targets to avoid conflicts.