#!/usr/bin/env python3
"""
BLIIOT Email Marketing Engine
=============================
安全可靠的邮件自动发送系统
- SMTP通道 (QQ企业邮)
- 多模板引擎 (HTML + 纯文本)
- 智能发送队列 (带延迟+随机化防SPAM)
- 发送日志 + 失败重试
- 读取跟进JSON数据

使用方法:
    1. 先设置密码:  python bliit_mailer.py --set-password
    2. 发送邮件:    python bliit_mailer.py --send
    3. 测试发送:    python bliit_mailer.py --test
"""

import os
import sys
import json
import time
import random
import smtplib
import logging
import argparse
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr, formatdate
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ============================================================
# Configuration
# ============================================================

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / ".mailer_config.json"
SENT_LOG = SCRIPT_DIR / ".sent_log.json"
PASSWORD_FILE = SCRIPT_DIR / ".smtp_password"

# QQ个人邮箱 SMTP (原为企业邮箱, 2026-06-18 切换为个人邮箱)
SMTP_HOST = "smtp.qq.com"
SMTP_PORT_SSL = 465
SMTP_PORT_TLS = 587

# 发件人
FROM_EMAIL = "kali_foever@qq.com"
FROM_NAME = "Kali | BLIIOT Technology"

# 发送控制
MIN_DELAY_SEC = 45    # 每封邮件最小间隔(秒)
MAX_DELAY_SEC = 90    # 每封邮件最大间隔(秒)
MAX_EMAILS_PER_DAY = 50  # 每日发送上限
BATCH_SIZE = 5        # 每批次多少封后休息
BATCH_REST_MIN = 180  # 批次间休息秒数(3分钟)
BATCH_REST_MAX = 300  # 批次间休息秒数(5分钟)

# 数据源路径
FOLLOWUP_DIRS = [
    Path(r"C:\Users\Admin\AppData\Local\hermes\memories\buyer-development"),
    Path(r"C:\Users\Admin\Desktop\Working"),
]

# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SCRIPT_DIR / "mailer.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("bliiot-mailer")

# ============================================================
# Email Templates
# ============================================================

HTML_TEMPLATES = {}

