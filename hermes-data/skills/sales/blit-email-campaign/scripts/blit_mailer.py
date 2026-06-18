"""
BLIIOT Mail Engine — SMTP wrapper for QQ personal email
Supports HTML/plain text, retry, and auth from password file.
"""
import smtplib, logging, time, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SENDER_EMAIL = "kali_foever@qq.com"
DEFAULT_SENDER_NAME = "Kali | BLIIOT Technology"
BASE_DIR = Path(os.environ.get("HERMES_HOME", Path.home() / "AppData" / "Local" / "hermes"))
CRM_DIR = BASE_DIR / "memories" / "脚本缓存" / "富通CRM"
PASSWORD_FILE = BASE_DIR / "memories" / "脚本缓存" / "产品推广" / ".smtp_password"

def send_email(
    to: str,
    subject: str,
    body: str,
    sender_name: str = DEFAULT_SENDER_NAME,
    sender_pass: str = None,
    is_html: bool = False,
    max_retries: int = 2,
) -> tuple[bool, str]:
    """
    Send email via QQ SMTP.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        sender_name: Display name for sender
        sender_pass: SMTP authorization code (if None, load from PASSWORD_FILE)
        is_html: If True, body is rendered as HTML
        max_retries: Number of retries on failure
    
    Returns:
        (success: bool, message: str)
    """
    if not sender_pass:
        try:
            with open(PASSWORD_FILE) as f:
                sender_pass = f.read().strip()
        except FileNotFoundError:
            return False, f"Password file not found: {PASSWORD_FILE}"
    
    if not sender_pass:
        return False, "Empty SMTP password"
    
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{sender_name} <{SENDER_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    
    if is_html:
        msg.attach(MIMEText(body, "html", "utf-8"))
    else:
        msg.attach(MIMEText(body, "plain", "utf-8"))
    
    for attempt in range(1 + max_retries):
        try:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
                server.login(SENDER_EMAIL, sender_pass)
                server.sendmail(SENDER_EMAIL, [to], msg.as_string())
            return True, "OK"
        except smtplib.SMTPAuthenticationError as e:
            return False, f"SMTP auth failed: {e}"
        except smtplib.SMTPRecipientsRefused as e:
            return False, f"Recipient refused: {e}"
        except (smtplib.SMTPException, TimeoutError, ConnectionError) as e:
            if attempt < max_retries:
                wait = 5 * (attempt + 1)
                logging.warning(f"SMTP attempt {attempt+1} failed: {e}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                return False, str(e)
    
    return False, "Max retries exceeded"


def send_email_with_attachment(to, subject, body, attachment_path, sender_pass=None):
    """Send email with a file attachment."""
    if not sender_pass:
        with open(PASSWORD_FILE) as f:
            sender_pass = f.read().strip()
    
    msg = MIMEMultipart()
    msg["From"] = f"{DEFAULT_SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    
    # Attach file
    from email.mime.base import MIMEBase
    from email import encoders
    
    with open(attachment_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{Path(attachment_path).name}"')
        msg.attach(part)
    
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
        server.login(SENDER_EMAIL, sender_pass)
        server.sendmail(SENDER_EMAIL, [to], msg.as_string())
    
    return True, "OK"


def test_connection():
    """Quick SMTP connectivity test."""
    pw = open(PASSWORD_FILE).read().strip()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SENDER_EMAIL, pw)
            server.quit()
        return True, "SMTP connection OK"
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    # Quick test
    import sys
    test_to = sys.argv[1] if len(sys.argv) > 1 else None
    if test_to:
        ok, msg = send_email(test_to, "Test from BLIIOT Mailer", 
                            f"Hello!\n\nThis is a test email from BLIIOT Mail Engine.\nSent at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\nBest,\nKali")
        print(f"{'✅' if ok else '❌'} {msg}")
    else:
        ok, msg = test_connection()
        print(f"Connection test: {'✅' if ok else '❌'} {msg}")