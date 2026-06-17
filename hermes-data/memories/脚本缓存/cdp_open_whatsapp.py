#!/usr/bin/env python3
"""Open WhatsApp Web via CDP and read chat list"""
import json
import time
import random
import urllib.request
import websocket

# Step 1: Get the browser WebSocket URL
pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9223/json/version").read())
browser_ws = pages["webSocketDebuggerUrl"]
print(f"Browser WS: {browser_ws}")

# Step 2: Connect to browser-level CDP
ws = websocket.create_connection(browser_ws, timeout=15)
msg_id = 0

def send_cmd(method, params=None):
    global msg_id
    msg_id += 1
    cmd = {"id": msg_id, "method": method, "params": params or {}}
    ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp

# Step 3: Create a new target for WhatsApp Web
print("\nOpening WhatsApp Web...")
resp = send_cmd("Target.createTarget", {"url": "https://web.whatsapp.com"})
target_id = resp["result"]["targetId"]
print(f"Target ID: {target_id}")

# Step 4: Wait for page to load
print("Waiting for WhatsApp to load...")
time.sleep(8)

# Step 5: Activate the target and get its page WS URL
resp = send_cmd("Target.attachToTarget", {"targetId": target_id, "flatten": True})
session_id = resp["result"]["sessionId"]
print(f"Session ID: {session_id}")

# Step 6: Send commands via the session
def send_session(method, params=None):
    global msg_id
    msg_id += 1
    cmd = {"id": msg_id, "sessionId": session_id, "method": method, "params": params or {}}
    ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(ws.recv())
        if resp.get("id") == msg_id:
            return resp

# Check page title
resp = send_session("Runtime.evaluate", {
    "expression": "document.title",
    "returnByValue": True
})
title = resp.get("result", {}).get("result", {}).get("value", "unknown")
print(f"Page title: {title}")

# Check if QR code is showing or already logged in
resp = send_session("Runtime.evaluate", {
    "expression": "document.querySelector('canvas') !== null ? 'QR code visible' : 'No QR code'",
    "returnByValue": True
})
print(f"Login status: {resp.get('result', {}).get('result', {}).get('value', 'unknown')}")

# Get chat list
resp = send_session("Runtime.evaluate", {
    "expression": """
(() => {
    const rows = document.querySelectorAll('[role="row"]');
    const results = [];
    for (let i = 0; i < Math.min(rows.length, 20); i++) {
        const row = rows[i];
        const nameEl = row.querySelector('[dir="auto"]');
        const msgEl = row.querySelector('[class*="message"] span, [dir="auto"]:last-child');
        if (nameEl) {
            results.push({
                name: nameEl.textContent.trim(),
                preview: msgEl ? msgEl.textContent.trim().substring(0, 100) : ''
            });
        }
    }
    return JSON.stringify(results);
})()
""",
    "returnByValue": True
})
chats_raw = resp.get("result", {}).get("result", {}).get("value", "[]")
chats = json.loads(chats_raw)
print(f"\nChat list ({len(chats)}):")
for c in chats:
    print(f"  {c['name']}: {c['preview'][:80]}")

ws.close()
