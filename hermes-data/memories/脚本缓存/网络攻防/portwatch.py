#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️ PortWatch — 远程端口监控器
实时监控远程主机端口变化，检测新增/关闭端口
支持：多主机、自定义端口、持续监控模式、变化告警

用法：
  python portwatch.py scan localhost 1-1024          # 扫描本地1-1024端口
  python portwatch.py watch localhost 22,80,443,3389  # 持续监控4个端口
  python portwatch.py status                          # 查看当前已知状态
  python portwatch.py http://192.168.1.1:5000         # 监控HTTP服务可用性
"""
import argparse
import json
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── 配置 ─────────────────────────────────────────────
STATE_FILE = Path(os.environ.get("LOCALAPPDATA", "C:\\Users\\Admin\\AppData\\Local")) / "hermes" / "memories" / "scripts_cache" / "portwatch_state.json"
SCAN_TIMEOUT = 2.0       # 单端口超时秒数
MAX_THREADS = 200        # 最大并发线程
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 135: "RPC",
    139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
    465: "SMTPS", 587: "SMTP Submission", 993: "IMAPS",
    995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
    2049: "NFS", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 5900: "VNC", 5985: "WinRM-HTTP",
    5986: "WinRM-HTTPS", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 27017: "MongoDB",
}
HIGH_RISK_PORTS = {21, 23, 135, 139, 445, 3389, 5900, 5985, 5986}


# ── 数据结构 ─────────────────────────────────────────
@dataclass
class PortEntry:
    port: int
    service: str = ""
    state: str = ""        # "open", "closed", "filtered"
    first_seen: str = ""
    last_seen: str = ""
    alert_sent: bool = False

@dataclass
class HostState:
    host: str
    ports: dict[int, PortEntry] = field(default_factory=dict)
    last_scan: str = ""
    unreachable: bool = False


# ── 端口扫描引擎 ─────────────────────────────────────
def resolve_host(host: str) -> Optional[str]:
    """解析hostname，返回IP或None"""
    # 移除http://前缀
    host = host.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None

def check_port(host: str, port: int, timeout: float = SCAN_TIMEOUT) -> tuple[int, str, float]:
    """检查单个端口，返回 (port, state, elapsed_ms)"""
    start = time.perf_counter()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        elapsed = (time.perf_counter() - start) * 1000
        if result == 0:
            service = COMMON_PORTS.get(port, "")
            return (port, "open", round(elapsed, 1))
        else:
            return (port, "closed", round(elapsed, 1))
    except socket.gaierror:
        return (port, "host_unreachable", 0)
    except OSError:
        return (port, "error", 0)
    except Exception:
        return (port, "error", 0)

def parse_ports(port_spec: str) -> list[int]:
    """解析端口范围描述，如 '1-1024' 或 '22,80,443'"""
    ports = []
    for part in port_spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            ports.extend(range(int(a.strip()), int(b.strip()) + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


# ── 状态管理 ─────────────────────────────────────────
def load_state() -> dict[str, dict]:
    """加载持久化状态，返回原始dict（避免dataclass反序列化问题）"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_state(state: dict[str, HostState]) -> None:
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 转换为可序列化格式
    out = {}
    for key, hs in state.items():
        ports_dict = {}
        for port, entry in hs.ports.items():
            ports_dict[str(port)] = asdict(entry)
        out[key] = {
            "host": hs.host,
            "ports": ports_dict,
            "last_scan": hs.last_scan,
            "unreachable": hs.unreachable
        }
    STATE_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 核心扫描功能 ─────────────────────────────────────
