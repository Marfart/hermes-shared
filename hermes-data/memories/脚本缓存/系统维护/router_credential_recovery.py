#!/usr/bin/env python3
"""
🔐 路由器密码恢复工具 Router Credential Recovery Tool
═══════════════════════════════════════════════════════

用途：当忘记公司/家庭路由器管理密码时，安全地尝试默认凭据
数据来源：GitHub DefaultCreds-cheat-sheet (3.7k+条) + SecLists

合法用途 ✅：
  1. 路由器背面标签模糊看不清密码 → 查默认凭据
  2. IT管理员忘记密码 → 用默认密码恢复
  3. 拿到"二手"路由器不知道密码 → 试默认组合
  4. 交换机/AP等网络设备密码找回

⚠️ 仅限在自己或授权管理的设备上使用！

用法：
  python router_credential_recovery.py              # 交互式：选品牌试密码
  python router_credential_recovery.py --auto       # 自动扫描所有常见品牌
  python router_credential_recovery.py --brand=tplink  # 指定品牌 TP-Link
  python router_credential_recovery.py --gateway=192.168.1.1  # 指定IP
"""

import os
import sys
import csv
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum, auto

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("router_recovery")

# ── 数据文件路径 ──────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
DEFAULT_CREDS_CSV = SCRIPT_DIR / "DefaultCreds-Cheat-Sheet.csv"
RESULTS_FILE = SCRIPT_DIR / "router_recovery_results.json"


# ── 枚举 ──────────────────────────────────────────────────
class AuthType(Enum):
    """路由器认证方式"""
    BASIC = auto()       # HTTP Basic Auth (最常见)
    DIGEST = auto()      # HTTP Digest
    FORM = auto()        # 表单登录
    UNKNOWN = auto()


class ScanResult(Enum):
    """扫描结果状态"""
    SUCCESS = auto()     # 密码正确
    FAILED = auto()      # 密码错误
    TIMEOUT = auto()     # 连接超时
    BLOCKED = auto()     # 被锁定（多次失败）
    NOT_FOUND = auto()   # 设备不存在


@dataclass
class Credential:
    """一组用户名+密码凭据"""
    username: str
    password: str

    @property
    def is_blank_username(self) -> bool:
        return self.username in ("", "<blank>", "<N/A>", "none")

    @property
    def is_blank_password(self) -> bool:
        return self.password in ("", "<blank>", "<N/A>", "none", "(blank)", "<blank>")

    def as_tuple(self) -> tuple:
        u = "" if self.is_blank_username else self.username
        p = "" if self.is_blank_password else self.password
        return (u, p)


@dataclass
class DeviceInfo:
    """扫描到的设备信息"""
    ip: str
    brand: str
    model: str = ""
    mac: str = ""
    found_credentials: list[Credential] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# 第一关：路由器品牌识别
# ═══════════════════════════════════════════════════════════

