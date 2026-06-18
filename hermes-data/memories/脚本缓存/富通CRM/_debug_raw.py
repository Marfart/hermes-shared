import json, asyncio, websockets

async def debug():
    ws_url = "ws://127.0.0.1:9226/devtools/page/FB081F841F2DB5392C4322A4D5A4211F"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            resp = json.loads(await ws.recv())
            return resp

        # Get full detail API response  
        expr = '''
        (async() => {
            let r = await fetch('/rapi/d/customers/229629960/1', {
                headers: {'Accept':'application/json','X-Cid':'71376','X-User':'183006'}
            });
            let t = await r.text();
            return t.substring(0, 5000);
        })()
        '''
        r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        text = r.get("result",{}).get("result",{}).get("value","")
        print("RAW response (first 5000 chars):")
        print(text)

asyncio.run(debug())