def scan_host(host: str, ports: list[int], threads: int = MAX_THREADS,
              timeout: float = SCAN_TIMEOUT, show_progress: bool = True) -> HostState:
    """扫描主机的指定端口列表"""
    ip = resolve_host(host)
    if not ip:
        print(f"❌ 无法解析主机: {host}")
        hs = HostState(host=host, unreachable=True, last_scan=datetime.now().isoformat())
        return hs

    now = datetime.now().isoformat()
    hs = HostState(host=host, last_scan=now, unreachable=False)
    found_ports = []

    print(f"\n🔍 扫描 {host} ({ip}) — {len(ports)} 个端口")
    print(f"{'─' * 50}")

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(check_port, ip, p, timeout): p for p in ports}
        done = 0
        total = len(ports)

        for future in as_completed(futures):
            port, state, elapsed = future.result()
            done += 1

            entry = PortEntry(
                port=port,
                service=COMMON_PORTS.get(port, ""),
                state=state,
                first_seen=now,
                last_seen=now,
            )
            hs.ports[port] = entry

            if state == "open":
                found_ports.append(port)
                risk = " ⚠️" if port in HIGH_RISK_PORTS else ""
                service_str = f" ({COMMON_PORTS[port]})" if port in COMMON_PORTS else ""
                if show_progress:
                    print(f"   ✅ PORT {port:5d}/tcp{service_str}  OPEN  [{elapsed:.0f}ms]{risk}")

            if show_progress and done % 50 == 0:
                pct = done * 100 // total
                print(f"   📊 进度: {done}/{total} ({pct}%) — 已发现 {len(found_ports)} 个开放端口")

    print(f"{'─' * 50}")
    print(f"📊 扫描完成: {len(ports)} 端口, {len(found_ports)} 开放")
    for p in found_ports:
        service = COMMON_PORTS.get(p, "未知")
        risk = " ⚠️ 高风险" if p in HIGH_RISK_PORTS else ""
        print(f"   🔓 端口 {p}  {service}{risk}")

    save_state({host: hs})
    return hs


# ── 变化检测 ─────────────────────────────────────────
def detect_changes(host: str, new_state: HostState) -> list[str]:
    """对比新扫描结果和旧状态，检测变化"""
    old_state_dict = load_state()
    old = old_state_dict.get(host)

    changes = []
    if not old:
        changes.append(f"🆕 首次扫描 {host}")
        return changes

    # 检查以前开着的端口现在关了
    old_ports = old.get("ports", {})
    for port_str, old_entry in old_ports.items():
        port = int(port_str)
        if old_entry.get("state") == "open":
            new_entry = new_state.ports.get(port)
            if not new_entry or new_entry.state != "open":
                service = COMMON_PORTS.get(port, "")
                changes.append(f"🔴 端口关闭: {port} ({service}) — 之前是OPEN, 现在已关闭")

    # 检查新增端口
    for port, entry in new_state.ports.items():
        if entry.state == "open":
            old_entry = old_ports.get(str(port))
            if not old_entry or old_entry.get("state") != "open":
                service = COMMON_PORTS.get(port, "")
                risk = " ⚠️高风险" if port in HIGH_RISK_PORTS else ""
                changes.append(f"🟢 新增端口: {port} ({service}) — 之前没开, 现在开放了{risk}")

    return changes


# ── 持续监控模式 ─────────────────────────────────────
def watch_host(host: str, port_spec: str, interval: int = 60,
               threads: int = 50, once: bool = False):
    """持续监控模式"""
    ports = parse_ports(port_spec)
    ip = resolve_host(host)

    if not ip:
        print(f"❌ 无法解析主机: {host}")
        return

    print(f"\n👁️  PortWatch 持续监控")
    print(f"   目标: {host} ({ip})")
    print(f"   端口: {len(ports)} 个 ({port_spec})")
    print(f"   间隔: {interval}s{' (单次)' if once else ''}")
    print(f"{'=' * 50}")

    # 首次扫描
    scan_result = scan_host(host, ports, threads=threads, show_progress=True)
    changes = detect_changes(host, scan_result)
    if changes:
        for c in changes:
            print(f"   📢 {c}")
    save_state({host: scan_result})

    if once:
        print(f"\n✅ 单次扫描完成")
        return

    # 持续监控循环
    cycle = 1
    while True:
        print(f"\n{'─' * 50}")
        print(f"⏱️  第{cycle}轮监控 ({datetime.now().strftime('%H:%M:%S')})")
        print(f"   等待 {interval}s...")
        time.sleep(interval)

        scan_result = scan_host(host, ports, threads=threads, show_progress=False)
        changes = detect_changes(host, scan_result)

        if changes:
            print(f"\n📢 检测到 {len(changes)} 个变化:")
            for c in changes:
                print(f"   {c}")
            save_state({host: scan_result})
        else:
            print(f"   ✅ 无变化 — {len([p for p in scan_result.ports.values() if p.state == 'open'])} 个端口持续开放")

        save_state({host: scan_result})
        cycle += 1


