import sqlite3, json, time, asyncio, websocket
from datetime import datetime, timezone, timedelta

DB_PATH = r'C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\富通CRM\crm_followups.db'

async def main():
    # Connect to CDP
    ws = websocket.WebSocket()
    ws.connect('ws://127.0.0.1:9226/devtools/page/7829F8F43F458721D9637BA8A9CBE8C8')
    
    msg_id = 0
    pending = {}
    
    def send(method, params=None):
        nonlocal msg_id
        msg_id += 1
        msg = {'id': msg_id, 'method': method}
        if params: msg['params'] = params
        ws.send(json.dumps(msg))
        # Wait for response with matching id
        while True:
            raw = ws.recv()
            resp = json.loads(raw)
            if resp.get('id') == msg_id:
                return resp
    
    # Navigate to establish session
    print('📡 连接CDP浏览器...')
    send('Page.navigate', {'url': 'https://trade.joinf.com/tms/customer/customers?type=search&tab=0'})
    time.sleep(4)
    
    db = sqlite3.connect(DB_PATH)
    records = db.execute('SELECT * FROM followups WHERE synced=0 ORDER BY id').fetchall()
    col_names = [d[0] for d in db.execute('PRAGMA table_info(followups)').fetchall()]
    
    success = 0
    fail = 0
    
    for rec in records:
        r = dict(zip(col_names, rec))
        cid, content, typ, created = r['customer_id'], r['content'], r['type'], r['created_at']
        full_content = f'[{typ}] {content}' if typ else content
        
        # Color mapping
        color_map = {'邮件': '"2B579A"', '报价': '"E67E22"', 'WhatsApp': '"27AE60"', '电话': '"E74C3C"'}
        method_map = {'邮件': '"邮件"', 'WhatsApp': '"WhatsApp"', '电话': '"电话"', '报价': '"跟进"'}
        color = color_map.get(typ, '"fe4145"')
        method = method_map.get(typ, '""')
        
        print(f'  📝 #{r["id"]} [{typ}] {content[:40]}... ', end='')
        
        expr = f'''
            (async () => {{
                try {{
                    const resp = await fetch('/rapi/m/follow/add', {{
                        method: 'POST',
                        headers: {{ 'X-Cid': '71376', 'X-User': '183006', 'Content-Type': 'application/json', 'Accept': 'application/json' }},
                        body: JSON.stringify({{
                            id: "", attachmentList: [], businessStep: 0, customerStep: 0,
                            completeNoRemind: 0, cycleEndDay: "", cycleStartDay: "", cycleId: "",
                            dataType: 0, currentDoneFlag: 0,
                            models: [
                                {{ columnDisplayName: "Customer Name", columnName: "dataName", dict: false, displayOriginalValue: {cid}, displayValue: {json.dumps(r.get('customer_name', '') or '')}, originalValue: "", value: {cid} }},
                                {{ columnDisplayName: "Contact Name", columnName: "dataContactName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Content", columnName: "contactContent", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: {json.dumps(full_content)} }},
                                {{ columnDisplayName: "Attachment", columnName: "annex", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Color", columnName: "bgColor", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: {color} }},
                                {{ columnDisplayName: "Follow Method", columnName: "method", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: {method} }},
                                {{ columnDisplayName: "Planning Time", columnName: "planningTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: {json.dumps(created)} }},
                                {{ columnDisplayName: "Step", columnName: "step", dict: true, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Next Remind Time", columnName: "nextRemindTime", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Repeat Cycle", columnName: "repeatCycle", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Relevant", columnName: "relevant", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Operator", columnName: "operatorName", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: null }},
                                {{ columnDisplayName: "Feedback Operator", columnName: "feedbackOperator", dict: false, displayOriginalValue: "", displayValue: "", originalValue: "", value: "183006" }}
                            ],
                            relevantList: [{{ relevantId: "", relevant: "" }}],
                            flowStep: "", forceRefresh: true, followType: "", followObject: ""
                        }})
                    }});
                    const json = await resp.json();
                    return JSON.stringify({{ ok: json.success, data: json.data, msg: json.errMsg }});
                }} catch(e) {{ return JSON.stringify({{ ok: false, error: e.message }}); }}
            }})()
        '''
        
        try:
            result = send('Runtime.evaluate', {'expression': expr, 'returnByValue': True, 'awaitPromise': True})
            res = json.loads(result['result']['result']['value'])
            
            if res.get('ok'):
                db.execute('UPDATE followups SET synced=1, joinf_follow_id=? WHERE id=?', (str(res.get('data','')), r['id']))
                db.execute("INSERT INTO sync_log (followup_id, customer_id, action, status, message) VALUES (?, ?, 'synced', 'success', ?)",
                          (r['id'], r['customer_id'], json.dumps(res)))
                print('✅')
                success += 1
            else:
                db.execute("INSERT INTO sync_log (followup_id, customer_id, action, status, message) VALUES (?, ?, 'sync_failed', 'failed', ?)",
                          (r['id'], r['customer_id'], res.get('msg') or res.get('error') or 'unknown'))
                print(f'❌ {res.get("msg") or res.get("error")}')
                fail += 1
        except Exception as e:
            print(f'❌ {e}')
            fail += 1
        
        time.sleep(0.5)
    
    db.commit()
    db.close()
    ws.close()
    
    print(f'\n📊 同步完成: {success} ✅ 成功, {fail} ❌ 失败')

asyncio.run(main())