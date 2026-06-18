import json, asyncio, websockets

async def push():
    # Get the correct page ID dynamically
    import urllib.request
    resp = urllib.request.urlopen("http://127.0.0.1:9226/json", timeout=5)
    pages = json.loads(resp.read())
    
    # Find the first CRM page that is logged in (not login page)
    ws_url = None
    for p in pages:
        u = p.get('url', '')
        if 'trade.joinf.com' in u and 'login' not in u.lower():
            ws_url = p['webSocketDebuggerUrl']
            print(f"Found logged-in page: {p['id'][:20]} | {u[:80]}")
            break
    
    if not ws_url:
        # Find any page and login from there
        for p in pages:
            if 'cloud.joinf.com/login' in p.get('url',''):
                ws_url = p['webSocketDebuggerUrl']
                print(f"Using login page: {p['id'][:20]}")
                break
    
    if not ws_url:
        print("No pages found!")
        return
    
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            resp = json.loads(await ws.recv())
            return resp
        
        # Check current URL
        r = await send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        url = r.get("result",{}).get("result",{}).get("value","")
        print(f"Current URL: {url[:100]}")
        
        if "login" in url:
            print("Logging in...")
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginID').value='bliiot03'"})
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginPassword').value='Kali1314520!'"})
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginBtn').click()"})
            await asyncio.sleep(5)
            
            r = await send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
            url = r.get("result",{}).get("result",{}).get("value","")
            print(f"After login: {url[:100]}")
        
        # Now navigate to customers page
        await send("Page.navigate", {"url": "https://trade.joinf.com/tms/customer/customers?tab=0"})
        await asyncio.sleep(4)
        
        r = await send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        url = r.get("result",{}).get("result",{}).get("value","")
        print(f"After navigate: {url[:100]}")
        
        if "login" in url:
            print("Redirected again, logging in from customers URL...")
            # Navigate with service redirect
            await send("Page.navigate", {"url": "https://cloud.joinf.com/login?service=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftab%3D0"})
            await asyncio.sleep(3)
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginID').value='bliiot03'"})
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginPassword').value='Kali1314520!'"})
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginBtn').click()"})
            await asyncio.sleep(5)
            
            r = await send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
            url = r.get("result",{}).get("result",{}).get("value","")
            print(f"Final URL: {url[:100]}")
        
        # Check if we're on CRM page
        if "customers" in url:
            print("✅ On customers page! Pushing follow-ups...")
            
            records = [
                (229629960, "Juan Carlos Martinez Quintero", "[邮件] 昨天给Juan Carlos发送了跟进邮件，询问新项目需求。"),
                (229679705, "Stephen Hudson / Valve Supplies (NZ) Ltd", "[邮件] 昨天给Stephen Hudson发送了跟进邮件，询问是否有新项目需求。"),
                (229629827, "Richard Twite / Twite Instruments", "[邮件] 昨天给Richard Twite发送了跟进邮件，介绍新产品。"),
                (229623037, "Mr Basem Mohamed Ibrahim Elsayed Elmanzalawi.", "[邮件] 昨天给Basem发送了跟进邮件，询问新项目需求。"),
                (229649728, "Alex Elliot", "[邮件] 昨天给Alex Elliot发送了跟进邮件，询问新项目合作机会。"),
            ]
            
            for i, (cid, name, content) in enumerate(records):
                expr = f'''
                (async() => {{
                    const r = await fetch('/rapi/m/follow/add', {{
                        method: 'POST',
                        headers: {{'Content-Type':'application/json','X-Cid':'71376','X-User':'183006'}},
                        body: JSON.stringify({{
                            models: [
                                {{columnName:"dataName", value:{cid}, displayValue:{json.dumps(name)}, displayOriginalValue:{cid}}},
                                {{columnName:"contactContent", value:{json.dumps(content)}, displayValue:"", displayOriginalValue:""}},
                                {{columnName:"bgColor", value:"2B579A", displayValue:"", displayOriginalValue:""}},
                                {{columnName:"method", dict:true, value:"邮件", displayValue:"", displayOriginalValue:""}},
                                {{columnName:"planningTime", value:"2026-06-18 22:00:00", displayValue:"", displayOriginalValue:""}},
                                {{columnName:"feedbackOperator", value:"183006", displayValue:"", displayOriginalValue:""}}
                            ]
                        }})
                    }});
                    const j = await r.json();
                    return JSON.stringify({{ok: j.success, msg: j.errMsg || 'OK', id: j.data?.[0]}});
                }})()
                '''
                r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
                val = r.get("result",{}).get("result",{}).get("value","")
                print(f"  [{i+1}/5] {name}: {val}")
            
            # VERIFY
            print("\n--- Verification ---")
            r = await send("Runtime.evaluate", {"expression": '''
                (async() => {
                    let r = await fetch('/rapi/d/customers?num=0&paging=true&size=200&searchText=Juan Carlos', {
                        headers: {'Accept':'application/json','X-Cid':'71376','X-User':'183006'}
                    });
                    let j = await r.json();
                    let v = j.data?.values;
                    if (v && v[0]) {
                        return JSON.stringify({
                            lastFollow: v[0].displayLastFollowTime,
                            name: v[0].name
                        });
                    }
                    return 'no results';
                })()
            ''', "returnByValue": True, "awaitPromise": True})
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"  Juan Carlos lastFollow: {val}")
            
            # Check if it changed (old = 1773365475000 = March)
            last = json.loads(val) if val[0]=='{' else {}
            if last.get('lastFollow') and last['lastFollow'] != 1773365475000:
                print("✅ FOLLOW-UP WRITTEN SUCCESSFULLY!")
            else:
                print("❌ lastFollow unchanged - still not written")
        else:
            print(f"❌ Not on customers page: {url[:80]}")

asyncio.run(push())