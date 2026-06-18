import json, asyncio, websockets

async def main():
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5)
    pages = json.loads(resp.read())
    
    login_page = None
    for p in pages:
        u = p.get('url','')
        if 'cloud.joinf.com/login' in u:
            login_page = p
            break
    
    if not login_page:
        print("No login page found")
        return
    
    ws_url = login_page['webSocketDebuggerUrl']
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            r = json.loads(await ws.recv())
            return r
        
        async def js(expr):
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            return r.get("result",{}).get("result",{}).get("value")
        
        # Login
        await send("Page.navigate", {"url": "https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0"})
        await asyncio.sleep(3)
        await js("document.getElementById('loginID').value='bliiot03'")
        await js("document.getElementById('loginPassword').value='Kali1314520!'")
        await js("document.getElementById('loginBtn').click()")
        await asyncio.sleep(5)
        url = await js("window.location.href")
        print(f"Login result: {url[:100]}")
        
        if 'ticket' in url:
            print("✅ Logged in successfully")
        elif 'login' in url:
            print("❌ Still on login page")
            return

asyncio.run(main())