def _init_templates():
    """初始化邮件HTML模板"""
    
    # 模板1: 标准B2B推广 - ARMxy Edge Computers
    HTML_TEMPLATES["armxy_edge"] = {
        "subject": "Industrial ARM Edge Controllers - BLIIOT Direct Factory Price",
        "html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🌟 BLIIOT Technology</h1>
        <p style="color: #e3f2fd; margin: 5px 0 0;">Industrial IoT Hardware Manufacturer Since 2005</p>
    </div>
    
    <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
        <h2 style="color: #1a73e8;">ARMxy Series Industrial Edge Controllers</h2>
        
        <p>Dear Partner,</p>
        
        <p>We are writing to introduce our <strong>ARMxy Series Industrial ARM Edge Controllers</strong> — versatile, cost-effective embedded computers designed for SCADA, IIoT, and edge computing applications.</p>
        
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #1a73e8; margin-top: 0;">Key Features:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px;">⚡</td><td><strong>Multi-core ARM Cortex</strong> (A7/A53/A76 up to 2.4GHz)</td></tr>
                <tr><td style="padding: 8px;">🔌</td><td><strong>Modular I/O</strong> — RS485, RS232, CAN Bus, DI/DO</td></tr>
                <tr><td style="padding: 8px;">🐧</td><td><strong>Linux/Ubuntu</strong> + Node-RED + Python pre-installed</td></tr>
                <tr><td style="padding: 8px;">🌐</td><td><strong>Modbus TCP/RTU, OPC UA, MQTT, BACnet</strong></td></tr>
                <tr><td style="padding: 8px;">🔒</td><td><strong>Industrial grade</strong> — -40°C to +85°C, 9-36VDC</td></tr>
                <tr><td style="padding: 8px;">📦</td><td><strong>DIN-rail mount</strong>, compact design</td></tr>
            </table>
        </div>
        
        <p><strong>Popular Models:</strong> BL301, BL310, BL330, BL340, BL350, BL360, BL410, BL460</p>
        <p><strong>Price Range:</strong> $80 - $300 (FOB Shenzhen, direct factory price)</p>
        
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p style="margin: 5px 0; font-size: 16px;"><strong>📞 WhatsApp: +86 17704014518</strong></p>
            <p style="margin: 5px 0; font-size: 14px; color: #666;">Or reply to this email for catalog and pricing</p>
        </div>
        
        <p>We also manufacture:</p>
        <ul>
            <li><strong>IoT Gateways</strong> (BL116, BE116, BA116) — 4G LTE, dual Ethernet, Node-RED</li>
            <li><strong>R40 Series Cellular Routers</strong> — Dual SIM, VPN, GPS, industrial grade</li>
            <li><strong>Remote I/O Modules</strong> — IOy series, Modbus TCP/RTU, analog & digital</li>
            <li><strong>RTU Solutions</strong> — RTU5020 series for SCADA & telemetry</li>
        </ul>
        
        <p>We are a direct manufacturer with <strong>10+ years</strong> of industrial automation experience. OEM/ODM welcome. Global shipping with fast delivery.</p>
        
        <p>Looking forward to hearing from you!</p>
        
        <p>Best regards,<br>
        <strong>BLIIOT Sales Team</strong><br>
        Shenzhen Beilai Technology Co., Ltd.<br>
        Website: <a href="https://www.bliiot.com">www.bliiot.com</a><br>
        Email: bl42@bliiot.com | WhatsApp: +86 17704014518</p>
    </div>
    
    <div style="background: #1a237e; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
        <p style="color: #90caf9; font-size: 12px; margin: 0;">
            This email is sent to you as a potential business partner. 
            If you would not like to receive future communications, simply reply with "Unsubscribe".
        </p>
    </div>
</body>
</html>""",
        "text": """Dear Partner,

BLIIOT Technology - Industrial IoT Hardware Manufacturer Since 2005

We are writing to introduce our ARMxy Series Industrial ARM Edge Controllers — versatile, cost-effective embedded computers for SCADA, IIoT, and edge computing.

Key Features:
- Multi-core ARM Cortex processors (A7/A53/A76)
- Modular I/O: RS485, RS232, CAN Bus, DI/DO
- Linux/Ubuntu + Node-RED + Python pre-installed
- Modbus TCP/RTU, OPC UA, MQTT, BACnet support
- Industrial grade: -40°C to +85°C, 9-36VDC
- DIN-rail mount, compact design

Popular Models: BL301, BL310, BL330, BL340, BL350, BL360, BL410, BL460
Price Range: $80 - $300 (FOB Shenzhen)

Also available:
- IoT Gateways (BL116, BE116, BA116) — 4G LTE, dual Ethernet
- R40 Cellular Routers — Dual SIM, VPN, GPS
- Remote I/O Modules — IOy series
- RTU for SCADA & telemetry

Direct manufacturer since 2005. OEM/ODM welcome.

Contact us:
WhatsApp: +86 17704014518
Email: bl42@bliiot.com
Web: www.bliiot.com

Best regards,
BLIIOT Sales Team
Shenzhen Beilai Technology Co., Ltd.

---
If you would not like to receive future communications, reply with "Unsubscribe".
""",
    }
    
    # 模板2: IoT Gateway推广
    HTML_TEMPLATES["iot_gateways"] = {
        "subject": "Industrial IoT Gateways with 4G LTE - BLIIOT Direct Supply",
        "html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #00897b, #004d40); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">🔗 BLIIOT Technology</h1>
        <p style="color: #b2dfdb; margin: 5px 0 0;">Industrial IoT Hardware Manufacturer</p>
    </div>
    
    <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
        <h2 style="color: #00897b;">Industrial IoT Gateways</h2>
        
        <p>Dear Partner,</p>
        
        <p>Are you looking for reliable, cost-effective IoT gateways for your industrial projects? BLIIOT offers a complete range of <strong>4G LTE Industrial IoT Gateways</strong> perfect for remote monitoring, smart manufacturing, and building automation.</p>
        
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #00897b; margin-top: 0;">BL116 / BE116 / BA116 Series</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 5px;">📶</td><td><strong>4G LTE Cat 4</strong> with dual SIM failover</td></tr>
                <tr><td style="padding: 5px;">🔗</td><td><strong>Dual Ethernet</strong> + RS485 + WiFi</td></tr>
                <tr><td style="padding: 5px;">⚙️</td><td><strong>Node-RED</strong> + Modbus pre-installed</td></tr>
                <tr><td style="padding: 5px;">🔄</td><td><strong>Protocol conversion:</strong> Modbus ↔ MQTT ↔ OPC UA ↔ BACnet</td></tr>
                <tr><td style="padding: 5px;">☁️</td><td><strong>BLRMS cloud</strong> remote management</td></tr>
                <tr><td style="padding: 5px;">🔒</td><td><strong>Industrial design:</strong> DIN-rail, wide temp, wide voltage</td></tr>
            </table>
        </div>
        
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p style="margin: 5px 0; font-size: 16px;"><strong>📞 Contact us on WhatsApp: +86 17704014518</strong></p>
            <p style="margin: 5px 0; font-size: 14px; color: #666;">Or reply to this email for catalog & pricing</p>
        </div>
        
        <p>We serve system integrators, automation companies, and OEMs in <strong>50+ countries</strong>.</p>
        
        <p>Best regards,<br>
        <strong>BLIIOT Sales Team</strong><br>
        Shenzhen Beilai Technology Co., Ltd.<br>
        Web: <a href="https://www.bliiot.com">www.bliiot.com</a></p>
    </div>
    
    <div style="background: #004d40; padding: 15px; border-radius: 0 0 10px 10px; text-align: center;">
        <p style="color: #80cbc4; font-size: 12px; margin: 0;">
            Reply "Unsubscribe" to opt out.
        </p>
    </div>
</body>
</html>""",
        "text": """Dear Partner,

Are you looking for reliable, cost-effective IoT gateways? BLIIOT offers a complete range of 4G LTE Industrial IoT Gateways.

BL116 / BE116 / BA116 Series:
- 4G LTE Cat 4 with dual SIM failover
- Dual Ethernet + RS485 + WiFi
- Node-RED + Modbus pre-installed
- Protocol conversion: Modbus - MQTT - OPC UA - BACnet
- BLRMS cloud remote management
- Industrial: DIN-rail, wide temp, wide voltage

Contact us:
WhatsApp: +86 17704014518
Email: bl42@bliiot.com
Web: www.bliiot.com

Best regards,
BLIIOT Sales Team
""",
    }
    
    # 模板3: R40工业路由器
    HTML_TEMPLATES["r40_router"] = {
        "subject": "Industrial 4G Cellular Router - Dual SIM, VPN, BLIIOT",
        "html": """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Arial, Helvetica, sans-serif; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #e65100, #bf360c); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">📡 BLIIOT Technology</h1>
        <p style="color: #ffccbc; margin: 5px 0 0;">Industrial IoT Hardware Manufacturer</p>
    </div>
    
    <div style="background: #fff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
        <h2 style="color: #e65100;">R40 Series Industrial Cellular Router</h2>
        
        <p>Dear Partner,</p>
        
        <p>For reliable connectivity in remote or harsh environments, our <strong>R40 Series Industrial 4G LTE Router</strong> is the ideal solution. Designed for oil & gas, smart grid, transportation, and remote monitoring applications.</p>
        
        <div style="background: #fff3e0; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 8px;">📶</td><td><strong>4G LTE Cat 4</strong> with dual SIM redundancy</td></tr>
                <tr><td style="padding: 8px;">🔗</td><td><strong>Dual Ethernet</strong> + WiFi + GPS</td></tr>
                <tr><td style="padding: 8px;">🔐</td><td><strong>VPN</strong> (OpenVPN/IPSec/PPTP)</td></tr>
                <tr><td style="padding: 8px;">🔌</td><td><strong>RS232/RS485</strong> serial ports</td></tr>
                <tr><td style="padding: 8px;">🌡️</td><td><strong>-40°C to +75°C</strong> wide temperature</td></tr>
                <tr><td style="padding: 8px;">⚡</td><td><strong>9-48VDC</strong> wide voltage input</td></tr>
            </table>
        </div>
        
        <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <p style="margin: 5px 0; font-size: 16px;"><strong>📞 WhatsApp: +86 17704014518</strong></p>
        </div>
        
        <p>Best regards,<br>
        <strong>BLIIOT Sales Team</strong><br>
        Web: <a href="https://www.bliiot.com">www.bliiot.com</a></p>
    </div>
</body>
</html>""",
        "text": """Dear Partner,

For reliable connectivity in remote or harsh environments, our R40 Series Industrial 4G LTE Router is the ideal solution.

Key Features:
- 4G LTE Cat 4 with dual SIM redundancy
- Dual Ethernet + WiFi + GPS
- VPN (OpenVPN/IPSec/PPTP)
- RS232/RS485 serial ports
- -40°C to +75°C wide temperature
- 9-48VDC wide voltage input

Contact: WhatsApp +86 17704014518 | Email: bl42@bliiot.com
Web: www.bliiot.com

Best regards,
BLIIOT Sales Team
""",
    }


