import asyncio
import json
import websocket
import urllib.request

async def main():
    # 1. 获取WhatsApp页面
    pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9223/json").read())
    
    ws_url = None
    for p in pages:
        if "web.whatsapp.com" in p.get("url", ""):
            ws_url = p["webSocketDebuggerUrl"]
            break
    
    if not ws_url:
        print("WhatsApp page not found")
        return
    
    print(f"Connecting to CDP...")
    ws = websocket.create_connection(ws_url, timeout=10)
    
    msg_id = 1
    def send_cmd(method, params={}):
        nonlocal msg_id
        cmd = {"id": msg_id, "method": method, "params": params}
        msg_id += 1
        ws.send(json.dumps(cmd))
        while True:
            resp = json.loads(ws.recv())
            if resp.get("id") == cmd["id"]:
                return resp
    
    # Enable Page domain
    send_cmd("Page.enable")
    send_cmd("Runtime.enable")
    
    # 2. 先看看当前页面状态
    result = send_cmd("Runtime.evaluate", {
        "expression": "document.title",
        "returnByValue": True
    })
    print(f"Page title: {result['result']['result']['value']}")
    
    # 3. 点击Guillaume Jonville的聊天
    result = send_cmd("Runtime.evaluate", {
        "expression": """
        (() => {
            const rows = document.querySelectorAll('[role="row"]');
            for (const row of rows) {
                if (row.textContent.includes('Guillaume Jonville')) {
                    row.click();
                    return 'Clicked Guillaume Jonville';
                }
            }
            return 'Not found';
        })()
        """,
        "returnByValue": True
    })
    print(f"Click: {result['result']['result']['value']}")
    
    # 4. 等聊天加载
    import time
    time.sleep(3)
    
    # 5. 滚到顶部看完整对话
    result = send_cmd("Runtime.evaluate", {
        "expression": """
        (() => {
            const panel = document.querySelector('[role="application"] [tabindex="-1"]') || 
                          document.querySelector('[role="region"]');
            if (panel) panel.scrollTop = 0;
            return 'Scrolled to top';
        })()
        """,
        "returnByValue": True
    })
    
    time.sleep(2)
    
    # 6. 读取所有消息
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
    print(f"\nGuillaume Jonville 的对话 ({len(msgs)}条):")
    print("=" * 60)
    for m in msgs:
        print(f"  {m[:300]}")
        print()
    
    ws.close()

asyncio.run(main())
