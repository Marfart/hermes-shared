#!/usr/bin/env python3
"""HTTP登录靶场 — 用于Hydra暴力破解测试"""
from flask import Flask, request, render_template_string
import hmac

app = Flask(__name__)

# 硬编码用户密码（已知的）
USERS = {
    "admin": "P@ssw0rd!",
    "kali": "hunter2",
    "manager": "Welcome2024",
    "root": "toor1234!",
    "test": "test123",
}

HTML_FORM = """<!DOCTYPE html>
<html><body>
<h2>🔐 登录</h2>
<form method="POST">
  <label>用户名: <input type="text" name="username"></label><br>
  <label>密码: <input type="password" name="password"></label><br>
  <input type="submit" value="登录">
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
            return f"✅ 登录成功！token: user-{u}-{{0f3a7b91-{hash(u) % 10000:04d}}}"
        return render_template_string(HTML_FORM, msg="❌ 用户名或密码错误")
    return render_template_string(HTML_FORM, msg="")

if __name__ == "__main__":
    print(f"靶场启动: http://127.0.0.1:5001")
    print(f"账户: {list(USERS.keys())}")
    app.run(host="0.0.0.0", port=5001, debug=False)