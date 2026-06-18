import json, asyncio, websockets

async def run():
    # Get CDP page ID
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5)
    pages = json.loads(resp.read())
    
    ws_url = None
    for p in pages:
        u = p.get('url', '')
        if 'cloud.joinf.com/login' in u:
            ws_url = p['webSocketDebuggerUrl']
            break
    
    if not ws_url:
        print("No login page found on 9226")
        return
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            resp = json.loads(await ws.recv())
            return resp
        
        async def js(expr):
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            return r.get("result",{}).get("result",{}).get("value")
        
        # Step 1: Login
        print("Logging in...")
        await send("Page.navigate", {"url": "https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0"})
        await asyncio.sleep(3)
        
        await js("document.getElementById('loginID').value='bliiot03'")
        await js("document.getElementById('loginPassword').value='Kali1314520!'")
        await js("document.getElementById('loginBtn').click()")
        await asyncio.sleep(5)
        
        url = await js("window.location.href")
        print(f'After login: {url[:100]}')
        
        # Step 2: Wait for CRM page to fully load
        if 'customer' in url:
            print("On customers page! Waiting for Vue to initialize...")
        else:
            # Try navigating directly
            await send("Page.navigate", {"url": "https://trade.joinf.com/tms/customer/customers?tab=0"})
            await asyncio.sleep(4)
            url = await js("window.location.href")
            print(f'After nav: {url[:100]}')
        
        # Step 3: Wait for page to fully render Vue app
        await asyncio.sleep(3)
        
        # Step 4: Verify read API works
        r = await js('''
            (async() => {
                let resp = await fetch('/rapi/d/customers?num=0&paging=true&size=3');
                let j = await resp.json();
                return JSON.stringify({ok: j.success, count: j.data?.values?.length});
            })()
        ''')
        print(f'Read API: {r}')
        
        # Step 5: Try write - NO X-Headers, rely on Cookie only
        r = await js('''
            (async() => {
                let resp = await fetch('/rapi/m/follow/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        models: [
                            {columnName:"dataName", value:229629960, displayValue:"Juan Carlos Martinez Quintero", displayOriginalValue:229629960},
                            {columnName:"contactContent", value:"[邮件] test follow-up", displayValue:"", displayOriginalValue:""},
                            {columnName:"bgColor", value:"2B579A", displayValue:"", displayOriginalValue:""},
                            {columnName:"method", dict:true, value:"邮件", displayValue:"", displayOriginalValue:""},
                            {columnName:"planningTime", value:"2026-06-18 22:00:00", displayValue:"", displayOriginalValue:""},
                            {columnName:"feedbackOperator", value:"183006", displayValue:"", displayOriginalValue:""}
                        ]
                    })
                });
                let j = await resp.json();
                return JSON.stringify({status: resp.status, ok: j.success, msg: j.errMsg, data: j.data});
            })()
        ''')
        print(f'Write API (no headers): {r}')
        
        # Step 6: Try with X-Headers
        r = await js('''
            (async() => {
                let resp = await fetch('/rapi/m/follow/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-Cid': '71376', 'X-User': '183006'},
                    body: JSON.stringify({
                        models: [
                            {columnName:"dataName", value:229629960, displayValue:"Juan Carlos Martinez Quintero", displayOriginalValue:229629960},
                            {columnName:"contactContent", value:"[邮件] test follow-up 2", displayValue:"", displayOriginalValue:""},
                            {columnName:"bgColor", value:"2B579A", displayValue:"", displayOriginalValue:""},
                            {columnName:"method", dict:true, value:"邮件", displayValue:"", displayOriginalValue:""},
                            {columnName:"planningTime", value:"2026-06-18 22:30:00", displayValue:"", displayOriginalValue:""},
                            {columnName:"feedbackOperator", value:"183006", displayValue:"", displayOriginalValue:""}
                        ]
                    })
                });
                let j = await resp.json();
                return JSON.stringify({status: resp.status, ok: j.success, msg: j.errMsg, data: j.data});
            })()
        ''')
        print(f'Write API (with headers): {r}')

asyncio.run(run())