import json, asyncio, websockets

async def push():
    ws_url = "ws://127.0.0.1:9226/devtools/page/FB081F841F2DB5392C4322A4D5A4211F"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            resp = json.loads(await ws.recv())
            return resp
        
        # Navigate to customers page
        await send("Page.navigate", {"url": "https://trade.joinf.com/tms/customer/customers?tab=0"})
        await asyncio.sleep(4)
        
        r = await send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        url = r.get("result",{}).get("result",{}).get("value","")
        print(f"URL: {url[:80]}")
        
        if "login" in url:
            print("Need login")
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginID').value='bliiot03'"})
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginPassword').value='Kali1314520!'"})
            await send("Runtime.evaluate", {"expression": "document.getElementById('loginBtn').click()"})
            await asyncio.sleep(4)
            await send("Page.navigate", {"url": "https://trade.joinf.com/tms/customer/customers?tab=0"})
            await asyncio.sleep(4)
        
        # Minimal payload - exactly what Codex taught
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
                return JSON.stringify({{ok: j.success, data: j.data, msg: j.errMsg}});
            }})()
            '''
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"[{i+1}/5] {name}: {val}")
        
        # Verify
        print("\n--- Verify ---")
        verify_expr = '''
        (async() => {
            let r = await fetch('/rapi/d/customers?num=0&paging=true&size=200&searchText=Juan Carlos', {
                headers: {'Accept':'application/json','X-Cid':'71376','X-User':'183006'}
            });
            let j = await r.json();
            let v = j.data?.values;
            if (v && v[0]) {
                return JSON.stringify({
                    lastFollow: v[0].displayLastFollowTime,
                    activityType: v[0].activityType,
                    displayLastFollowTime: v[0].displayLastFollowTime
                });
            }
            return 'no results';
        })()
        '''
        r = await send("Runtime.evaluate", {"expression": verify_expr, "returnByValue": True, "awaitPromise": True})
        val = r.get("result",{}).get("result",{}).get("value","")
        print(f"Juan Carlos verification: {val}")

asyncio.run(push())