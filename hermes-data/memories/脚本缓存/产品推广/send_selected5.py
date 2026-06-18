"""BLIIOT 拟人邮件发送 — 针对富通CRM老客户 v3 (防重复)"""
import json, smtplib, ssl, time, random, sys, os
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

SD = Path(__file__).parent
SEL = SD / "_selected5.json"
PW = SD / ".smtp_password"
CRM_DB = Path.home() / "AppData/Local/hermes/memories/脚本缓存/富通CRM/crm_followups.db"
SENT_LOG = SD / ".sent_log.json"

FE = "kali_foever@qq.com"
FN = "Kali | BLIIOT Technology"
SH = "smtp.qq.com"
SP = 465
SUBJ = "Following up | BLIIOT Industrial IoT Solutions"

BODY = """Hi {n},

Hope this email finds you well.

I hope you don't mind me reaching out. I'm Kali from BLIIOT (www.bliiot.com) — we previously discussed our industrial IoT gateways and remote monitoring solutions, which are widely used in solar energy, building automation, transformer monitoring, and industrial control applications.

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

def load_sent():
    if SENT_LOG.exists():
        return set(json.loads(SENT_LOG.read_text('utf-8')))
    return set()

def save_sent(sent):
    SENT_LOG.write_text(json.dumps(list(sent), ensure_ascii=False))

def send(to, sub, body):
    ctx = ssl.create_default_context()
    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr((FN, FE))
    msg["To"] = to
    msg["Subject"] = sub
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(body, "plain", "utf-8"))
    try:
        with smtplib.SMTP_SSL(SH, SP, context=ctx, timeout=30) as s:
            s.login(FE, pw())
            s.sendmail(FE, [to], msg.as_string())
        return True
    except smtplib.SMTPRecipientsRefused:
        return "refused"
    except Exception as e:
        return str(e)

def crm(cid, name, content):
    try:
        import sqlite3
        c = sqlite3.connect(str(CRM_DB))
        c.execute(
            "INSERT INTO followups (customer_id,customer_name,type,content,operator,source,synced) VALUES (?,?,?,?,?,?,1)",
            (cid, name, "邮件", content, "Kali Marfa", "email")
        )
        c.commit()
        c.close()
        print(f"     📝 CRM跟进已记录", flush=True)
    except Exception as e:
        print(f"     ⚠️ CRM记录失败: {e}", flush=True)

def main():
    cs = json.loads(SEL.read_text('utf-8'))
    sent = load_sent()
    
    # 过滤掉已发送的
    pending = [c for c in cs if c['id'] not in sent]
    
    print(f"📤 总计 {len(cs)} 个客户 | 已发 {len(sent)} | 待发 {len(pending)}", flush=True)
    
    if not pending:
        print("✅ 全部已发送，无需重复发送", flush=True)
        return
    
    sent_count = 0
    fail_count = 0
    
    for i, c in enumerate(pending):
        em = c.get('contactEmail', '')
        nm = (c.get('contactName') or c.get('name') or '').strip()
        fn = nm.split()[0] if nm else 'there'
        cid = c.get('id', 0)
        region = c.get('displayRegion', '')
        
        if not em or '@' not in em:
            print(f"  [{i+1}] ⏭️ 无邮箱: {nm}", flush=True)
            continue
        
        print(f"  [{i+1}] 📧 {nm} <{em}> ({region})...", end=' ', flush=True)
        b = BODY.format(n=fn)
        r = send(em, SUBJ, b)
        
        if r is True:
            print(f"✅ 发送成功", flush=True)
            sent.add(cid)
            save_sent(sent)  # 立即保存，防止重复
            crm(cid, nm, f"发送跟进邮件给{nm}({em})")
            sent_count += 1
        else:
            print(f"❌ {r}", flush=True)
            fail_count += 1
        
        if i < len(pending) - 1:
            d = random.randint(60, 150)
            m, s = divmod(d, 60)
            print(f"     ⏱ 等待 {m}分{s}秒...", flush=True)
            time.sleep(d)
    
    print(f"\n{'='*50}", flush=True)
    print(f"📊 完成: 成功 {sent_count} | 失败 {fail_count} | 总计 {len(pending)}", flush=True)

if __name__ == '__main__':
    main()
