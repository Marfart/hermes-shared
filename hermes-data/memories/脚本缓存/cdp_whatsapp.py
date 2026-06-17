import asyncio
import json
import websocket

async def main():
    # 1. Get page list from CDP
    import urllib.request
    pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9223/json").read())
    
    # Find WhatsApp page
    ws_url = None
    for p in pages:
        if "web.whatsapp.com" in p.get("url", ""):
            ws_url = p["webSocketDebuggerUrl"]
            break
    
    if not ws_url:
        print("WhatsApp page not found")
        return
    
    print(f"Connecting to: {ws_url[:60]}...")
    
    # 2. Connect via websocket
    ws = websocket.create_connection(ws_url, timeout=10)
    
    msg_id = 1
    def send_cmd(method, params={}):
        nonlocal msg_id
        cmd = {"id": msg_id, "method": method, "params": params}
        msg_id += 1
        ws.send(json.dumps(cmd))
        # Wait for response
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == cmd["id"]:
                return resp
    
    # 3. Navigate to WhatsApp
    send_cmd("Page.enable")
    
    # 4. Get all messages from current chat
    result = send_cmd("Runtime.evaluate", {
        "expression": """
        (() => {
            const messages = document.querySelectorAll('[data-pre-plain-text]');
            const results = [];
            messages.forEach(m => {
                const text = m.textContent || '';
                if (text.trim().length > 0) results.push(text.substring(0, 500));
            });
            return JSON.stringify(results);
        })()
        """,
        "returnByValue": True
    })
    
    msgs = json.loads(result["result"]["result"]["value"])
    print(f"Found {len(msgs)} messages")
    for m in msgs[:5]:
        print(f"  {m[:100]}")
    
    # 5. Find Guillaume Jonville in chat list and click
    result = send_cmd("Runtime.evaluate", {
        "expression": """
        (() => {
            const rows = document.querySelectorAll('[role="row"]');
            for (const row of rows) {
                if (row.textContent.includes('Guillaume Jonville')) {
                    row.click();
                    return 'Clicked Guillaume';
                }
            }
            return 'Not found';
        })()
        """,
        "returnByValue": True
    })
    print(f"Click result: {result['result']['result']['value']}")
    
    # 6. Wait and get messages
    import time
    time.sleep(3)
    
    result = send_cmd("Runtime.evaluate", {
        "expression": """
        (() => {
            const messages = document.querySelectorAll('[data-pre-plain-text]');
            const results = [];
            messages.forEach(m => {
                const text = m.textContent || '';
                if (text.trim().length > 0) results.push(text.substring(0, 500));
            });
            return JSON.stringify(results);
        })()
        """,
        "returnByValue": True
    })
    
    msgs = json.loads(result["result"]["result"]["value"])
    print(f"\nGuillaume's messages ({len(msgs)}):")
    for m in msgs:
        print(f"  {m[:200]}")
    
    ws.close()

asyncio.run(main())
