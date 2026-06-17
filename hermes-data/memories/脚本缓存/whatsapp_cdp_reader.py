#!/usr/bin/env python3
"""CDP WhatsApp Reader — connects to local Chrome via CDP WebSocket"""
import json
import time
import random
import base64
import sys
import websocket

CDP_URL = "ws://127.0.0.1:9223/devtools/browser/bd38c27e-b8ab-490a-96db-bb81f147cab2"

class CDPClient:
    def __init__(self, url):
        self.ws = websocket.create_connection(url, timeout=30)
        self.msg_id = 0
        self.target_id = None
    
    def send(self, method, params=None):
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method, "params": params or {}}
        self.ws.send(json.dumps(msg))
        return self._recv()
    
    def _recv(self):
        resp = json.loads(self.ws.recv())
        while "id" not in resp:
            resp = json.loads(self.ws.recv())
        return resp
    
    def create_target(self, url):
        resp = self.send("Target.createTarget", {"url": url})
        self.target_id = resp["result"]["targetId"]
        return self.target_id
    
    def send_to_target(self, method, params=None):
        """Send command to a specific target page"""
        self.msg_id += 1
        msg = {
            "id": self.msg_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": f"fetch('http://127.0.0.1:9223/json/activate?{self.target_id}')",
                "returnByValue": True
            }
        }
        # Actually, we need to use Target.sendMessageToTarget
        self.msg_id += 1
        msg = {
            "id": self.msg_id,
            "method": "Target.sendMessageToTarget",
            "params": {
                "targetId": self.target_id,
                "message": json.dumps({
                    "id": 1,
                    "method": method,
                    "params": params or {}
                })
            }
        }
        self.ws.send(json.dumps(msg))
        return self._recv()
    
    def evaluate(self, expression):
        """Evaluate JS in the target page"""
        self.msg_id += 1
        msg = {
            "id": self.msg_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            }
        }
        # Need to send to target via Target.sendMessageToTarget
        self.msg_id += 1
        inner_id = 1
        inner_msg = json.dumps({
            "id": inner_id,
            "method": "Runtime.evaluate",
            "params": {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True
            }
        })
        msg = {
            "id": self.msg_id,
            "method": "Target.sendMessageToTarget",
            "params": {
                "targetId": self.target_id,
                "message": inner_msg
            }
        }
        self.ws.send(json.dumps(msg))
        
        # Receive the response
        while True:
            resp = json.loads(self.ws.recv())
            if "id" in resp and resp["id"] == self.msg_id:
                # This is the outer response
                inner_resp_str = resp.get("result", {}).get("message", "")
                if inner_resp_str:
                    inner_resp = json.loads(inner_resp_str)
                    return inner_resp.get("result", {})
            elif "method" in resp and resp.get("method") == "Target.receivedMessageFromTarget":
                inner_str = resp.get("params", {}).get("message", "")
                if inner_str:
                    inner = json.loads(inner_str)
                    if inner.get("id") == inner_id:
                        return inner.get("result", {})
    
    def close(self):
        self.ws.close()

print("Connecting to CDP...")
client = CDPClient(CDP_URL)

# First, list existing targets
resp = client.send("Target.getTargets")
targets = resp.get("result", {}).get("targetInfos", [])
print(f"Found {len(targets)} target(s):")
for t in targets:
    print(f"  [{t['targetId'][:20]}...] {t['title'][:60]} | {t['url'][:80]}")

# Check if WhatsApp is already open
whatsapp_target = None
for t in targets:
    if "web.whatsapp.com" in t.get("url", ""):
        whatsapp_target = t["targetId"]
        print(f"\nFound WhatsApp Web target: {t['targetId']}")
        break

if not whatsapp_target:
    print("\nWhatsApp not open. Creating new target...")
    resp = client.send("Target.createTarget", {"url": "https://web.whatsapp.com"})
    whatsapp_target = resp["result"]["targetId"]
    print(f"Created target: {whatsapp_target}")
    print("Waiting for WhatsApp to load...")
    time.sleep(5)

client.target_id = whatsapp_target
print(f"\nUsing target: {whatsapp_target}")

# Activate the target
resp = client.send("Target.activateTarget", {"targetId": whatsapp_target})
print(f"Activated: {resp}")

# Wait for page to load
time.sleep(3)

# Get page title
result = client.evaluate("document.title")
print(f"Page title: {result}")

# Get all chat elements
result = client.evaluate("""
(() => {
    const chats = document.querySelectorAll('[data-testid="chat-list"] [role="row"]');
    const results = [];
    for (let i = 0; i < Math.min(chats.length, 10); i++) {
        const chat = chats[i];
        const nameEl = chat.querySelector('[data-testid="conversation-info-header"] span, [dir="auto"]');
        const msgEl = chat.querySelector('[data-testid="last-msg"] span, [data-pre-plain-text]');
        results.push({
            name: nameEl ? nameEl.textContent : 'unknown',
            lastMsg: msgEl ? msgEl.textContent : '',
        });
    }
    return results;
})()
""")
print(f"\nChat list: {json.dumps(result, ensure_ascii=False, indent=2)}")

client.close()
