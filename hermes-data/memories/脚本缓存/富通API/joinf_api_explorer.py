#!/usr/bin/env python3
"""
富通CRM API探索脚本 - 阶段1: Network监听 + 添加备注测试
目标: 用CDP Network域监听XHR请求，捕获添加备注时的真实API调用
"""
import json, websocket, time, subprocess, os, sys
from datetime import datetime

LOG_FILE = r"C:\Users\Admin\Desktop\hermes_crm_api_exploration_log.md"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"### [{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def get_ws_url():
    result = subprocess.run(['curl', '-s', 'http://127.0.0.1:9223/json'], 
                          capture_output=True, text=True, timeout=5)
    pages = json.loads(result.stdout)
    # 找富通页面
    joinf = [p for p in pages if 'trade.joinf' in p.get('url','') and p.get('type')=='page']
    if not joinf:
        # 找任意页面
        joinf = [p for p in pages if p.get('type')=='page']
    if not joinf:
        raise Exception("No page found!")
    return f"ws://127.0.0.1:9223/devtools/page/{joinf[0]['id']}"

def recv_with_timeout(ws, timeout=5, msg_id=None):
    """接收响应，可选等待特定id"""
    end = time.time() + timeout
    while time.time() < end:
        ws.settimeout(min(2, end - time.time()))
        try:
            data = json.loads(ws.recv())
            if msg_id is None or data.get('id') == msg_id:
                return data
        except:
            pass
    return None

log("=" * 60)
log("阶段1开始: Network监听 + 添加备注测试")
log("=" * 60)

ws_url = get_ws_url()
log(f"连接: {ws_url}")

ws = websocket.create_connection(ws_url, timeout=30)
log("WebSocket连接成功 ✓")

# ===== Step 1: 启用 Network 域 =====
ws.send(json.dumps({"id": 10, "method": "Network.enable", "params": {}}))
time.sleep(1)
ws.settimeout(3)
try:
    r = json.loads(ws.recv())
    log(f"Network.enable: OK")
except:
    log("Network.enable: 无响应(可能已启用)")

# ===== Step 2: 导航到客户详情页 =====
log("导航到测试客户详情页 (id=238855365)...")
ws.send(json.dumps({
    "id": 20,
    "method": "Page.navigate",
    "params": {"url": "https://trade.joinf.com/tms/customer/customers?type=edit&id=238855365&tab=0"}
}))

time.sleep(8)

# 清空可能积压的消息
ws.settimeout(1)
try:
    while True:
        ws.recv()
except:
    pass

# 确认页面加载
ws.send(json.dumps({
    "id": 21,
    "method": "Runtime.evaluate",
    "params": {"expression": "document.readyState + ' | ' + window.location.href.substring(0,100)", "returnByValue": True}
}))
time.sleep(2)
ws.settimeout(5)
try:
    resp = recv_with_timeout(ws, 5, 21)
    if resp:
        val = resp.get('result',{}).get('result',{}).get('value','')
        log(f"页面状态: {val}")
except Exception as e:
    log(f"状态检查错误: {e}")

# ===== Step 3: 记录原始备注值 =====
ws.send(json.dumps({
    "id": 30,
    "method": "Runtime.evaluate",
    "params": {
        "expression": """
        (function() {
            var intro = document.getElementById('introduce');
            var textarea = document.querySelector('textarea[name="introduce"]');
            var el = intro || textarea;
            if (!el) {
                // 找所有textarea
                var all = document.querySelectorAll('textarea');
                var info = 'No introduce found. Textareas: ' + all.length;
                all.forEach(function(t,i) { info += '\\n  ' + i + ': id=' + t.id + ' name=' + t.name; });
                return info;
            }
            return 'Original value: ' + el.value.substring(0, 100);
        })()
        """,
        "returnByValue": True
    }
}))
time.sleep(1)
ws.settimeout(5)
try:
    resp = recv_with_timeout(ws, 5, 30)
    if resp:
        val = resp.get('result',{}).get('result',{}).get('value','')
        log(f"原始备注: {val[:200]}")
        original_value = val
except Exception as e:
    log(f"获取备注错误: {e}")
    original_value = ""

# ===== Step 4: 输入测试备注 =====
TEST_STRING = f"HERMES_API_TEST_{datetime.now().strftime('%H%M%S')}"
log(f"测试字符串: {TEST_STRING}")

