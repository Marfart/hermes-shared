#!/usr/bin/env python3
"""Check WhatsApp status more carefully"""
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
whatsapp = None
for t in targets:
    if 'web.whatsapp.com' in t.get('url', '') and t.get('type') == 'page':
        whatsapp = t
        break

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
    
    # Full page HTML analysis
    resp = send_session('Runtime.evaluate', {
        'expression': """
(() => {
    const info = {};
    info.title = document.title;
    info.url = window.location.href;
    info.hasCanvas = !!document.querySelector('canvas');
    info.hasQR = !!document.querySelector('img[alt*=\"QR\"]');
    info.hasLoginBtn = !!document.querySelector('[data-testid=\"login\"]');
    info.hasChatList = !!document.querySelector('[data-testid=\"chat-list\"]');
    info.hasMainApp = !!document.querySelector('#app .two');
    info.hasE2E = document.body.innerText.includes('端到端加密');
    info.hasLinkDevice = document.body.innerText.includes('链接设备') || document.body.innerText.includes('Link a device');
    info.bodyPreview = document.body.innerText.substring(0, 500);
    return JSON.stringify(info);
})()
""",
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    print(f'Status: {r.get("value", "?")}')

ws.close()
