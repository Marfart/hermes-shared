"""小马轮询学弟消息 v2 - 发现新消息通过Telegram Bot API通知群"""
import urllib.request
import urllib.parse
import json
import os

RELAY = "https://nsw-sandra-reliable-either.trycloudflare.com"
CHAT_ID = "-5381168616"
ENV_PATH = r"C:\Users\Admin\AppData\Local\hermes\.env"

def get_bot_token():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#") or not stripped:
                    continue
                if "TELEGRAM_BOT_TOKEN" in stripped:
                    parts = stripped.split("=", 1)
                    if len(parts) > 1:
                        token = parts[1].strip().strip('"').strip("'")
                        if token and len(token) > 10:
                            return token
    return ""

def notify_telegram(text):
    bot_token = get_bot_token()
    if not bot_token:
        print(f"[no token] {text[:100]}")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode("utf-8")
    proxy_handler = urllib.request.ProxyHandler({
        "https": "http://127.0.0.1:7897",
        "http": "http://127.0.0.1:7897"
    })
    opener = urllib.request.build_opener(proxy_handler)
    try:
        req = urllib.request.Request(url, data=data)
        resp = opener.open(req, timeout=15)
        result = json.loads(resp.read().decode("utf-8"))
        if result.get("ok"):
            print("TG ok")
        else:
            print(f"TG fail: {result.get('description', '?')}")
    except Exception:
        try:
            req2 = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req2, timeout=15)
            print("TG ok (direct)")
        except Exception as e2:
            print(f"TG all fail: {e2}")

def poll_and_notify():
    try:
        url = f"{RELAY}/poll/" + urllib.parse.quote("小马")
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        if data.get("count", 0) == 0:
            return
        for msg in data.get("messages", []):
            content = msg.get("content", "")
            notify_text = f"📨 <b>学弟发来消息：</b>\n\n{content}"
            notify_telegram(notify_text)
            msg_id = msg.get("id", "")
            if msg_id:
                try:
                    del_req = urllib.request.Request(f"{RELAY}/msg/{msg_id}", method="DELETE")
                    urllib.request.urlopen(del_req, timeout=10)
                except Exception:
                    pass
    except Exception:
        pass

if __name__ == "__main__":
    poll_and_notify()