# 常见品牌→默认网关→默认凭据映射
ROUTER_BRANDS = {
    "TP-Link": {
        "gateways": ["192.168.1.1", "192.168.0.1", "192.168.0.254"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", "password"),
            Credential("admin", "1234"),
            Credential("admin", ""),
            Credential("root", "admin"),
            Credential("admin", "tp-link"),
        ],
    },
    "Huawei": {
        "gateways": ["192.168.100.1", "192.168.1.1", "192.168.0.1"],
        "common_creds": [
            Credential("root", "admin"),
            Credential("root", "root"),
            Credential("admin", "admin"),
            Credential("telecomadmin", "admintelecom"),
            Credential("admin", ""),
            Credential("root", "huawei"),
        ],
    },
    "H3C": {
        "gateways": ["192.168.1.1", "192.168.0.1", "192.168.1.254"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", "password"),
            Credential("admin", "h3c"),
            Credential("root", "admin"),
            Credential("admin", ""),
        ],
    },
    "MikroTik": {
        "gateways": ["192.168.88.1", "192.168.1.1"],
        "common_creds": [
            Credential("admin", ""),
            Credential("admin", "admin"),
            Credential("root", "root"),
        ],
    },
    "Cisco": {
        "gateways": ["192.168.1.1", "192.168.0.1", "10.0.0.1"],
        "common_creds": [
            Credential("cisco", "cisco"),
            Credential("admin", "cisco"),
            Credential("root", "cisco"),
            Credential("admin", "admin"),
            Credential("cisco", "password"),
        ],
    },
    "ASUS": {
        "gateways": ["192.168.1.1", "192.168.0.1", "192.168.50.1"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", "password"),
            Credential("root", "admin"),
        ],
    },
    "D-Link": {
        "gateways": ["192.168.0.1", "192.168.1.1", "192.168.0.30"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", ""),
            Credential("root", "admin"),
            Credential("Admin", "Admin"),
        ],
    },
    "Tenda": {
        "gateways": ["192.168.0.1", "192.168.1.1", "192.168.2.1"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", ""),
            Credential("admin", "123456"),
            Credential("root", "admin"),
        ],
    },
    "Mercury": {
        "gateways": ["192.168.1.1", "192.168.0.1"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", ""),
            Credential("root", "admin"),
        ],
    },
    "Netgear": {
        "gateways": ["192.168.1.1", "192.168.0.1", "192.168.0.227"],
        "common_creds": [
            Credential("admin", "password"),
            Credential("admin", "1234"),
            Credential("admin", ""),
            Credential("root", "password"),
        ],
    },
    "Xiaomi": {
        "gateways": ["192.168.31.1", "192.168.1.1"],
        "common_creds": [
            Credential("admin", "admin"),
            Credential("admin", ""),
            Credential("root", "admin"),
        ],
    },
}

# 中国公司常见品牌的中英文对照
BRAND_ALIASES = {
    "tplink": "TP-Link",
    "tp-link": "TP-Link",
    "tp link": "TP-Link",
    "tpl": "TP-Link",
    "普联": "TP-Link",
    "huawei": "Huawei",
    "华为": "Huawei",
    "h3c": "H3C",
    "华三": "H3C",
    "cisco": "Cisco",
    "思科": "Cisco",
    "mikrotik": "MikroTik",
    "ros": "MikroTik",
    "asus": "ASUS",
    "华硕": "ASUS",
    "dlink": "D-Link",
    "d-link": "D-Link",
    "友讯": "D-Link",
    "tenda": "Tenda",
    "腾达": "Tenda",
    "mercury": "Mercury",
    "水星": "Mercury",
    "netgear": "Netgear",
    "网件": "Netgear",
    "xiaomi": "Xiaomi",
    "小米": "Xiaomi",
    "mi": "Xiaomi",
}

# ── 通用网关IP检查（如果不知道品牌） ──────────────────────
COMMON_GATEWAYS = [
    "192.168.1.1",     # 绝大多数家用路由器
    "192.168.0.1",     # D-Link / TP-Link 部分型号
    "192.168.0.254",   # TP-Link 部分型号
    "192.168.1.254",   # 华为/H3C 部分型号
    "192.168.100.1",   # 华为光猫/路由器
    "192.168.88.1",    # MikroTik
    "192.168.31.1",    # 小米路由器
    "10.0.0.1",        # 部分企业级路由器
    "10.0.0.2",        # Cisco / Comcast
    "192.168.2.1",     # Tenda / Linksys 部分型号
    "192.168.3.1",     # 部分型号
    "192.168.10.1",    # 企业级
    "172.16.0.1",      # 企业级
]


# ═══════════════════════════════════════════════════════════
# 第二关：加载默认密码数据库
# ═══════════════════════════════════════════════════════════

