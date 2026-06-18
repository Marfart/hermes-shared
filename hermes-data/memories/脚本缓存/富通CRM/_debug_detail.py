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
        
        # Navigate to customers page first
        await send("Page.navigate", {"url": "https://trade.joinf.com/tms/customer/customers?tab=0"})
        await asyncio.sleep(4)
        
        # Dump the full detail API response for Juan Carlos
        expr = '''
        (async() => {
            let r = await fetch('/rapi/d/customers/229629960/1', {
                headers: {'Accept':'application/json','X-Cid':'71376','X-User':'183006'}
            });
            let j = await r.json();
            if (j.data) {
                // Print category names
                let cats = j.data.map(c => c.categoryName);
                let colNames = [];
                for (let cat of j.data) {
                    if (cat.columnData) {
                        for (let key of Object.keys(cat.columnData)) {
                            let cd = cat.columnData[key];
                            if (cd && typeof cd === 'object') {
                                colNames.push({cat: cat.categoryName, col: key, val: cd.value, display: cd.displayValue});
                            }
                        }
                    }
                }
                return JSON.stringify({
                    categories: cats,
                    columnInfo: colNames.filter(c => c.col.includes('Follow') || c.col.includes('follow') || c.col.includes('last') || c.col.includes('recently'))
                });
            }
            return JSON.stringify(j).substring(0,1000);
        })()
        '''
        r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
        val = r.get("result",{}).get("result",{}).get("value","")
        print("Detail API response:")
        print(val[:2000])

asyncio.run(debug())