"""BLIIOT CRM老客户邮件召回 — 从CRM随机选客户 → 发送 → 记跟进"""
import json, smtplib, ssl, time, random, sys
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate

SD = Path(__file__).parent
SEL = SD / "_selected5.json"
PW = SD / ".smtp_password"

FE = "kali_foever@qq.com"
FN = "Kali | BLIIOT Technology"
SH = "smtp.qq.com"
SP = 465
SUBJ = "Following up | BLIIOT Industrial IoT Solutions"

BODY = """Hi {n},

Hope this email finds you well.

I hope you don't mind me reaching out. I'm Kali from BLIIOT (www.bliiot.com)— we previously discussed our industrial IoT gateways and remote monitoring solutions, which are widely used in solar energy, building automation, transformer monitoring, and industrial control applications.

I was wondering if you still remember us, and whether you're still interested in our products? Do you have any upcoming projects where our solutions might be a good fit?

We've also released several new products recently. If you'd like to learn more, please feel free to reach out anytime.

You can contact me directly at
Email: bl42@bliiot.com
WhatsApp: +86 17704014518.

Looking forward to hearing from you.

Best regards,
Kali
BLIIOT"""

def pw():
    if PW.exists(): return PW.read_text('utf-8').strip()
    print("❌ 无密码"); sys.exit(1)

def send(to, sub, body):
    ctx = ssl.create_default_context()
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((FN, FE)); msg["To"] = to
    msg["Subject"] = sub; msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP_SSL(SH, SP, context=ctx, timeout=30) as s:
            s.login(FE, pw()); s.sendmail(FE, [to], msg.as_string())
        return True
    except smtplib.SMTPRecipientsRefused: return "refused"
    except Exception as e: return str(e)

def crm(cid, content):
    try:
        import sqlite3
        d = Path.home() / 'AppData/Local/hermes/memories/脚本缓存/富通CRM/crm_followups.db'
        c = sqlite3.connect(str(d))
        c.execute("INSERT INTO followups (customer_id,customer_name,type,content,operator,source,synced) VALUES (?,'','邮件',?,'Kali Marfa','email',1)", (cid, content))
        c.commit(); c.close()
    except: pass

def main():
    cs = json.loads(SEL.read_text('utf-8'))
    print(f"📤 {len(cs)}封 → {FE}")
    for i, c in enumerate(cs):
        em = c.get('contactEmail','')
        nm = (c.get('contactName') or c.get('name') or '').strip()
        fn = nm.split()[0] if nm else 'there'
        if not em or '@' not in em: print(f"  [{i+1}] ⏭️ {em}"); continue
        b = BODY.format(n=fn)
        print(f"  [{i+1}] 📧 {em} ({fn})...", end=' ', flush=True)
        r = send(em, SUBJ, b)
        if r is True: print("✅"); crm(c.get('id',0), f"发送跟进邮件给{nm}")
        else: print(f"❌ {r}")
        if i < len(cs)-1:
            d = random.randint(60,150)
            m,s = divmod(d,60); print(f"     ⏱ {m}分{s}秒..."); time.sleep(d)
    print(f"\n✅ 完成")

if __name__ == '__main__': main()