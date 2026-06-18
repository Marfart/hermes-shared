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
            return r.get('result',{}).get('result',{}).get('value')
        
        for cid, name in [(229629960,'Juan Carlos'),(229679705,'Stephen'),(229629827,'Richard'),(229623037,'Basem'),(229649728,'Alex')]:
            r = await j(f"(async()=>{{var r=await fetch('/rapi/d/customers/"+str(cid)+"/1',{{headers:{{'Accept':'application/json','X-Cid':'71376','X-User':'183006'}}}});var j=await r.json();var info=j.data?.find(c=>c.categoryName==='主要信息');if(info&&info.columnData)return JSON.stringify({{lf:info.columnData.displayLastFollowTime?.value,rf:info.columnData.recentlyFollowTime?.value}});return'no'}})()")
            print(f'{name}: {r}')

asyncio.run(verify())