_init_templates()


# ============================================================
# Data Loading
# ============================================================

def load_leads_with_email():
    """从所有客户跟进JSON中提取有邮箱的客户"""
    all_leads = []
    seen_emails = set()

    for directory in FOLLOWUP_DIRS:
        if not directory.exists():
            continue
        for f in sorted(directory.glob("*followup*.json")):
            try:
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, list):
                    for entry in data:
                        email = (entry.get("email") or "").strip().lower()
                        if not email or "@" not in email:
                            continue
                        # 过滤无效邮箱
                        if email in ("user@domain.com",):
                            continue
                        # 过滤明显非邮箱的字符串（如图片名、乱码）
                        domain_part = email.split("@")[-1]
                        if "." not in domain_part:
                            continue
                        ext = domain_part.rsplit(".", 1)[-1]
                        if ext in ("jpg", "png", "gif", "jpeg", "bmp", "pdf", "doc", "docx", "xls", "xlsx", "fw", "io"):
                            continue
                        if email in seen_emails:
                            continue
                        seen_emails.add(email)
                        all_leads.append({
                            "email": email,
                            "company": (entry.get("company_name") or "").strip(),
                            "country": (entry.get("country") or "").strip(),
                            "website": (entry.get("website") or "").strip(),
                            "whatsapp": (entry.get("whatsapp") or "").strip(),
                            "industry": (entry.get("industry") or "").strip(),
                            "source": f.name,
                        })
            except Exception as e:
                log.warning(f"Error reading {f}: {e}")

    return all_leads