ws.send(json.dumps({
    "id": 40,
    "method": "Runtime.evaluate",
    "params": {
        "expression": f"""
        (function() {{
            var intro = document.getElementById('introduce');
            var textarea = document.querySelector('textarea[name="introduce"]');
            var el = intro || textarea;
            if (!el) return 'NO_ELEMENT';
            
            // 设置值并触发事件
            el.value = '{TEST_STRING}';
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            
            // 如果是Vue组件，尝试触发Vue响应
            if (el.__vue__) {{
                el.__vue__.$emit('input', '{TEST_STRING}');
            }}
            
            return 'SET:' + el.value.substring(0,50);
        }})()
        """,
        "returnByValue": True
    }
}))
time.sleep(1)
ws.settimeout(5)
try:
    resp = recv_with_timeout(ws, 5, 40)
    if resp:
        val = resp.get('result',{}).get('result',{}).get('value','')
        log(f"设置备注: {val}")
except Exception as e:
    log(f"设置备注错误: {e}")

# ===== Step 5: 点击保存按钮 =====
log("查找并点击保存按钮...")

ws.send(json.dumps({
    "id": 50,
    "method": "Runtime.evaluate",
    "params": {
        "expression": """
        (function() {
            // 找保存按钮 - 多种选择器
            var selectors = [
                'button[type="submit"]',
                '.save-btn', '.btn-save', 
                'button:contains("保存")',
                '.el-button--primary',
                'button.submit'
            ];
            
            var found = [];
            // 遍历所有按钮
            var btns = document.querySelectorAll('button, input[type="submit"]');
            btns.forEach(function(b) {
                var text = b.textContent.trim();
                var cls = b.className;
                found.push({text: text.substring(0,30), class: cls.substring(0,50), id: b.id});
            });
            
            // 找包含"保存"文字的按钮
            var saveBtn = null;
            btns.forEach(function(b) {
                if (b.textContent.indexOf('保存') >= 0 || b.textContent.indexOf('Save') >= 0) {
                    saveBtn = b;
                }
            });
            
            if (saveBtn) {
                saveBtn.click();
                return 'CLICKED: ' + saveBtn.textContent.trim().substring(0,30);
            }
            
            return 'NO_SAVE_BTN. Found: ' + JSON.stringify(found.slice(0,10));
        })()
        """,
        "returnByValue": True
    }
}))
time.sleep(2)
ws.settimeout(5)
try:
    resp = recv_with_timeout(ws, 5, 50)
    if resp:
        val = resp.get('result',{}).get('result',{}).get('value','')
        log(f"保存按钮: {val[:300]}")
except Exception as e:
    log(f"保存按钮错误: {e}")

# ===== Step 6: 监听 10 秒内的 Network 请求 =====
log("监听 Network 请求 (10秒)...")

collected_requests = []
collected_responses = {}  # requestId -> response body
pending_requests = {}  # requestId -> request info

end_time = time.time() + 10
ws.settimeout(1)

while time.time() < end_time:
    try:
        data = json.loads(ws.recv())
        method = data.get('method', '')
        
        if method == 'Network.requestWillBeSent':
            req = data.get('params', {})
            rid = req.get('requestId')
            url = req.get('request', {}).get('url', '')
            req_method = req.get('request', {}).get('method', '')
            post_data = req.get('request', {}).get('postData', '')
            
            # 只关注 POST/PUT/PATCH
            if req_method in ('POST', 'PUT', 'PATCH'):
                pending_requests[rid] = {
                    'url': url,
                    'method': req_method,
                    'postData': post_data[:500] if post_data else '',
                    'time': time.time()
                }
                
        elif method == 'Network.responseReceived':
            resp = data.get('params', {})
            rid = resp.get('requestId')
            if rid in pending_requests:
                pending_requests[rid]['status'] = resp.get('response', {}).get('status')
                
        elif method == 'Network.loadingFinished':
            rid = data.get('params', {}).get('requestId')
            if rid in pending_requests:
                # 尝试获取response body
                ws.send(json.dumps({
                    "id": 9000 + len(collected_responses),
                    "method": "Network.getResponseBody",
                    "params": {"requestId": rid}
                }))
                
        elif data.get('id', 0) >= 9000:
            # 这是 getResponseBody 的响应
            body = data.get('result', {}).get('body', '')
            # 找到对应的request
            for rid, req_info in pending_requests.items():
                if rid not in collected_responses:
                    collected_responses[rid] = body[:1000]
                    break
                    
    except websocket.WebSocketTimeoutException:
        continue
    except Exception as e:
        pass

