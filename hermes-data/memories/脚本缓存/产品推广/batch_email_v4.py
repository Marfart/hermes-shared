"""
BLIIOT 每日拟人邮件发送 — 分批执行版
每批5个客户，由cron分批调用
用法: python batch_email.py [batch_size=5]
"""
import json, smtplib, ssl, time, random, sys
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate

SD = Path(__file__).parent
DATA_FILE = Path.home() / "Desktop/Working/富通CRM_公海客户_全量.json"
SENT_LOG = SD / ".sent_log_v4.json"
DAILY_STATE = SD / ".daily_state_v4.json"
CRM_DB = Path.home() / "AppData/Local/hermes/memories/脚本缓存/富通CRM/crm_followups.db"

FE = "kali_foever@qq.com"
FN = "Kali | BLIIOT Technology"
SH = "smtp.qq.com"
SP = 465
DAILY_LIMIT = 50
MIN_DELAY = 60
MAX_DELAY = 180

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
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    pw = get_pw()
    if not pw:
        print("❌ 无SMTP密码"); return
    
    data = json.loads(DATA_FILE.read_text('utf-8'))
    sent = load_sent()
    state = load_state()
    
    today_count = state.get('count', 0)
    remaining = DAILY_LIMIT - today_count
    
    print(f"今日已发: {today_count}/{DAILY_LIMIT} | 剩余配额: {remaining}")
    
    if remaining <= 0:
        print(f"✅ 今日已达上限"); return
    
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
    
    random.shuffle(targets)
    to_send = targets[:min(batch_size, remaining)]
    
    print(f"目标: {len(targets)} | 本批发送: {len(to_send)}")
    print("-" * 50)
    
    ok = fail = 0
    for i, c in enumerate(to_send):
        cid = c.get('id')
        if cid in sent: continue
        
        email = c.get('contactEmail', '')
        name = (c.get('contactName') or c.get('name') or '').strip()
        first = name.split()[0] if name else 'there'
        region = c.get('displayRegion', '')
        
        if cid in sent: continue
        
        subject = random.choice(SUBJECTS)
        body = random.choice(BODIES).format(
            greeting=random.choice(["Hi", "Hello", "Dear", "Hey"]) + f" {first},"
        )
        
        r = send_email(email, subject, body)
        ts = datetime.now().strftime('%H:%M:%S')
        
        if r is True:
            print(f"  {ts} ✅ {name} ({region})")
            sent.add(cid)
            save_sent(sent)
            state['count'] = state.get('count', 0) + 1
            state['sent_ids'].append(cid)
            save_state(state)
            ok += 1
        else:
            print(f"  {ts} ❌ {name}: {r}")
            fail += 1
        
        if i < len(to_send) - 1:
            d = random.randint(MIN_DELAY, MAX_DELAY)
            m, s = divmod(d, 60)
            print(f"       等待 {m}分{s}s...")
            time.sleep(d)
    
    print(f"\n本批: ✅{ok} ❌{fail} | 今日累计: {state['count']}/{DAILY_LIMIT}")

if __name__ == '__main__':
    main()