# ============================================================
# SMTP / Send Engine
# ============================================================

def get_smtp_password():
    """读取保存的SMTP密码/授权码"""
    if PASSWORD_FILE.exists():
        return PASSWORD_FILE.read_text(encoding="utf-8").strip()
    return None

def save_smtp_password(password: str):
    """保存SMTP授权码"""
    PASSWORD_FILE.write_text(password.strip(), encoding="utf-8")
    log.info("✅ SMTP password saved (not the login password - QQ企业邮授权码)")
    print("✅ SMTP授权码已保存！")

def send_email(
    to_addr: str,
    subject: str,
    html_body: str,
    text_body: str,
    password: str,
) -> bool:
    """通过QQ企业邮SMTP发送邮件"""
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)

        # 纯文本 + HTML
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # SSL连接
        context = None
        try:
            context = __import__("ssl").create_default_context()
        except:
            pass

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL, context=context, timeout=30) as server:
            server.login(FROM_EMAIL, password)
            server.sendmail(FROM_EMAIL, [to_addr], msg.as_string())
        
        log.info(f"✅ Sent to {to_addr}")
        return True
    except smtplib.SMTPAuthenticationError:
        log.error(f"❌ SMTP认证失败！密码/授权码错误")
        return False
    except smtplib.SMTPRecipientsRefused:
        log.warning(f"❌ 收件人拒绝: {to_addr}")
        return False
    except Exception as e:
        log.error(f"❌ Failed to send to {to_addr}: {e}")
        return False


# ============================================================
# Queue & Logging
# ============================================================

def load_sent_log():
    """加载已发送日志"""
    if SENT_LOG.exists():
        try:
            with open(SENT_LOG, encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"sent": [], "failed": [], "total_sent": 0}