def load_default_creds(csv_path: str | Path) -> dict[str, list[Credential]]:
    """
    从 DefaultCreds 数据库加载所有已知默认凭据
    
    Args:
        csv_path: DefaultCreds-Cheat-Sheet.csv 文件路径
    
    Returns:
        {品牌名: [Credential, ...]} 字典
    """
    creds_db: dict[str, list[Credential]] = {}
    
    path = Path(csv_path)
    if not path.exists():
        log.warning(f"⚠️ 默认凭据数据库不存在: {csv_path}")
        log.info("💡 脚本会自动使用内置的常见品牌凭据 ~ 够用了！")
        return creds_db
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                brand = row.get("productvendor", "").strip()
                username = row.get("username", "").strip()
                password = row.get("password", "").strip()
                
                if not brand:
                    continue
                    
                # 标准化品牌名
                brand_clean = brand.split("(")[0].strip()
                
                if brand_clean not in creds_db:
                    creds_db[brand_clean] = []
                
                creds_db[brand_clean].append(Credential(username, password))
                count += 1
            
            log.info(f"✅ 已加载 {count} 条默认凭据，覆盖 {len(creds_db)} 个品牌")
    
    except Exception as e:
        log.warning(f"⚠️ 读取默认凭据文件失败: {e}")
    
    return creds_db


def get_creds_for_brand(
    brand: str,
    creds_db: dict[str, list[Credential]],
) -> list[Credential]:
    """
    获取指定品牌的所有可能凭据（数据库 + 常见组合）
    
    Args:
        brand: 路由器品牌名
        creds_db: 默认凭据数据库
    
    Returns:
        去重后的凭据列表
    """
    # 品牌模糊匹配
    brand_lower = brand.lower()
    matched_brands = [brand]
    
    for db_brand in creds_db:
        if brand_lower in db_brand.lower():
            matched_brands.append(db_brand)
    
    all_creds: list[Credential] = []
    seen = set()
    
    # 从数据库取
    for b in matched_brands:
        for cred in creds_db.get(b, []):
            key = (cred.username.lower(), cred.password.lower())
            if key not in seen:
                seen.add(key)
                all_creds.append(cred)
    
    # 从内置品牌信息取
    brand_info = ROUTER_BRANDS.get(brand, {})
    for cred in brand_info.get("common_creds", []):
        key = (cred.username.lower(), cred.password.lower())
        if key not in seen:
            seen.add(key)
            all_creds.append(cred)
    
    return all_creds


# ═══════════════════════════════════════════════════════════
# 第三关：尝试登录路由器
# ═══════════════════════════════════════════════════════════

