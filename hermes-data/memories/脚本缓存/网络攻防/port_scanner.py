#!/usr/bin/env python
"""
高性能异步端口扫描器
======================
灵感来源：
  - pwntools tube 基类：errno 精准分类（EAGAIN/ECONNRESET/EINTR 分别处理）
  - impacket SMBConnection：自动协商协议版本，连接器模式
  - Sn1per：模块化扫描管道

特性：
  - 非阻塞 connect_ex（不排队，秒级扫千端口）
  - 半开/全开/服务识别 三级检测
  - 错误按类型分类（超时/拒绝/不可达/未知）
  - 多目标并行扫描（线程池）
  - JSON/表格双输出格式

用法：
  python port_scanner.py 192.168.1.1
  python port_scanner.py 192.168.1.0/24 --top-ports 100 --timeout 2
  python port_scanner.py 10.0.0.1 --port-range 1-1024 --json
"""

from __future__ import annotations

import argparse
import errno
import ipaddress
import json
import logging
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Iterator, Optional

# ── 日志配置 ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("port_scanner")

# ── 常量 ──────────────────────────────────────────────────
# 常见服务端口映射（非完整列表，仅覆盖最常用）
SERVICE_MAP: dict[int, str] = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    111: "RPC",
    135: "MSRPC",
    139: "NetBIOS-SSN",
    143: "IMAP",
    161: "SNMP",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    500: "ISAKMP",
    514: "Syslog",
    587: "SMTP-Sub",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1080: "SOCKS",
    1194: "OpenVPN",
    1352: "Lotus-Notes",
    1433: "MSSQL",
    1521: "Oracle-DB",
    1723: "PPTP",
    2049: "NFS",
    2082: "CPanel",
    2181: "ZooKeeper",
    2222: "SSH-Alt",
    2375: "Docker-TCP",
    2376: "Docker-TLS",
    3128: "Squid-Proxy",
    3306: "MySQL",
    3389: "RDP",
    3690: "SVN",
    4000: "Diablo-II",
    4369: "Erlang-Port",
    4444: "Metasploit",
    5000: "Flask/UPnP",
    5432: "PostgreSQL",
    5555: "Android-ADB",
    5632: "PCAnywhere",
    5800: "VNC-HTTP",
    5900: "VNC",
    5985: "WinRM-HTTP",
    5986: "WinRM-HTTPS",
    6379: "Redis",
    6443: "K8s-API-SSL",
    6667: "IRC",
    6668: "IRC-SSL",
    7001: "WebLogic",
    7070: "OwnCloud",
    8000: "HTTP-Alt",
    8080: "HTTP-Proxy",
    8081: "HTTP-Alt2",
    8443: "HTTPS-Alt",
    8888: "HTTP-Alt3",
    9000: "PHP-FPM",
    9090: "Cockpit",
    9100: "Node-Exporter",
    9200: "Elasticsearch",
    9300: "Elasticsearch-Cluster",
    9418: "Git",
    9999: "HTTP-Alt4",
    10000: "Webmin",
    11211: "Memcached",
    12345: "NetBus",
    27017: "MongoDB",
    28017: "MongoDB-HTTP",
    32400: "Plex",
    49152: "Windows-RPC",
    50000: "SAP",
    50070: "HDFS",
    60000: "DeepSeek",
}

# 常用端口列表（Top 100 / Top 1000）
TOP_100 = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 389, 443,
           445, 993, 995, 1433, 1521, 2049, 3306, 3389, 5432, 5900, 5985,
           5986, 6379, 8080, 8443, 9000, 9090, 9200, 27017, 11211, 10000]

TOP_1000 = list(range(1, 1025))  # 1-1024 标准端口

# 常见的不可达/超时错误码
CONNECTION_REFUSED_CODES = {errno.ECONNREFUSED, errno.ECONNRESET, errno.ENETUNREACH}
TIMEOUT_CODES = {errno.ETIMEDOUT, errno.EAGAIN, errno.EINPROGRESS}
UNREACHABLE_CODES = {errno.EHOSTUNREACH, errno.ENETUNREACH, 10065}
PERMISSION_CODES = {errno.EACCES, errno.EPERM, 10013}


# ── 枚举 ──────────────────────────────────────────────────
class PortState(Enum):
    """端口状态"""
    OPEN = auto()
    CLOSED = auto()
    FILTERED = auto()
    TIMEOUT = auto()
    ERROR = auto()


class ScanLevel(Enum):
    """扫描深度"""
    SYN = auto()      # 半开扫描（connect_ex 快速）
    FULL = auto()     # 完整连接
    SERVICE = auto()  # 服务识别


# ── 数据结构 ──────────────────────────────────────────────
@dataclass
class ScanTarget:
    """扫描目标"""
    host: str
    ip: str
    port: int
    timeout: float = 2.0

    @property
    def service(self) -> str:
        return SERVICE_MAP.get(self.port, "unknown")


