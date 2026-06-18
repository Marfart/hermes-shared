import json, asyncio, websockets

async def sync_direct():
    ws_url = "ws://127.0.0.1:9226/devtools/page/FB081F841F2DB5392C4322A4D5A4211F"
    async with websockets.connect(ws_url, max_size=10*1024*1024) as ws:
        mid = 0
        async def send(method, params={}):
            nonlocal mid; mid += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            resp = json.loads(await ws.recv())
            return resp
        
        # DON'T navigate - use current page. Just verify we're on the right page
        r = await send("Runtime.evaluate", {"expression": "window.location.href", "returnByValue": True})
        url = r.get("result",{}).get("result",{}).get("value","")
        print(f"Current URL: {url[:80]}")
        
        if "login" in url:
            print("!!! On login page, need to re-auth")
            return
        
        # Push 5 follow-ups
        records = [
            (229629960, "Juan Carlos Martinez Quintero", "[邮件] 昨天（2026-06-18）给Juan Carlos（juancarlosmartinezq@hotmail.com）发送了一封跟进邮件，询问是否有新项目需求，并介绍了BLIIOT最新产品线。"),
            (229679705, "Stephen Hudson / Valve Supplies (NZ) Ltd", "[邮件] 昨天（2026-06-18）给Stephen Hudson（Stephen@Home.co.nz）发送了一封跟进邮件，询问是否还记得BLIIOT及是否有新项目需求。"),
            (229629827, "Richard Twite / Twite Instruments", "[邮件] 昨天（2026-06-18）给Richard Twite（richard@twite.com.au）发送了一封跟进邮件，介绍BLIIOT新工业IoT产品方案。"),
            (229623037, "Mr Basem Mohamed Ibrahim Elsayed Elmanzalawi.", "[邮件] 昨天（2026-06-18）给Basem（basemnani71077@gmail.com）发送了一封跟进邮件，询问是否有新项目需求。"),
            (229649728, "Alex Elliot", "[邮件] 昨天（2026-06-18）给Alex Elliot（alex@the-elliots.us）发送了一封跟进邮件，询问是否有新项目合作机会。"),
        ]
        
        for i, (cid, name, content) in enumerate(records):
            expr = f'''
            (async () => {{
                try {{
                    const resp = await fetch('/rapi/m/follow/add', {{
                        method: 'POST',
                        headers: {{'X-Cid':'71376','X-User':'183006','Content-Type':'application/json','Accept':'application/json'}},
                        body: JSON.stringify({{
                            id:"",attachmentList:[],businessStep:0,customerStep:0,completeNoRemind:0,
                            cycleEndDay:"",cycleStartDay:"",cycleId:"",dataType:0,currentDoneFlag:0,
                            models:[
                                {{columnDisplayName:"Customer Name",columnName:"dataName",dict:false,
                                 displayOriginalValue:{cid},displayValue:{json.dumps(name)},originalValue:"",value:{cid}}},
                                {{columnDisplayName:"Contact Name",columnName:"dataContactName",dict:false,
                                 displayOriginalValue:"",displayValue:"",originalValue:"",value:null}},
                                {{columnDisplayName:"Content",columnName:"contactContent",dict:false,
                                 displayOriginalValue:"",displayValue:"",originalValue:"",value:{json.dumps(content)}}},
                                {{columnDisplayName:"Color",columnName:"bgColor",dict:false,
                                 displayOriginalValue:"",displayValue:"",originalValue:"",value:"2B579A"}},
                                {{columnDisplayName:"Follow Method",columnName:"method",dict:true,
                                 displayOriginalValue:"",displayValue:"",originalValue:"",value:"邮件"}},
                                {{columnDisplayName:"Planning Time",columnName:"planningTime",dict:false,
                                 displayOriginalValue:"",displayValue:"",originalValue:"",value:"2026-06-18 22:00:00"}},
                                {{columnDisplayName:"Feedback Operator",columnName:"feedbackOperator",dict:false,
                                 displayOriginalValue:"",displayValue:"",originalValue:"",value:"183006"}}
                            ],
                            relevantList:[{{relevantId:"",relevant:""}}],
                            flowStep:"",forceRefresh:true,followType:"",followObject:""
                        }})
                    }});
                    const json = await resp.json();
                    return JSON.stringify({{ok: json.success || json.code === 0, data: json.data, msg: json.errMsg}});
                }} catch(e) {{ return JSON.stringify({{ok:false, error: e.message}}); }}
            }})()
            '''
            
            r = await send("Runtime.evaluate", {"expression": expr, "returnByValue": True, "awaitPromise": True})
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"[{i+1}/5] {name}: {val}")
        
        # Verify: check displayLastFollowTime
        print("\n--- Verification ---")
        for cid, name, _ in records:
            verify_expr = f'''
            (async() => {{
                let r = await fetch('/rapi/d/customers/{cid}/1', {{
                    headers: {{'Accept':'application/json','X-Cid':'71376','X-User':'183006'}}
                }});
                let j = await r.json();
                let cats = j.data?.map(c => c.categoryName) || [];
                let info = j.data?.find(c => c.categoryName === '主要信息');
                if (info && info.columnData) {{
                    let lf = info.columnData.displayLastFollowTime;
                    let rf = info.columnData.recentlyFollowTime;
                    return JSON.stringify({{
                        lastFollow: lf?.value + ' (' + (lf?.displayValue || '') + ')',
                        recentlyFollow: rf?.value + ' (' + (rf?.displayValue || '') + ')'
                    }});
                }}
                return 'cats=' + JSON.stringify(cats);
            }})()
            '''
            r = await send("Runtime.evaluate", {"expression": verify_expr, "returnByValue": True, "awaitPromise": True})
            val = r.get("result",{}).get("result",{}).get("value","")
            print(f"  {name}: {val}")

asyncio.run(sync_direct())