def try_router_login(
    ip: str,
    username: str,
    password: str,
    timeout: int = 5,
) -> tuple[ScanResult, str]:
    """
    尝试用一组凭据登录路由器管理页面
    
    Args:
        ip: 路由器IP地址
        username: 用户名
        password: 密码
        timeout: 超时秒数
    
    Returns:
        (ScanResult, 详细消息)
    """
    import urllib.request
    import urllib.error
    import base64
    
    result = ScanResult.FAILED
    msg = "密码错误"
    
    # 构建基础认证头
    auth_str = f"{username}:{password}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    # 尝试多个常见管理页面路径
    paths = [
        "/", "/index.html", "/login.cgi", "/cgi-bin/login",
        "/userRpm/", "/admin/login.asp", "/Main_Login.asp",
        "/goform/login", "/cgi-bin/luci", "/login.htm",
        "/webpages/login.html",
    ]
    
    for path in paths:
        url = f"http://{ip}{path}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Basic {b64_auth}")
        req.add_header("User-Agent", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            body = resp.read().decode("utf-8", errors="ignore").lower()
            
            # 如果返回的不是登录页面（不再包含login关键字），说明登录成功
            # 或者返回状态码200且有管理界面内容
            if resp.status == 200:
                login_keywords = ["login", "password", "username", "sign in", "请输入"]
                if not all(kw in body for kw in ["login", "password"]):
                    # 可能登录成功！看看页面上有没有管理功能字样
                    admin_keywords = ["status", "lan", "wan", "dhcp", "无线", "网络",
                                      "设置", "管理", "system", "administration"]
                    if any(kw in body for kw in admin_keywords):
                        return ScanResult.SUCCESS, f"✅ 登录成功！{username}:{password} (路径: {path})"
                    else:
                        # 不确定，记录但继续尝试
                        msg = f"⚠️ 可能成功 ({path})，但页面内容不确定"
                        result = ScanResult.SUCCESS
                
        except urllib.error.HTTPError as e:
            if e.code == 401:
                # 认证失败，继续试下一个路径
                continue
            elif e.code == 403:
                msg = "被拒绝访问（可能IP被限制）"
                result = ScanResult.BLOCKED
                break
            elif e.code == 404:
                # 路径不存在，试下一个
                continue
            elif e.code == 302 or e.code == 301:
                # 被重定向了——可能是登录成功！
                location = e.headers.get("Location", "")
                if "login" not in location.lower():
                    return ScanResult.SUCCESS, f"✅ 登录成功！{username}:{password} (重定向到 {location})"
                continue
            else:
                continue
                
        except urllib.error.URLError as e:
            msg = f"连接失败: {e.reason}"
            result = ScanResult.TIMEOUT
            break
            
        except Exception as e:
            msg = f"未知错误: {str(e)[:60]}"
            continue
    
    return result, msg


# ═══════════════════════════════════════════════════════════
# 第四关：全自动扫描
# ═══════════════════════════════════════════════════════════

def find_gateway() -> list[str]:
    """
    尝试发现路由器的IP地址
    
    Returns:
        可达的网关IP列表
    """
    import subprocess
    
    reachable = []
    
    print("\n🔍 正在扫描常见网关地址...")
    print(f"   {'IP地址':<18} {'状态':<12}")
    print(f"   {'─'*30}")
    
    for gw in COMMON_GATEWAYS:
        try:
            # Windows: ping -n 1
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "1000", gw],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                reachable.append(gw)
                print(f"   {gw:<18} {'✅ 可达':<12}")
            elif result.returncode != 0:
                print(f"   {gw:<18} {'❌ 不可达':<12}")
        except Exception:
            print(f"   {gw:<18} {'⚠️ 超时':<12}")
    
    return reachable


def identify_brand_from_http(gateway: str) -> str | None:
    """
    通过HTTP响应头猜测路由器品牌
    
    Args:
        gateway: 路由器IP
    
    Returns:
        品牌名或None
    """
    import urllib.request
    
    try:
        req = urllib.request.Request(f"http://{gateway}/")
        req.add_header("User-Agent", "Mozilla/5.0")
        resp = urllib.request.urlopen(req, timeout=5)
        
        server = resp.headers.get("Server", "").lower()
        www_auth = resp.headers.get("WWW-Authenticate", "").lower()
        body = resp.read().decode("utf-8", errors="ignore").lower()
        
        # 从Server头识别
        if "tp-link" in server or "tplink" in server:
            return "TP-Link"
        elif "huawei" in server or "huawei" in www_auth:
            return "Huawei"
        elif "mikrotik" in server or "routeros" in server:
            return "MikroTik"
        elif "asus" in server or "asuswrt" in server:
            return "ASUS"
        elif "cisco" in server:
            return "Cisco"
        elif "dlink" in server or "d-link" in server:
            return "D-Link"
        elif "netgear" in server:
            return "Netgear"
        elif "tenda" in server:
            return "Tenda"
        
        # 从页面内容识别
        title_keywords = {
            "TP-Link": ["tp-link", "tplink", "普联"],
            "Huawei": ["huawei", "华为"],
            "H3C": ["h3c", "华三", "quidway"],
            "ASUS": ["asus", "华硕"],
            "MikroTK": ["mikrotik", "routeros"],
            "D-Link": ["dlink", "d-link", "友讯"],
            "Tenda": ["tenda", "腾达"],
            "Mercury": ["mercury", "水星"],
            "Netgear": ["netgear", "网件"],
            "Xiaomi": ["xiaomi", "小米", "miwifi"],
        }
        
        for brand, keywords in title_keywords.items():
            if any(kw in body for kw in keywords):
                return brand
        
        return None
        
    except Exception:
        return None