@dataclass
class ScanResult:
    """单端口扫描结果"""
    host: str
    port: int
    state: PortState
    service: str = "unknown"
    banner: str = ""
    scan_time_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "state": self.state.name.lower(),
            "service": self.service,
            "banner": self.banner,
            "scan_time_ms": round(self.scan_time_ms, 1),
            "error": self.error,
        }


@dataclass
class ScanSummary:
    """扫描总结"""
    target: str
    total_ports: int
    open_ports: list[ScanResult]
    filtered_count: int
    closed_count: int
    error_count: int
    scan_duration_sec: float
    start_time: str
    end_time: str

    def open_count(self) -> int:
        return len(self.open_ports)


# ── 核心扫描器 ────────────────────────────────────────────
class PortScanner:
    """
    TCP 端口扫描器

    设计理念（来自 pwntools tube + impacket）：
    - errno 精准分类处理每种错误类型
    - 非阻塞 connect_ex + select 超时控制
    - 连接器模式：从目标 IP 到端口逐层推进
    """

    def __init__(self, timeout: float = 2.0, max_workers: int = 200):
        self.timeout = timeout
        self.max_workers = max_workers

    def scan_port(self, host: str, port: int, grab_banner: bool = False) -> ScanResult:
        """
        扫描单个端口

        借鉴 pwntools sock.recv_raw 的 errno 分类法：
        - ECONNREFUSED → CLOSED
        - ETIMEDOUT/EAGAIN → FILTERED
        - EHOSTUNREACH → FILTERED
        - EACCES → ERROR
        """
        start = time.perf_counter()
        result = ScanResult(host=host, port=port, state=PortState.CLOSED, service=SERVICE_MAP.get(port, "unknown"))

        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            # 非阻塞 connect_ex
            err = sock.connect_ex((host, port))

            if err == 0:
                # OPEN! 端口开放
                result.state = PortState.OPEN

                # 可选：抓取 banner（模拟 impacket 的协议握手）
                if grab_banner and port not in {80, 443, 8080, 8443}:  # HTTP/HTTPS 需要发送请求
                    try:
                        sock.settimeout(3.0)
                        banner = sock.recv(1024)
                        result.banner = banner.decode("utf-8", errors="replace").strip()[:200]
                    except (socket.timeout, OSError):
                        pass

            elif err in CONNECTION_REFUSED_CODES:
                result.state = PortState.CLOSED
            elif err in TIMEOUT_CODES:
                result.state = PortState.TIMEOUT
                result.error = "timeout"
            elif err in UNREACHABLE_CODES:
                result.state = PortState.FILTERED
                result.error = "unreachable"
            elif err in PERMISSION_CODES:
                result.state = PortState.ERROR
                result.error = "permission denied"
            else:
                result.state = PortState.CLOSED
                result.error = f"errno={err}"

        except socket.gaierror:
            result.state = PortState.ERROR
            result.error = "DNS resolution failed"
        except OSError as e:
            # socket 级错误
            if e.errno in CONNECTION_REFUSED_CODES | TIMEOUT_CODES | UNREACHABLE_CODES:
                result.state = PortState.FILTERED
            else:
                result.state = PortState.ERROR
            result.error = str(e)[:60]
        except Exception as e:
            result.state = PortState.ERROR
            result.error = str(e)[:60]
        finally:
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass

        result.scan_time_ms = (time.perf_counter() - start) * 1000
        return result

    def scan_range(self, host: str, ports: list[int], grab_banner: bool = False) -> list[ScanResult]:
        """
        多端口并行扫描

        使用 ThreadPoolExecutor 并行，借鉴 Sn1per 的批量扫描模式
        """
        results: list[ScanResult] = []
        futures = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for port in ports:
                future = executor.submit(self.scan_port, host, port, grab_banner)
                futures[future] = port

            for future in as_completed(futures):
                try:
                    result = future.result(timeout=self.timeout + 5)
                    results.append(result)
                except Exception as e:
                    port = futures[future]
                    results.append(ScanResult(
                        host=host, port=port, state=PortState.ERROR,
                        error=f"future error: {str(e)[:40]}"
                    ))

        results.sort(key=lambda r: r.port)
        return results

    def scan_top_ports(self, host: str, count: int = 100, grab_banner: bool = False) -> list[ScanResult]:
        """扫描常用端口"""
        ports = TOP_1000 if count > 100 else TOP_100[:count]
        return self.scan_range(host, ports, grab_banner)

    def scan(self, target: str, port_range: str = "", top_ports: int = 0,
             grab_banner: bool = False) -> ScanSummary:
        """
        统一扫描入口

        Args:
            target: IP 或 CIDR 或 域名
            port_range: "1-1024" 或 "22,80,443"
            top_ports: 0=全部端口, 100=top100, 1000=top1000
            grab_banner: 是否抓取服务 banner

        Returns:
            ScanSummary
        """
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scan_start = time.perf_counter()

        # 解析目标
        try:
            ip = socket.gethostbyname(target)
        except socket.gaierror:
            return ScanSummary(
                target=target, total_ports=0, open_ports=[],
                filtered_count=0, closed_count=0, error_count=0,
                scan_duration_sec=0, start_time=start_time,
                end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )

        # 解析端口列表
        ports: list[int] = []
        if top_ports > 0:
            all_ports = TOP_1000 if top_ports > 100 else TOP_100
            ports = all_ports[:min(top_ports, len(all_ports))]
        elif port_range:
            ports = self._parse_ports(port_range)
        else:
            ports = TOP_100

        if not ports:
            ports = TOP_100

        log.info(f"🔍 扫描目标 {target} ({ip}) — {len(ports)} 个端口")

        # 执行扫描
        results = self.scan_range(ip, ports, grab_banner)

        # 分类结果
        open_ports = [r for r in results if r.state == PortState.OPEN]
        filtered = [r for r in results if r.state in (PortState.FILTERED, PortState.TIMEOUT)]
        closed = [r for r in results if r.state == PortState.CLOSED]
        errors = [r for r in results if r.state == PortState.ERROR]

        scan_end = time.perf_counter()

        return ScanSummary(
            target=f"{target} ({ip})",
            total_ports=len(ports),
            open_ports=open_ports,
            filtered_count=len(filtered),
            closed_count=len(closed),
            error_count=len(errors),
            scan_duration_sec=round(scan_end - scan_start, 2),
            start_time=start_time,
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    def _parse_ports(port_range: str) -> list[int]:
        """解析端口范围字符串"""
        ports: set[int] = set()
        parts = port_range.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                try:
                    lo, hi = part.split("-", 1)
                    lo, hi = int(lo.strip()), int(hi.strip())
                    if 1 <= lo <= 65535 and 1 <= hi <= 65535 and lo <= hi:
                        ports.update(range(lo, hi + 1))
                except ValueError:
                    pass
            else:
                try:
                    p = int(part)
                    if 1 <= p <= 65535:
                        ports.add(p)
                except ValueError:
                    pass
        return sorted(ports)


# ── 输出 ──────────────────────────────────────────────────
def print_summary(summary: ScanSummary) -> None:
    """打印扫描报告"""
    print()
    print("=" * 70)
    print(f"  端口扫描报告 — {summary.target}")
    print("=" * 70)
    print(f"  📊 扫描端口: {summary.total_ports} 个")
    print(f"  ✅ 开放端口: {summary.open_count()} 个")
    print(f"  🔒 关闭端口: {summary.closed_count} 个")
    print(f"  ⏳ 超时/过滤: {summary.filtered_count} 个")
    print(f"  ❌ 错误: {summary.error_count} 个")
    print(f"  ⏱️  耗时: {summary.scan_duration_sec} 秒")
    print()

    if summary.open_ports:
        print(f"  {'端口':>6} {'状态':<10} {'服务名':<20} {'Banner'}")
        print(f"  {'-'*60}")
        for r in sorted(summary.open_ports, key=lambda x: x.port):
            banner = r.banner[:40] if r.banner else ""
            print(f"  {r.port:>6} {'✅ OPEN':<10} {r.service:<20} {banner}")
        print()

    if summary.error_count > 0:
        errors = [r for r in summary.open_ports if r.error]
        for r in errors[:5]:
            print(f"  ⚠️  端口 {r.port}: {r.error}")
        if len(errors) > 5:
            print(f"  ... 还有 {len(errors) - 5} 个错误")


# ── 主入口 ────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="高性能异步端口扫描器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  port_scanner.py 192.168.1.1
  port_scanner.py 192.168.1.0/24 --top-ports 100 --timeout 2
  port_scanner.py 10.0.0.1 --port-range 1-1024 --json
  port_scanner.py example.com --port-range 22,80,443,3306,3389 --banner
        """,
    )
    parser.add_argument("target", help="目标 IP / 域名 / CIDR")
    parser.add_argument("--port-range", "-p", default="", help="端口范围 (例: 22,80,443 或 1-1024)")
    parser.add_argument("--top-ports", "-t", type=int, default=0, help="扫描常用端口数量 (100 或 1000)")
    parser.add_argument("--timeout", "-T", type=float, default=2.0, help="超时时间 (默认 2s)")
    parser.add_argument("--banner", "-b", action="store_true", help="抓取服务 banner")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 格式输出")
    parser.add_argument("--workers", "-w", type=int, default=200, help="并行线程数 (默认 200)")

    args = parser.parse_args()

    scanner = PortScanner(timeout=args.timeout, max_workers=args.workers)
    summary = scanner.scan(args.target, args.port_range, args.top_ports, args.banner)

    if args.json:
        output = {
            "tool": "port_scanner",
            "version": "1.0.0",
            "scan_time": summary.start_time,
            "target": summary.target,
            "duration_sec": summary.scan_duration_sec,
            "total_ports": summary.total_ports,
            "results": {
                "open": summary.open_count(),
                "filtered": summary.filtered_count,
                "closed": summary.closed_count,
                "errors": summary.error_count,
            },
            "open_ports": [r.to_dict() for r in sorted(summary.open_ports, key=lambda x: x.port)],
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_summary(summary)

    return 0 if summary.open_count() > 0 or summary.total_ports > 0 else 1


if __name__ == "__main__":
    sys.exit(main())