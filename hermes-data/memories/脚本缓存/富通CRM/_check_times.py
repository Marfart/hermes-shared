import json, asyncio, websockets

async def check():
    ws_url = "ws://127.0.0.1:9226/devtools/page/FB081F841F2DB5392C4322A4D5A4211F"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            resp = json.loads(await ws.recv())
            return resp

        # Check list API for each customer
        for cid, name in [(229629960,"Juan Carlos"),(229679705,"Stephen"),(229629827,"Richard"),(229623037,"Basem"),(229649728,"Alex")]:
            expr = f'''
            (async() => {{
                let r = await fetch('/rapi/d/customers?num=0&paging=true&size=200&searchText={name}', {{
                    headers: {{'Accept':'application/json','X-Cid':'71376','X-User':'183006'}}
                }});
                let j = await r.json();
                let v = j.data?.values;
                if (v && v[0]) {{
                    return JSON.stringify({{
                        lf: v[0].displayLastFollowTime,
                        rf: v[0].recentlyFollowTime
                    }});
                }}
                return 'no match';
            }})()
            '''
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"{name} (CID {cid}): {val}")

asyncio.run(check())