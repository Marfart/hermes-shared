import json, asyncio, websockets, urllib.request

async def verify():
    pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5).read())
    p = next(page for page in pages if 'trade.joinf.com' in page.get('url','') and 'login' not in page.get('url',''))
    
    async with websockets.connect(p['webSocketDebuggerUrl'], max_size=10*1024*1024) as ws:
        mid=0
        async def s(m,params={}):
            nonlocal mid;mid+=1
            await ws.send(json.dumps({'id':mid,'method':m,'params':params}))
            return json.loads(await ws.recv())
        
        async def j(expr):
            r = await s('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True})
            val = r.get('result',{}).get('result',{}).get('value')
            if val is None:
                # Check if there was an exception
                exc = r.get('result',{}).get('exceptionDetails',{})
                if exc:
                    print(f"  JS exception: {exc.get('text','')}")
            return val
        
        # Check list API for each customer
        for search, name in [('Juan Carlos','Juan Carlos'),('Stephen@Home','Stephen'),('richard@twite','Richard'),('basemnani','Basem'),('the-elliots','Alex')]:
            expr = f"(async()=>{{var r=await fetch('/rapi/d/customers?num=0&paging=true&size=200&searchText={search}',{{headers:{{'Accept':'application/json','X-Cid':'71376','X-User':'183006'}}}});var j=await r.json();var v=j.data?.values;if(v&&v[0])return JSON.stringify({{lf:v[0].displayLastFollowTime,n:v[0].name}});return JSON.stringify({{count:j.data?.values?.length||0}});}})()"
            r = await j(expr)
            print(f'{name}: {r}')

asyncio.run(verify())