def auto_scan_brand(
    gateway: str,
    brand: str,
    creds_db: dict[str, list[Credential]],
) -> DeviceInfo | None:
    """
    对指定品牌的网关进行全凭据扫描
    
    Args:
        gateway: 路由器IP
        brand: 品牌名
        creds_db: 凭据数据库
    
    Returns:
        找到凭据时的设备信息，None表示未找到
    """
    creds = get_creds_for_brand(brand, creds_db)
    
    if not creds:
        log.warning(f"⚠️ 没有找到 {brand} 的默认凭据")
        return None
    
    # 先试最常见的组合（快速命中）
    common_creds = ROUTER_BRANDS.get(brand, {}).get("common_creds", [])
    priority_creds = common_creds + [c for c in creds if c not in common_creds]
    
    log.info(f"🔑 正在尝试 {len(priority_creds)} 组 {brand} 默认凭据...")
    
    device = DeviceInfo(ip=gateway, brand=brand)
    
    for i, cred in enumerate(priority_creds):
        username = "" if cred.is_blank_username else cred.username
        password = "" if cred.is_blank_password else cred.password
        
        # 显示进度
        u_display = username if username else "(空)"
        p_display = password if password else "(空)"
        progress = f"[{i+1}/{len(priority_creds)}]"
        
        print(f"   {progress} 尝试 {u_display}:{p_display}", end="\r")
        
        result, msg = try_router_login(gateway, username, password)
        
        if result == ScanResult.SUCCESS:
            print(f"\n{'':>5} ✅ 找到密码！{u_display}:{p_display}")
            device.found_credentials.append(cred)
            return device
        elif result == ScanResult.BLOCKED:
            print(f"\n{'':>5} ⛔ 被锁定！可能多次错误导致IP被禁")
            break
        elif result == ScanResult.TIMEOUT:
            print(f"\n{'':>5} ⏱️ 连接超时，网关可能不响应")
            break
        
        # 每10次暂停一下，防止触发锁
        if (i + 1) % 10 == 0:
            time.sleep(0.5)
    
    print()
    return None


def save_results(devices: list[DeviceInfo]):
    """保存扫描结果"""
    data = []
    for d in devices:
        data.append({
            "ip": d.ip,
            "brand": d.brand,
            "model": d.model,
            "found_credentials": [
                {"username": c.username, "password": c.password}
                for c in d.found_credentials
            ],
        })
    
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    log.info(f"💾 结果已保存到 {RESULTS_FILE}")


# ═══════════════════════════════════════════════════════════
# 主程序
# ═══════════════════════════════════════════════════════════

def print_banner():
    """打印标题"""
    print(r"""
╔══════════════════════════════════════════════╗
║     🔐 路由器密码恢复工具                     ║
║     Router Credential Recovery Tool          ║
║     v1.0 · 数据来源: DefaultCreds 3.7k+     ║
╚══════════════════════════════════════════════╝
    """)


def print_brand_menu(creds_db: dict[str, list[Credential]]):
    """打印品牌选择菜单"""
    # 合并所有品牌
    all_brands = list(ROUTER_BRANDS.keys())
    
    print("\n📋 可选的品牌列表：")
    print(f"   {'编号':<6} {'品牌':<18} {'默认网关':<22}")
    print(f"   {'─'*46}")
    
    for i, brand in enumerate(all_brands, 1):
        gateways = ", ".join(ROUTER_BRANDS[brand]["gateways"][:2])
        db_count = len(creds_db.get(brand, []))
        extra = f" (含{db_count}条数据库)" if db_count > 0 else ""
        print(f"   [{i:<3}] {brand:<18} {gateways:<22}{extra}")
    
    print(f"   [A]  自动扫描所有常见品牌")
    
    return all_brands