log(f"收集到 {len(pending_requests)} 个 POST/PUT/PATCH 请求")

# ===== Step 7: 分析请求 =====
log("分析请求...")

target_requests = []
for rid, req in pending_requests.items():
    url = req['url']
    post = req.get('postData', '')
    resp = collected_responses.get(rid, '')
    
    # 筛选包含测试字符串的请求
    has_test = (TEST_STRING in url or TEST_STRING in post or TEST_STRING in resp)
    
    # 筛选 URL 关键词
    url_lower = url.lower()
    is_api = any(kw in url_lower for kw in ['/api/', '/rapi/', '/service', 'save', 'update', 'add', 'create', 'customer', 'contact', 'remark', 'follow', 'record', 'mail', 'draft'])
    
    if has_test or is_api:
        target_requests.append({
            'url': url,
            'method': req['method'],
            'postData': post[:300],
            'response': resp[:300],
            'status': req.get('status', '?'),
            'hasTestString': has_test
        })

log(f"目标请求: {len(target_requests)} 个")

for i, req in enumerate(target_requests):
    log(f"\n--- 请求 {i+1} {'★TEST_STRING★' if req['hasTestString'] else ''} ---")
    log(f"  URL: {req['url'][:150]}")
    log(f"  Method: {req['method']}")
    log(f"  Status: {req['status']}")
    log(f"  Payload: {req['postData'][:200]}")
    log(f"  Response: {req['response'][:200]}")

# ===== Step 8: 获取 Cookies =====
ws.send(json.dumps({
    "id": 100,
    "method": "Network.getCookies",
    "params": {"urls": ["https://trade.joinf.com"]}
}))
time.sleep(2)
ws.settimeout(5)
try:
    resp = recv_with_timeout(ws, 5, 100)
    if resp:
        cookies = resp.get('result', {}).get('cookies', [])
        cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies])
        log(f"\nCookies ({len(cookies)}):")
        for c in cookies:
            log(f"  {c['name']}={c['value'][:30]}")
        
        # 保存到文件供后续使用
        with open(r"C:\Users\Admin\Desktop\joinf_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        log("Cookies已保存到 joinf_cookies.json")
except Exception as e:
    log(f"获取Cookies错误: {e}")

ws.close()

# ===== Step 9: 获取页面当前备注值验证 =====
log("\n验证备注是否保存...")

ws2 = websocket.create_connection(ws_url, timeout=20)
ws2.send(json.dumps({
    "id": 200,
    "method": "Runtime.evaluate",
    "params": {
        "expression": f"""
        (function() {{
            var intro = document.getElementById('introduce');
            var textarea = document.querySelector('textarea[name="introduce"]');
            var el = intro || textarea;
            if (!el) return 'NO_ELEMENT';
            return el.value.substring(0, 100);
        }})()
        """,
        "returnByValue": True
    }
}))
time.sleep(1)
ws2.settimeout(5)
try:
    resp = json.loads(ws2.recv())
    val = resp.get('result',{}).get('result',{}).get('value','')
    log(f"当前备注值: {val}")
    if TEST_STRING in val:
        log("✓ 测试字符串在页面中!")
except Exception as e:
    log(f"验证错误: {e}")

ws2.close()

# ===== 输出结果 =====
log("\n" + "=" * 60)
log("阶段1完成")
log(f"测试字符串: {TEST_STRING}")
log(f"目标请求数: {len(target_requests)}")
log("=" * 60)

# 保存结果
result = {
    'test_string': TEST_STRING,
    'timestamp': datetime.now().isoformat(),
    'requests_found': len(target_requests),
    'requests': target_requests
}
with open(r"C:\Users\Admin\Desktop\joinf_api_test_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
log("结果已保存到 joinf_api_test_result.json")

print(f"\n=== 完成 ===")
print(f"测试字符串: {TEST_STRING}")
print(f"找到 {len(target_requests)} 个目标请求")
