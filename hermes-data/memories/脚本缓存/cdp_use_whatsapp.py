#!/usr/bin/env python3
"""Click 'Use this window' on WhatsApp and read chats"""
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
        print(f'Found: {t["title"]}')

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
    
    # Click "Use this window" button
    resp = send_session('Runtime.evaluate', {
        'expression': """
(() => {
    const buttons = document.querySelectorAll('button, div[role="button"]');
    for (const btn of buttons) {
        if (btn.textContent.includes('使用此窗口') || btn.textContent.includes('Use this window')) {
            btn.click();
            return 'Clicked: ' + btn.textContent.trim();
        }
    }
    return 'Button not found. Buttons: ' + Array.from(buttons).map(b => b.textContent.trim()).join(' | ');
})()
""",
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    print(f'Click result: {r.get("value", "?")}')
    
    # Wait for WhatsApp to load
    print('Waiting for WhatsApp to load...')
    time.sleep(5)
    
    # Check status
    resp = send_session('Runtime.evaluate', {
        'expression': 'document.body.innerText.substring(0, 200)',
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    print(f'Body: {r.get("value", "?")}')
    
    # Get chat list
    resp = send_session('Runtime.evaluate', {
        'expression': """
(() => {
    const rows = document.querySelectorAll('[role="row"]');
    const results = [];
    for (let i = 0; i < Math.min(rows.length, 25); i++) {
        const row = rows[i];
        const spans = row.querySelectorAll('span[dir="auto"]');
        const name = spans.length > 0 ? spans[0].textContent.trim() : '';
        const lastMsg = spans.length > 1 ? spans[spans.length-1].textContent.trim().substring(0, 100) : '';
        if (name) results.push({name: name, lastMsg: lastMsg});
    }
    return JSON.stringify(results);
})()
""",
        'returnByValue': True
    })
    r = resp.get('result', {}).get('result', {})
    chats = json.loads(r.get('value', '[]'))
    print(f'\nChat list ({len(chats)}):')
    for c in chats:
        print(f'  {c["name"]}: {c["lastMsg"][:80]}')

ws.close()
