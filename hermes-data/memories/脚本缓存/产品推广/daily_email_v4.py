"""
BLIIOT 每日拟人邮件发送 v4.1 — 随机时间版
- 每天cron触发后，随机延迟0-60分钟再开始发送
- 每封邮件间隔随机60-180秒
- 每天最多50封，严格防重复
"""
import json, smtplib, ssl, time, random, sys, os
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate

# ===== 路径配置（绝对路径，cron模式下也能用） =====
SD = Path.home() / "AppData/Local/hermes/memories/脚本缓存/产品推广"
DATA_FILE = Path.home() / "Desktop/Working/富通CRM_公海客户_全量.json"
SENT_LOG = SD / ".sent_log_v4.json"
DAILY_STATE = SD / ".daily_state_v4.json"
CRM_DB = Path.home() / "AppData/Local/hermes/memories/脚本缓存/富通CRM/crm_followups.db"

FE = "kali_foever@qq.com"
FN = "Kali | BLIIOT Technology"
SH = "smtp.qq.com"
SP = 465
DAILY_LIMIT = 50

SUBJECTS = [
    "Following up | BLIIOT Industrial IoT Solutions",
    "Quick check-in from BLIIOT",
    "Re: Industrial IoT gateways & remote monitoring",
    "Checking in | BLIIOT Industrial Solutions",
]

BODIES = [
    """{greeting}

Hope this email finds you well.

I'm Kali from BLIIOT (www.bliiot.com). We previously connected about our industrial IoT gateways and remote monitoring solutions.

I wanted to check if you have any upcoming projects where our solutions might help?

Email: bl42@bliiot.com | WhatsApp: +86 17704014518

Best regards,
Kali | BLIIOT""",

    """{greeting}

I hope you're having a great week!

This is Kali from BLIIOT. We spoke about industrial IoT solutions for remote monitoring.

New products: ARM edge controllers, LoRaWAN gateways, IOy remote I/O.

Email: bl42@bliiot.com | WhatsApp: +86 17704014518

Thanks,
Kali | BLIIOT""",

    """{greeting}

Quick note from BLIIOT — we provide industrial IoT gateways and remote I/O for SCADA, solar monitoring, and building automation.

Any automation projects coming up?

Email: bl42@bliiot.com | WhatsApp: +86 17704014518

Best,
Kali | BLIIOT""",
]

def get_pw():
    pw_file = SD / ".smtp_password"
    return pw_file.read_text('utf-8').strip() if pw_file.exists() else None

def load_sent():
    s = set()
    for f in [SENT_LOG, SD / ".sent_log.json"]:
        if f.exists():
            s |= set(json.loads(f.read_text('utf-8')))
    return s

def save_sent(sent):
    SENT_LOG.write_text(json.dumps(list(sent), ensure_ascii=False))

def load_state():
    if DAILY_STATE.exists():
        s = json.loads(DAILY_STATE.read_text('utf-8'))
        if s.get('date') == datetime.now().strftime('%Y-%m-%d'):
            return s
    return {'date': datetime.now().strftime('%Y-%m-%d'), 'count': 0, 'sent_ids': []}

def save_state(state):
    DAILY_STATE.write_text(json.dumps(state, ensure_ascii=False))

def send_email(to, subject, body):
    ctx = ssl.create_default_context()
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((FN, FE))
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP_SSL(SH, SP, context=ctx, timeout=30) as s:
            s.login(FE, get_pw())
            s.sendmail(FE, [to], msg.as_string())
        return True
    except Exception as e:
        return str(e)

def main():
    print("=" * 60)
    print(f"BLIIOT 拟人邮件发送 v4.1 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    pw = get_pw()
    if not pw:
        print("❌ 无SMTP密码"); return
    
    state = load_state()
    today_count = state.get('count', 0) if state.get('date') == datetime.now().strftime('%Y-%m-%d') else 0
    remaining = DAILY_LIMIT - today_count
    
    print(f"今日已发: {today_count}/{DAILY_LIMIT} | 剩余: {remaining}")
    
    if remaining <= 0:
        print(f"✅ 今日已达上限 {DAILY_LIMIT} 封，明天再发")
        return
    
    # 随机延迟0-60分钟再开始（模拟真人不固定时间操作）
    initial_delay = random.randint(0, 3600)
    if initial_delay > 0:
        m, s = divmod(initial_delay, 60)
        print(f"⏳ 随机延迟 {m}分{s}秒后开始发送（模拟真人操作时间）")
        time.sleep(initial_delay)
    
    # 加载数据
    print("📂 加载客户数据...")
    data = json.loads(DATA_FILE.read_text('utf-8'))
    sent = load_sent()
    
    # 筛选目标
    targets = []
    for c in data:
        cid = c.get('id')
        if cid in sent: continue
        email = c.get('contactEmail', '')
        if not email or '@' not in email: continue
        ct = c.get('displayCreateTime', 0)
        if not ct: continue
        try:
            if datetime.fromtimestamp(int(ct)/1000).year < 2024:
                targets.append(c)
        except: pass
    
    print(f"目标客户: {len(targets)} 个")
    
    if not targets:
        print("✅ 没有待发送的客户")
        return
    
    random.shuffle(targets)
    to_send = targets[:remaining]
    print(f"本次发送: {len(to_send)} 封")
    print("-" * 60)
    
    ok = fail = 0
    for i, c in enumerate(to_send):
        cid = c.get('id')
        if cid in sent: continue
        
        email = c.get('contactEmail', '')
        name = (c.get('contactName') or c.get('name') or '').strip()
        first = name.split()[0] if name else 'there'
        region = c.get('displayRegion', '')
        
        subject = random.choice(SUBJECTS)
        body = random.choice(BODIES).format(
            greeting=random.choice(["Hi", "Hello", "Dear", "Hey"]) + f" {first},"
        )
        
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"  {ts} [{i+1}/{len(to_send)}] {name} <{email}> ({region})")
        
        r = send_email(email, subject, body)
        
        if r is True:
            print(f"         ✅ 成功")
            sent.add(cid)
            save_sent(sent)
            state['count'] = state.get('count', 0) + 1
            state['sent_ids'].append(cid)
            save_state(state)
            ok += 1
        else:
            print(f"         ❌ {r}")
            fail += 1
        
        # 随机延迟60-180秒
        if i < len(to_send) - 1:
            delay = random.randint(60, 180)
            m, s = divmod(delay, 60)
            print(f"         ⏱ 等待 {m}分{s}s...")
            time.sleep(delay)
    
    print(f"\n{'='*60}")
    print(f"📊 完成: ✅{ok} ❌{fail} | 今日累计: {state['count']}/{DAILY_LIMIT}")
    print(f"   历史累计: {len(sent)} 个客户")
    print("=" * 60)

if __name__ == '__main__':
    main()
