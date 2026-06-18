import json, asyncio, websockets, urllib.request

async def check():
    pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5).read())
    p = next((pg for pg in pages if 'trade.joinf.com' in pg.get('url','') and 'login' not in pg.get('url','')), pages[0])
    
    async with websockets.connect(p['webSocketDebuggerUrl'], max_size=10*1024*1024) as ws:
        mid=0
        async def s(m,params={}):
            nonlocal mid;mid+=1
            await ws.send(json.dumps({'id':mid,'method':m,'params':params}))
            return json.loads(await ws.recv())
        
        async def j(expr):
            r = await s('Runtime.evaluate',{'expression':expr,'returnByValue':True,'awaitPromise':True})
            return r.get('result',{}).get('result',{}).get('value')
        
        # Check page URL and cookies
        url = await j("window.location.href")
        print(f"URL: {url}")
        
        cookie_str = await j("document.cookie")
        print(f"Cookie (first 200): {(cookie_str or '')[:200]}")
        
        xcid = await j("localStorage.getItem('joinf-compnayId')")
        xuser = await j("localStorage.getItem('joinf-XUser')")
        print(f"X-Cid: {xcid}, X-User: {xuser}")
        
        # Try absolute URL
        r = await j("(async()=>{try{var r=await fetch('https://trade.joinf.com/rapi/m/follow/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({models:[{columnName:'dataName',value:229629960,displayValue:'Test JC',displayOriginalValue:229629960},{columnName:'contactContent',value:'[邮件] test',displayValue:'',displayOriginalValue:''},{columnName:'bgColor',value:'2B579A',displayValue:'',displayOriginalValue:''},{columnName:'method',dict:true,value:'邮件',displayValue:'',displayOriginalValue:''},{columnName:'planningTime',value:'2026-06-18 22:00:00',displayValue:'',displayOriginalValue:''},{columnName:'feedbackOperator',value:'183006',displayValue:'',displayOriginalValue:''}]})});var j=await r.json();return JSON.stringify({status:r.status,ok:j.success,msg:j.errMsg})}catch(e){return JSON.stringify({error:e.message})}})()")
        print(f"Write API: {r}")

asyncio.run(check())