# ── HTTP服务监控 ──────────────────────────────────────
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def check_http(url: str, timeout: int = 10) -> tuple[bool, int, str]:
    """检查HTTP服务是否可达"""
    try:
        req = Request(url, method="HEAD")
        req.add_header("User-Agent", "PortWatch/1.0")
        resp = urlopen(req, timeout=timeout)
        return (True, resp.status, "OK")
    except HTTPError as e:
        # 4xx/5xx 也算服务活着
        return (True, e.code, f"HTTP {e.code}")
    except URLError as e:
        return (False, 0, f"连接失败: {e.reason}")
    except Exception as e:
        return (False, 0, str(e))

def monitor_http(url: str, interval: int = 30, once: bool = False):
    """HTTP服务可用性监控"""
    print(f"\n🌐 HTTP服务监控: {url}")
    print(f"{'=' * 50}")

    cycle = 0
    while True:
        cycle += 1
        start = time.perf_counter()
        ok, code, msg = check_http(url)
        elapsed = (time.perf_counter() - start) * 1000

        status = "✅" if ok else "❌"
        ts = datetime.now().strftime("%H:%M:%S")
        bar = "█" * int(code / 10) if ok else "░"
        print(f"   [{ts}] {status} {url} → {code} ({elapsed:.0f}ms)")

        if once:
            break
        time.sleep(interval)


# ── CLI ─────────────────────────────────────────────
def show_status():
    """显示当前监控状态"""
    state = load_state()
    if not state:
        print("📭 无历史记录 — 尚未执行过扫描")
        return

    print(f"\n📋 PortWatch 状态 ({len(state)} 台主机)")
    print(f"{'=' * 50}")
    for host, hs in state.items():
        ports = hs.get("ports", {})
        open_ports = [p for p in ports.values() if p.get("state") == "open"]
        risk_ports = [p for p in open_ports if p.get("port") in HIGH_RISK_PORTS]
        print(f"\n🖥️  {host}")
        print(f"   最后扫描: {hs.get('last_scan', '')}")
        print(f"   开放端口: {len(open_ports)} | 高风险: {len(risk_ports)}")
        if open_ports:
            for entry in sorted(open_ports, key=lambda x: x.get("port", 0))[:10]:
                port = entry.get("port", 0)
                service = COMMON_PORTS.get(port, "")
                risk = " ⚠️" if port in HIGH_RISK_PORTS else ""
                print(f"     🔓 {port:5d}  {service}{risk}")
            if len(open_ports) > 10:
                print(f"     ... 还有 {len(open_ports)-10} 个端口")


def main():
    parser = argparse.ArgumentParser(
        description="👁️ PortWatch — 远程端口监控器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 扫描主机端口范围
  python portwatch.py scan 192.168.1.1 1-1024

  # 持续监控关键端口
  python portwatch.py watch 192.168.1.1 22,80,443,3389 --interval 60

  # 单次扫描（不持续）
  python portwatch.py watch localhost 1-100 --once

  # HTTP服务监控
  python portwatch.py http://example.com

  # 查看历史状态
  python portwatch.py status
""")
    parser.add_argument("command", nargs="?", default="status",
                        help="命令: scan/watch/status/URL")
    parser.add_argument("host", nargs="?", help="目标主机")
    parser.add_argument("ports", nargs="?", default="22,80,443,3389,8080",
                        help="端口范围或列表 (例: 1-1024, 22,80,443)")
    parser.add_argument("--interval", "-i", type=int, default=60,
                        help="监控间隔秒数")
    parser.add_argument("--threads", "-t", type=int, default=MAX_THREADS,
                        help="并发线程数")
    parser.add_argument("--timeout", type=float, default=SCAN_TIMEOUT,
                        help="单端口超时秒数")
    parser.add_argument("--once", action="store_true",
                        help="仅扫描一次，不持续监控")

    args = parser.parse_args()

    cmd = args.command

    # HTTP模式
    if cmd.startswith("http://") or cmd.startswith("https://"):
        monitor_http(cmd, interval=args.interval, once=args.once)
        return

    # 命令模式
    if cmd == "status":
        show_status()
    elif cmd == "scan":
        if not args.host:
            print("❌ 需要指定目标主机")
            sys.exit(1)
        ports = parse_ports(args.ports)
        scan_host(args.host, ports, threads=args.threads, timeout=args.timeout)
    elif cmd == "watch":
        if not args.host:
            print("❌ 需要指定目标主机")
            sys.exit(1)
        watch_host(args.host, args.ports, interval=args.interval,
                   threads=args.threads, once=args.once)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()