def save_sent_log(log_data: dict):
    """保存发送日志"""
    with open(SENT_LOG, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

def get_todays_count(log_data: dict) -> int:
    """今天已发送数量"""
    today = time.strftime("%Y-%m-%d")
    return sum(1 for s in log_data.get("sent", []) if s.get("date", "").startswith(today))


# ============================================================
# Main Send Flow
# ============================================================

def do_send(dry_run: bool = False):
    """执行发送流程"""
    password = get_smtp_password()
    if not password:
        log.error("❌ SMTP密码未设置！请先运行 --set-password")
        print("\n❌ 错误: SMTP授权码未设置！")
        print("   请先运行: python bliit_mailer.py --set-password")
        return

    # 加载客户数据
    leads = load_leads_with_email()
    if not leads:
        log.warning("⚠️ 没有找到有邮箱的客户")
        print("⚠️ 没有找到有邮箱的客户数据")
        return

    # 加载发送日志
    sent_log = load_sent_log()
    today_count = get_todays_count(sent_log)
    sent_emails = set(s["email"] for s in sent_log.get("sent", []))

    # 过滤未发送的
    unsent = [l for l in leads if l["email"] not in sent_emails]

    # 按今日限额截断
    remaining_slots = MAX_EMAILS_PER_DAY - today_count
    if remaining_slots <= 0:
        log.warning(f"⚠️ 今日已发{today_count}封，达到上限{MAX_EMAILS_PER_DAY}")
        print(f"⚠️ 今日已达发送上限 ({MAX_EMAILS_PER_DAY}封)")
        return

    to_send = unsent[:remaining_slots]

    print(f"\n{'='*60}")
    print(f"  BLIIOT Email Marketing Engine")
    print(f"{'='*60}")
    print(f"  客户总数:      {len(leads)}")
    print(f"  今日已发送:    {today_count}")
    print(f"  剩余名额:      {remaining_slots}")
    print(f"  本次将发送:    {len(to_send)}")
    print(f"  已发送历史:    {len(sent_emails)}")
    print()

    if not to_send:
        print("🎉 所有客户都已发送完毕！")
        return

    if dry_run:
        print(f"\n📋 干运行模式 - 以下客户将收到邮件:")
        for i, lead in enumerate(to_send, 1):
            print(f"  {i}. {lead['company']:35s} <{lead['email']:25s}> {lead['country']}")
        print(f"\n  (共{len(to_send)}封，未实际发送)")
        return

    # 开始发送
    print(f"\n🚀 开始发送 {len(to_send)} 封邮件...\n")

    success_count = 0
    fail_count = 0

    for idx, lead in enumerate(to_send, 1):
        # 选择模板（随机选择产品线）
        template_key = random.choice(list(HTML_TEMPLATES.keys()))
        template = HTML_TEMPLATES[template_key]

        # 可个性化公司名称
        company = lead["company"] if lead["company"] else "Partner"

        # 准备邮件内容
        subject = template["subject"]
        html_body = template["html"]
        text_body = f"Dear {company},\n\n{template['text']}"

        if not dry_run:
            print(f"  [{idx}/{len(to_send)}] Sending to {company:30s} <{lead['email']}>... ", end="")

        ok = send_email(lead["email"], subject, html_body, text_body, password)
        
        if ok:
            success_count += 1
            sent_log["sent"].append({
                "email": lead["email"],
                "company": lead["company"],
                "country": lead["country"],
                "template": template_key,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            if not dry_run:
                print("✅")
        else:
            fail_count += 1
            sent_log["failed"].append({
                "email": lead["email"],
                "company": lead["company"],
                "error": "send_failed",
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            })
            if not dry_run:
                print("❌")

        # 保存日志（每发送一个都保存，防止中断丢失）
        sent_log["total_sent"] = success_count
        save_sent_log(sent_log)

        # 延迟（防SPAM）
        if idx < len(to_send):
            delay = random.randint(MIN_DELAY_SEC, MAX_DELAY_SEC)
            if not dry_run:
                print(f"     ⏱ Waiting {delay}s...")
            time.sleep(delay)

            # 批次间长休息
            if idx % BATCH_SIZE == 0:
                rest = random.randint(BATCH_REST_MIN, BATCH_REST_MAX)
                if not dry_run:
                    print(f"     💤 Batch complete, resting {rest}s...")
                time.sleep(rest)

    # 报告
    print(f"\n{'='*60}")
    print(f"  📊 发送完成！")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  累计: {sent_log['total_sent']}")
    print(f"{'='*60}")

    # 列出已发客户
    if success_count > 0:
        print(f"\n📬 本次发送客户列表:")
        for s in sent_log["sent"][-success_count:]:
            print(f"  ✅ {s['company']:30s} <{s['email']:30s}> [{s['country']}]")


def show_status():
    """显示当前状态"""
    leads = load_leads_with_email()
    sent_log = load_sent_log()
    today_count = get_todays_count(sent_log)
    sent_emails = set(s["email"] for s in sent_log.get("sent", []))
    unsent = [l for l in leads if l["email"] not in sent_emails]

    print(f"\n{'='*60}")
    print(f"  📊 BLIIOT Mailer Status")
    print(f"{'='*60}")
    print(f"  SMTP通道:      {FROM_EMAIL} @ {SMTP_HOST}")
    print(f"  密码设置:      {'✅ 已设置' if get_smtp_password() else '❌ 未设置'}")
    print(f"  客户邮箱总数:  {len(leads)}")
    print(f"  已发送:        {len(sent_emails)}")
    print(f"  今日已发:      {today_count}/{MAX_EMAILS_PER_DAY}")
    print(f"  待发送:        {len(unsent)}")
    print()

    if sent_log["sent"]:
        print("  最近发送记录:")
        for s in sent_log["sent"][-10:]:
            print(f"    {s['date']} | {s['company']:25s} | {s['email']} | [{s['country']}]")

    if sent_log["failed"]:
        print(f"\n  失败记录 ({len(sent_log['failed'])}条):")
        for f in sent_log["failed"][-3:]:
            print(f"    {f['date']} | {f['company']} | {f['email']} | {f.get('error','')}")

    if unsent:
        print(f"\n  📋 待发送客户:")
        for i, l in enumerate(unsent[:10], 1):
            print(f"    {i}. {l['company']:30s} <{l['email']:30s}> [{l['country']}]")
        if len(unsent) > 10:
            print(f"    ... 还有{len(unsent)-10}个")

    print()


def send_test_email(password: str = None):
    """发送测试邮件到发件人自己"""
    if not password:
        password = get_smtp_password()
    if not password:
        log.error("❌ 未设置SMTP密码")
        return False

    print(f"\n📧 发送测试邮件到 {FROM_EMAIL} ...")
    ok = send_email(
        FROM_EMAIL,
        "Test Email from BLIIOT Mailer",
        "<h1>Test</h1><p>This is a test email from your BLIIOT Email Marketing Engine.</p><p>If you receive this, SMTP is working!</p>",
        "Test email - SMTP is working!",
        password,
    )
    if ok:
        print(f"✅ 测试邮件已发送到 {FROM_EMAIL}，请检查收件箱！")
    else:
        print(f"❌ 发送失败，请检查SMTP授权码是否正确")
    return ok


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="BLIIOT Email Marketing Engine")
    parser.add_argument("--set-password", action="store_true", help="设置SMTP授权码")
    parser.add_argument("--send", action="store_true", help="执行发送")
    parser.add_argument("--dry-run", action="store_true", help="干运行（只列出不发）")
    parser.add_argument("--status", action="store_true", help="显示状态")
    parser.add_argument("--test", action="store_true", help="发送测试邮件")
    parser.add_argument("--reset-log", action="store_true", help="重置发送日志")
    parser.add_argument("--list", action="store_true", help="列出所有客户")
    args = parser.parse_args()

    if args.set_password:
        print("\n🔑 请输入QQ企业邮SMTP授权码")
        print("   (不是登录密码，是QQ邮箱设置里生成的授权码)")
        pw = input("   SMTP授权码: ").strip()
        if pw:
            save_smtp_password(pw)
            print("\n📧 发送测试邮件验证...")
            send_test_email(pw)
        else:
            print("❌ 密码不能为空")
        return

    if args.list:
        leads = load_leads_with_email()
        print(f"\n📋 共有 {len(leads)} 个客户有邮箱:")
        for i, l in enumerate(leads, 1):
            print(f"  {i:3d}. {l['company']:35s} <{l['email']:30s}> [{l['country']:15s}]")
        return

    if args.status:
        show_status()
        return

    if args.test:
        send_test_email()
        return

    if args.reset_log:
        save_sent_log({"sent": [], "failed": [], "total_sent": 0})
        print("✅ 发送日志已重置")
        return

    if args.send or args.dry_run:
        do_send(dry_run=args.dry_run)
        return

    # 无参数时显示状态
    show_status()


if __name__ == "__main__":
    main()