import json, asyncio, websockets

async def main():
    import urllib.request
    pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5).read())
    p = None
    for page in pages:
        if 'cloud.joinf.com/login' in page.get('url',''):
            p = page; break
    if not p: return print("No login page")
    
    async with websockets.connect(p['webSocketDebuggerUrl'], max_size=10*1024*1024) as ws:
        mid = 0
        async def send(m, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": m, "params": params}))
            return json.loads(await ws.recv())
        
        async def js(expr):
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            return r.get("result",{}).get("result",{}).get("value")
        
        # Login + go to customers
        print("Logging in...")
        await send("Page.navigate", {"url": "https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0"})
        await asyncio.sleep(3)
        await js("document.getElementById('loginID').value='bliiot03'")
        await js("document.getElementById('loginPassword').value='Kali1314520!'")
        await js("document.getElementById('loginBtn').click()")
        await asyncio.sleep(4)
        
        url = await js("window.location.href")
        print(f"URL: {url[:80]}")
        
        if 'customer' in url:
            print("✅ On customers page!")
            # Push follow-ups
            records = [
                (229629960, "Juan Carlos Martinez Quintero", "[邮件] 昨天给Juan Carlos发送了跟进邮件，询问新项目需求。"),
                (229679705, "Stephen Hudson / Valve Supplies", "[邮件] 昨天给Stephen Hudson发送了跟进邮件，询问是否有新项目需求。"),
                (229629827, "Richard Twite / Twite Instruments", "[邮件] 昨天给Richard Twite发送了跟进邮件，介绍新产品。"),
                (229623037, "Mr Basem Mohamed Ibrahim", "[邮件] 昨天给Basem发送了跟进邮件，询问新项目需求。"),
                (229649728, "Alex Elliot", "[邮件] 昨天给Alex Elliot发送了跟进邮件，询问新项目合作机会。"),
            ]
            for i, (cid, name, content) in enumerate(records):
                expr = f'''(async()=>{{const r=await fetch('/rapi/m/follow/add',{{method:'POST',headers:{{'Content-Type':'application/json','X-Cid':'71376','X-User':'183006'}},body:JSON.stringify({{models:[{{columnName:"dataName",value:{cid},displayValue:{json.dumps(name)},displayOriginalValue:{cid}}},{{columnName:"contactContent",value:{json.dumps(content)},displayValue:"",displayOriginalValue:""}},{{columnName:"bgColor",value:"2B579A",displayValue:"",displayOriginalValue:""}},{{columnName:"method",dict:true,value:"邮件",displayValue:"",displayOriginalValue:""}},{{columnName:"planningTime",value:"2026-06-18 22:00:00",displayValue:"",displayOriginalValue:""}},{{columnName:"feedbackOperator",value:"183006",displayValue:"",displayOriginalValue:""}}]}})}});const j=await r.json();return JSON.stringify({{ok:j.success,id:j.data?.[0],msg:j.errMsg}})}})()'''
                r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
                val = r.get("result",{}).get("result",{}).get("value","")
                print(f"  [{i+1}/5] {name}: {val}")
            
            # Verify
            print("\n--- Verify ---")
            r = await send("Runtime.evaluate", {"expression": "(async()=>{var r=await fetch('/rapi/d/customers?num=0&paging=true&size=200&searchText=Juan Carlos',{headers:{'Accept':'application/json','X-Cid':'71376','X-User':'183006'}});var j=await r.json();var v=j.data?.values;if(v&&v[0])return JSON.stringify({lf:v[0].displayLastFollowTime,n:v[0].name});return'no'})()", "returnByValue": True, "awaitPromise": True})
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"  Juan Carlos lastFollow: {val}")
        else:
            print("❌ Login failed")

asyncio.run(main())