def main():
    parser = argparse.ArgumentParser(
        description="路由器密码恢复工具 - Router Credential Recovery Tool"
    )
    parser.add_argument("--brand", "-b", type=str, default=None,
                        help="指定品牌名 (如 tplink, huawei, h3c)")
    parser.add_argument("--gateway", "-g", type=str, default=None,
                        help="指定路由器IP (如 192.168.1.1)")
    parser.add_argument("--auto", "-a", action="store_true",
                        help="自动扫描模式")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出所有支持的品牌")
    
    args = parser.parse_args()
    
    # 加载凭据数据库
    creds_db = load_default_creds(DEFAULT_CREDS_CSV)
    
    if args.list:
        print_banner()
        print("📋 支持的品牌列表：")
        for brand in sorted(ROUTER_BRANDS.keys()):
            gateways = ", ".join(ROUTER_BRANDS[brand]["gateways"][:2])
            db_count = len(creds_db.get(brand, []))
            print(f"   {brand:<18}  网关: {gateways:<22} {'(' + str(db_count) + '条数据库)' if db_count > 0 else ''}")
        return
    
    print_banner()
    
    # ── 确定路由器IP ──────────────────────────────────────
    gateway = args.gateway
    if not gateway:
        print("\n📡 第一步：发现路由器IP")
        print("=" * 40)
        reachable = find_gateway()
        
        if not reachable:
            print("\n❌ 没有发现可达的网关IP！")
            print("\n💡 请手动确认路由器IP：")
            print("   1. Windows: 打开CMD → 输入 ipconfig → 看默认网关")
            print("   2. 常见IP: 192.168.1.1 / 192.168.0.1 / 192.168.100.1")
            print("\n   然后用 --gateway 参数指定：")
            print("   python router_credential_recovery.py --gateway=192.168.1.1")
            return
        
        if len(reachable) == 1:
            gateway = reachable[0]
            print(f"\n   🎯 选择唯一可用的网关: {gateway}")
        else:
            print(f"\n   🎯 发现多个可达网关，使用第一个: {reachable[0]}")
            gateway = reachable[0]
    
    print(f"\n📡 扫描目标: http://{gateway}/")
    
    # ── 自动识别品牌 ──────────────────────────────────────
    auto_brand = identify_brand_from_http(gateway)
    if auto_brand:
        print(f"🔍 HTTP识别品牌: {auto_brand}")
    
    # ── 确定品牌 ──────────────────────────────────────────
    brand = None
    if args.brand:
        # 别名转换
        brand_lower = args.brand.lower().strip()
        if brand_lower in BRAND_ALIASES:
            brand = BRAND_ALIASES[brand_lower]
        else:
            # 模糊匹配
            for alias, real_name in BRAND_ALIASES.items():
                if brand_lower in alias or alias in brand_lower:
                    brand = real_name
                    break
            if not brand:
                # 直接匹配品牌名
                for b in ROUTER_BRANDS:
                    if brand_lower in b.lower():
                        brand = b
                        break
            if not brand:
                print(f"❌ 未识别的品牌: {args.brand}")
                print("   可用 --list 查看所有支持品牌")
                return
        
        print(f"🎯 目标品牌: {brand}")
    
    elif auto_brand:
        brand = auto_brand
        print(f"🎯 自动识别品牌: {brand}")
    
    elif args.auto:
        # 自动模式：扫描所有可达网关
        reachable = [gateway] if gateway else find_gateway()
        found_any = False
        
        for gw in reachable:
            detected_brand = identify_brand_from_http(gw)
            if detected_brand:
                print(f"\n🔍 {gw} 识别为: {detected_brand}")
                device = auto_scan_brand(gw, detected_brand, creds_db)
                if device and device.found_credentials:
                    found_any = True
            else:
                # 未识别品牌，尝试所有常见品牌
                print(f"\n🔍 {gw} 品牌未知，逐品牌尝试...")
                for b in ROUTER_BRANDS:
                    print(f"   ─ 尝试 {b}...")
                    device = auto_scan_brand(gw, b, creds_db)
                    if device and device.found_credentials:
                        found_any = True
                        break
        
        if found_any:
            print("\n✅ 扫描完成！找到密码了！")
        else:
            print("\n❌ 未找到有效凭据")
            print("\n💡 建议尝试：")
            print("   🅰 看路由器背面标签（大概率有默认密码）")
            print("   🅱 捅Reset键10秒恢复出厂")
            print("   🅲 问IT/网管要密码")
        return
    
    else:
        # 交互模式：选品牌
        all_brands = print_brand_menu(creds_db)
        try:
            choice = input("\n请输入编号 (1-{}) 或品牌名: ".format(len(all_brands))).strip()
            if choice.upper() == "A" or choice.lower() == "auto":
                brand = None
                args.auto = True
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(all_brands):
                    brand = all_brands[idx]
                else:
                    print("❌ 无效编号")
                    return
            else:
                # 品牌名匹配
                cl = choice.lower()
                matched = [b for b in all_brands if cl in b.lower()]
                if matched:
                    brand = matched[0]
                elif cl in BRAND_ALIASES:
                    brand = BRAND_ALIASES[cl]
                else:
                    print(f"❌ 未识别: {choice}")
                    return
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 已取消")
            return
    
    if args.auto:
        # 重定向到自动模式
        main_auto = lambda: None
        # 简化的自动扫描
        print(f"\n🔍 全自动扫描 {gateway}...")
        for b in ROUTER_BRANDS:
            print(f"\n   ─ 尝试 {b}...")
            device = auto_scan_brand(gateway, b, creds_db)
            if device and device.found_credentials:
                print(f"\n🎉 找到密码！用户名: {device.found_credentials[0].username}, 密码: {device.found_credentials[0].password}")
                save_results([device])
                return
        
        print("\n❌ 未找到有效凭据")
        print("\n💡 建议尝试：")
        print("   🅰 看路由器背面标签（大概率有默认密码）")
        print("   🅱 捅Reset键10秒恢复出厂")
        print("   🅲 问IT/网管要密码")
        return
    
    if not brand:
        print("❌ 未指定品牌")
        return
    
    # ── 执行扫描 ──────────────────────────────────────────
    print(f"\n🔑 第二步：尝试 {brand} 路由器默认密码")
    print("=" * 60)
    
    device = auto_scan_brand(gateway, brand, creds_db)
    
    if device and device.found_credentials:
        cred = device.found_credentials[0]
        print(f"\n{'='*60}")
        print(f"🎉 找到了 {brand} 路由器的登录密码！")
        print(f"{'='*60}")
        print(f"   🌐 管理地址: http://{gateway}/")
        print(f"   👤 用户名:    {cred.username}")
        print(f"   🔑 密码:      {cred.password}")
        print(f"{'='*60}")
        print("\n💡 现在可以用这个密码登录路由器后台了！")
        print("   进去后记得设置 WOL 和端口转发哦~")
        
        save_results([device])
    else:
        print(f"\n{'='*60}")
        print(f"❌ 未在 {brand} 默认凭据中找到有效密码")
        print(f"{'='*60}")
        print(f"\n💡 其他可行的方法：")
        print(f"   🅰 看路由器【背面标签】——大概率上面印着默认密码！")
        print(f"   🅱 捅【Reset键】10秒恢复出厂设置（需要重新设置WiFi密码）")
        print(f"   🅲 直接问【IT/网管】——说「老板要远程办公」一般会给")
        print(f"   🅳 用 --brand=其他品牌 试试不同品牌")
        if not auto_brand:
            print(f"   🅴 HTTP没识别出品牌，试试 --auto 全自动扫描")


if __name__ == "__main__":
    main()