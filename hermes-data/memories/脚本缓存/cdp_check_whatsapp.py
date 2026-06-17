#!/usr/bin/env python3
"""Check WhatsApp Web status via CDP"""
import json
import time
import urllib.request
import websocket

pages = json.loads(urllib.request.urlopen('http://127.0.0.1:9223/json/version').read())
browser_ws = pages['webSocketDebuggerUrl']

ws = websocket.create_connection(browser_ws, timeout=15)
msg_id = 0

def send_cmd(method, params=None):
    global msg_id
    msg_id += 1
    cmd = {'id': msg_id, 'method': method, 'params': params or {}}
    ws.send(json.dumps(cmd))
    while True:
        resp = json.loads(ws.recv())
        if resp.get('id') == msg_id:
            return resp

# Find WhatsApp target
resp = send_cmd('Target.getTargets')
targets = resp.get('result', {}).get('targetInfos', [])
print(f'Targets: {len(targets)}')

whatsapp = None
for t in targets:
    if 'web.whatsapp.com' in t.get('url', '') and t.get('type') == 'page':
        whatsapp = t
        print(f'Found: {t["title"]} | {t["url"][:60]}')

if whatsapp:
    tid = whatsapp['targetId']
    resp = send_cmd('Target.attachToTarget', {'targetId': tid, 'flatten': True})
    sid = resp['result']['sessionId']
    
    def send_session(method, params=None):
        global msg_id
        msg_id += 1
        cmd = {'id': msg_id, 'sessionId': sid, 'method': method, 'params': params or {}}
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get('id') == msg_id:
                return resp
    
    # Check status
    resp = send_session('Runtime.evaluate', {
        'expression': 'document.body.innerText.substring(0, 300)',
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    val = r.get('value', 'no value')
    print(f'Body text: {val}')
    
    # Check for QR code
    resp = send_session('Runtime.evaluate', {
        'expression': '!!document.querySelector("canvas")',
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    print(f'Has QR canvas: {r.get("value", "?")}')
    
    # Check chat list
    resp = send_session('Runtime.evaluate', {
        'expression': 'document.querySelectorAll("[role=\\"row\\"]").length',
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    print(f'Chat rows: {r.get("value", "?")}')
    
    # Get chat names
    resp = send_session('Runtime.evaluate', {
        'expression': """
(() => {
    const rows = document.querySelectorAll('[role="row"]');
    return JSON.stringify(Array.from(rows).slice(0, 20).map(r => r.textContent.trim().substring(0, 80)));
})()
""",
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    print(f'Chats: {r.get("value", "[]")}')

ws.close()
