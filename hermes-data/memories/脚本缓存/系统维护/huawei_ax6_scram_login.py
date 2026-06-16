#!/usr/bin/env python3
"""
华为AX6 SCRAM完整认证登录
步骤：
  1. POST /api/system/user_login → 拿SCRAM salt + iter
  2. 用SCRAM算法计算密码证明
  3. 发送证明完成登录
"""

import json, hashlib, hmac, base64, urllib.request, urllib.error, sys

IP = "192.168.1.1"

def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()

def get_json(url: str, data: bytes = None) -> dict:
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    try:
        resp = urllib.request.urlopen(
            urllib.request.Request(url, data=data, headers=headers), timeout=8)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("=" * 60)
print("🔐 华为AX6 SCRAM 完整认证")
print("=" * 60)

# ── Step 1: 获取CSRF ──────────────────────────────────────
print("\n📡 Step 1: 获取CSRF Token...")
cs = get_json(f"http://{IP}/api/system/deviceinfo")
cs_p = cs.get("csrf_param", "")
cs_t = cs.get("csrf_token", "")
print(f"    csrf_param: {cs_p[:25]}...")
print(f"    csrf_token: {cs_t[:25]}...")

# ── Step 2: 提交初始登录（获得SCRAM参数） ──────────────────
print("\n🔑 Step 2: 提交SHA256密码（获取SCRAM参数）...")
pwd_hash = hashlib.sha256(b"admin").hexdigest().upper()

body = json.dumps({
    "UserName": "admin",
    "Password": pwd_hash,
    "csrf": {"csrf_param": cs_p, "csrf_token": cs_t}
}).encode()

scram_resp = get_json(f"http://{IP}/api/system/user_login", body)
print(f"    响应: {json.dumps(scram_resp, ensure_ascii=False)[:200]}")

ec = scram_resp.get("errorCategory", "")
if ec == "change_to_scram":
    print("    ✅ 密码正确！需要完成SCRAM握手")
    
    # SCRAM握手参数
    scram_cs_p = scram_resp.get("csrf_param", "")
    scram_cs_t = scram_resp.get("csrf_token", "")
    
    # 这些csrf参数很可能包含SCRAM的salt信息
    # 华为的SCRAM通常: csrf_param = salt, csrf_token = 服务器第一次消息
    
    # ── Step 3: SCRAM客户端第一次消息 ─────────────────────
    print("\n🔄 Step 3: 发送SCRAM客户端证明...")
    
    # SCRAM-SHA-256
    password = "admin"
    salt = scram_cs_p.encode()  # csrf_param可能是salt
    iterations = 4096  # 华为常用迭代次数
    
    # SaltedPassword = Hi(password, salt, iterations)
    # ClientKey = HMAC(SaltedPassword, "Client Key")
    # StoredKey = SHA256(ClientKey)
    # AuthMessage = client_first_bare + "," + server_first + "," + client_final_without_proof
    # ClientSignature = HMAC(StoredKey, AuthMessage)
    # ClientProof = ClientKey XOR ClientSignature
    
    salted = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    print(f"    SaltedPassword: {b64(salted)[:30]}...")
    
    client_key = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
    stored_key = hashlib.sha256(client_key).digest()
    
    # 构建认证消息
    c_nonce = scram_cs_t[:16]  # 取部分token作为client nonce
    client_first = f"n,,n=admin,r={c_nonce}"
    server_first = f"r={c_nonce},s={b64(salt)},i={iterations}"
    client_final_no_proof = f"c=biws,r={c_nonce}"
    auth_msg = f"{client_first},{server_first},{client_final_no_proof}"
    
    client_sig = hmac.new(stored_key, auth_msg.encode(), hashlib.sha256).digest()
    client_proof = bytes(a ^ b for a, b in zip(client_key, client_sig))
    
    # ── Step 4: 发送SCRAM最终消息 ─────────────────────────
    scram_final = json.dumps({
        "UserName": "admin",
        "Password": b64(salted),  # SaltedPassword
        "Proof": b64(client_proof),
        "StoredKey": b64(stored_key),
        "AuthMessage": auth_msg,
        "csrf": {"csrf_param": scram_cs_p, "csrf_token": scram_cs_t}
    }).encode()
    
    final_resp = get_json(f"http://{IP}/api/system/user_login", scram_final)
    print(f"    SCRAM最终响应: {json.dumps(final_resp, ensure_ascii=False)[:300]}")
    
    if "error" not in str(final_resp).lower() or "errcode" not in str(final_resp).lower():
        print(f"\n{'='*60}")
        print("🎉 完整SCRAM登录成功！！！")
        print(f"{'='*60}")
        print(f"   路由器: 华为AX6 (192.168.1.1)")
        print(f"   用户名: admin")
        print(f"   密码:   admin")
        print(f"{'='*60}")
    else:
        print("\n⚠️ SCRAM未完成，试试其他salt组合...")
        
        # 也试试csrf_token作为salt
        print("\n🔄 Step 3b: 用csrf_token做salt重试...")
        salt2 = scram_cs_t.encode()
        salted2 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt2, 4096)
        
        body_alt = json.dumps({
            "UserName": "admin",
            "Password": b64(salted2),
            "csrf": {"csrf_param": scram_cs_p, "csrf_token": scram_cs_t}
        }).encode()
        
        alt_resp = get_json(f"http://{IP}/api/system/user_login", body_alt)
        print(f"    响应: {json.dumps(alt_resp, ensure_ascii=False)[:200]}")
        
        # 也试试用原始的csrf_param作为salt
        print("\n🔄 Step 3c: 用原始csrf_param做salt重试...")
        salt3 = cs_p.encode()
        salted3 = hashlib.pbkdf2_hmac("sha256", password.encode(), salt3, 4096)
        
        body_alt2 = json.dumps({
            "UserName": "admin",
            "Password": b64(salted3),
            "csrf": {"csrf_param": scram_cs_p, "csrf_token": scram_cs_t}
        }).encode()
        
        alt_resp2 = get_json(f"http://{IP}/api/system/user_login", body_alt2)
        print(f"    响应: {json.dumps(alt_resp2, ensure_ascii=False)[:200]}")

elif "error" in str(scram_resp).lower() or "errcode" in str(scram_resp).lower():
    print("\n❌ SHA256密码验证失败 - 密码不是admin？")
    print(f"   试试其他常见密码...")
else:
    print(f"\n🎉 直接登录成功！")
    print(f"   用户: admin")
    print(f"   密码: admin")