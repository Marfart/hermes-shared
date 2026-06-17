#!/usr/bin/env python3
"""Close all WhatsApp targets and open fresh"""
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

# Close all WhatsApp targets
resp = send_cmd('Target.getTargets')
targets = resp.get('result', {}).get('targetInfos', [])
print(f'Targets: {len(targets)}')

for t in targets:
    if 'web.whatsapp.com' in t.get('url', ''):
        print(f'Closing: {t["title"]} | {t["targetId"][:20]}')
        send_cmd('Target.closeTarget', {'targetId': t['targetId']})
        time.sleep(0.5)

time.sleep(2)

# Create fresh WhatsApp target
print('\nCreating fresh WhatsApp target...')
resp = send_cmd('Target.createTarget', {'url': 'https://web.whatsapp.com'})
new_tid = resp['result']['targetId']
print(f'New target: {new_tid}')

# Wait for load
print('Waiting 10s for WhatsApp to load...')
time.sleep(10)

# Attach and check
resp = send_cmd('Target.attachToTarget', {'targetId': new_tid, 'flatten': True})
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
print(f'Body: {r.get("value", "?")}')

# Check for QR or login
resp = send_session('Runtime.evaluate', {
    'expression': '!!document.querySelector("canvas")',
    'returnByValue': True
})
r = resp.get('result', {}).get('result', {})
print(f'Has QR: {r.get("value", "?")}')

# Check chat list
resp = send_session('Runtime.evaluate', {
    'expression': 'document.querySelectorAll("[role=\\"row\\"]").length',
    'returnByValue': True
})
r = resp.get('result', {}).get('result', {})
print(f'Chat rows: {r.get("value", "?")}')

ws.close()
