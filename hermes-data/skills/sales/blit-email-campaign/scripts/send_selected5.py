"""
BLIIOT Email Campaign — filter CRM customers by date, random sample, send via QQ SMTP, log follow-ups
Usage: python send_selected5.py [--count 5] [--before 2024-01-01] [--country US]
"""
import sqlite3, random, time, logging, sys, os, json
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "memories" / "脚本缓存" / "富通CRM"
DB_PATH = DB_DIR / "crm_followups.db"
SMTP_PW = DB_DIR / ".smtp_password"

# ── Email template ──────────────────────────────────────────
EMAIL_SUBJECT = "Partnership Inquiry - BLIIOT Technology"

EMAIL_BODY = """\
Greetings {name} and the {company} team,

Hope this message finds you well.

I'm reaching out from BLIIOT Technology based in Shenzhen, a professional manufacturer of industrial IoT hardware with over 10 years of experience empowering clients across energy, automation, and industrial communication.

I noticed {company} is involved in {industry} — a domain where reliable and cost-effective hardware is critical.

We specialize in a comprehensive range of products designed for demanding industrial environments:
• Industrial gateways and protocol converters
• ARM-based edge computing controllers
• Remote I/O modules and data acquisition devices
• Industrial 4G/5G routers
• IoT data terminal units

Our products are trusted by system integrators and industrial partners in over 120 countries for their stability, flexibility, and competitive pricing.

Would you be open to a quick chat about how our solutions might support your ongoing projects? I'm happy to share more details or product documentation that aligns with your needs.

Looking forward to hearing from you.

Warm regards,

Kali
International Sales | BLIIOT Technology
Email: kalifoever@bliiot.com
Web: www.bliiot.com
"""

def load_password():
    with open(SMTP_PW) as f:
        return f.read().strip()

def get_customers_before(conn, date_before="2024-01-01", limit=None, country=None):
    cursor = conn.cursor()
    query = "SELECT * FROM customers WHERE createDate < ?"
    params = [date_before]
    if country:
        query += " AND country = ?"
        params.append(country)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    customers = [dict(zip(cols, row)) for row in rows]
    logging.info(f"Found {len(customers)} customers registered before {date_before}" +
                 (f" in {country}" if country else ""))
    if not customers:
        return []
    if limit:
        sample_size = min(limit, len(customers))
        customers = random.sample(customers, sample_size)
    return customers

def extract_email(customer):
    """Extract email from customer record (contacts JSON or email column)."""
    if customer.get("email"):
        return customer["email"].strip()
    contacts_raw = customer.get("contacts", "[]")
    if isinstance(contacts_raw, str):
        try:
            contacts = json.loads(contacts_raw)
            for c in contacts:
                if c.get("email"):
                    return c["email"].strip()
        except json.JSONDecodeError:
            pass
    return None

def add_followup(conn, customer_id, note, follow_type="email"):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO followups (customer_id, note, type, created_at, synced)
        VALUES (?, ?, ?, ?, 0)
    """, (customer_id, note, follow_type, datetime.now().isoformat()))
    conn.commit()
    return cursor.lastrowid

def run_campaign(num=5, date_before="2024-01-01", country=None):
    # Dynamically import blit_mailer — it's in the same directory
    sys.path.insert(0, str(DB_DIR))
    from blit_mailer import send_email

    conn = sqlite3.connect(str(DB_PATH))
    
    try:
        customers = get_customers_before(conn, date_before, limit=num, country=country)
        if not customers:
            logging.warning("No customers matched criteria.")
            return []
        
        password = load_password()
        results = []
        
        for i, c in enumerate(customers):
            name = c.get("contactName") or c.get("name", "Customer")
            company = c.get("name", "your company")
            industry = c.get("industryDetail") or c.get("industry", "industrial automation")
            email = extract_email(c)
            
            if not email:
                logging.warning(f"✗ {name} ({company}) — no email found, skipping")
                results.append({"name": name, "company": company, "email": None, "success": False, "reason": "no email"})
                continue
            
            body = EMAIL_BODY.format(name=name, company=company, industry=industry)
            
            logging.info(f"[{i+1}/{len(customers)}] Sending to {name} <{email}> ({c.get('country', '?')})")
            success, message = send_email(email, EMAIL_SUBJECT, body, sender_pass=password)
            
            if success:
                add_followup(conn, c["id"], f"Sent email to {email}: {EMAIL_SUBJECT}", "email")
                results.append({"name": name, "company": company, "email": email, "country": c.get("country"), "success": True})
                logging.info(f"  ✅ Sent OK")
            else:
                results.append({"name": name, "company": company, "email": email, "success": False, "reason": message})
                logging.error(f"  ❌ Failed: {message}")
            
            # Human-like delay between sends (1-2.5 min)
            if i < len(customers) - 1:
                delay = random.randint(60, 150)
                logging.info(f"  ⏳ Waiting {delay}s before next send...")
                time.sleep(delay)
        
        # Summary
        sent = sum(1 for r in results if r.get("success"))
        failed = sum(1 for r in results if not r.get("success"))
        logging.info(f"\n{'='*50}")
        logging.info(f"Campaign complete: {sent} sent, {failed} failed, {len(results)} total")
        
        return results
    
    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="BLIIOT Email Campaign")
    parser.add_argument("--count", type=int, default=5, help="Number of customers to email")
    parser.add_argument("--before", default="2024-01-01", help="Filter: createDate < this date")
    parser.add_argument("--country", default=None, help="Filter: specific country code")
    
    args = parser.parse_args()
    results = run_campaign(num=args.count, date_before=args.before, country=args.country)
    
    # Print summary table
    print(f"\n{'Name':<30} {'Email':<35} {'Country':<15} {'Status'}")
    print("-" * 95)
    for r in results:
        status = "✅" if r.get("success") else ("⏭️" if r.get("reason")=="no email" else "❌")
        email = r.get("email") or "(no email)"
        print(f"{r['name']:<30} {email:<35} {r.get('country','?'):<15} {status}")