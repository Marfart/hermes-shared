"""
富通公海客户全量爬取 v4
通过Vue组件翻页 + 读取tableData
优化：每页读取后立即翻页，最小化等待时间
"""
import json, socket, base64, struct, time, os, sys

CDP_WS = "ws://127.0.0.1:9226/devtools/page/09B7ECBE4020E3E37AA5C19C37CB1DDB"
OUTPUT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Working', '富通CRM_公海客户_全量.json')
TOTAL_PAGES = 3312
TOTAL_RECORDS = 66224

def ws_connect(url):
    url = url.replace('ws://', '')
    host_port, path = url.split('/', 1)
    host, port = host_port.split(':')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(300)
    sock.connect((host, int(port)))
    key = base64.b64encode(os.urandom(16)).decode()
    req = f"GET /{path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    sock.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += sock.recv(4096)
    return sock

def ws_send(sock, data):
    payload = data.encode('utf-8')
    frame = bytearray([0x81])
    length = len(payload)
    mask_key = os.urandom(4)
    if length < 126: frame.append(0x80 | length)
    elif length < 65536: frame.append(0x80 | 126); frame.extend(struct.pack('>H', length))
    else: frame.append(0x80 | 127); frame.extend(struct.pack('>Q', length))
    frame.extend(mask_key)
    frame.extend(b ^ mask_key[i % 4] for i, b in enumerate(payload))
    sock.sendall(frame)

def ws_recv(sock, timeout=30):
    sock.settimeout(timeout)
    data = b""
    try:
        while True:
            chunk = sock.recv(65536)
            if not chunk: break
            data += chunk
            for marker in [b'{"id":', b'{"method":']:
                idx = data.find(marker)
                if idx >= 0:
                    try: return json.loads(data[idx:])
                    except: continue
    except socket.timeout: pass
    return None

def read_page_data(sock, page_num):
    """读取指定页的数据"""
    # 先翻页
    cmd = {
        "id": page_num * 10 + 1,
        "method": "Runtime.evaluate",
        "params": {
            "expression": f"""
                (function() {{
                    let all = document.querySelectorAll('*');
                    for (let el of all) {{
                        if (el.__vue__) {{
                            let d = el.__vue__.$data;
                            if (d && d.tableDataTotal > 1000) {{
                                el.__vue__.handleCurrentChange({page_num});
                                return 'ok';
                            }}
                        }}
                    }}
                    return 'nf';
                }})()
            """,
            "returnByValue": True,
            "timeout": 5000
        }
    }
    ws_send(sock, json.dumps(cmd))
    ws_recv(sock, timeout=5)
    
    # 等数据加载
    time.sleep(0.8)
    
    # 读取数据
    cmd = {
        "id": page_num * 10 + 2,
        "method": "Runtime.evaluate",
        "params": {
            "expression": """
                (function() {
                    let all = document.querySelectorAll('*');
                    for (let el of all) {
                        if (el.__vue__) {
                            let d = el.__vue__.$data;
                            if (d && d.tableDataTotal > 1000 && d.tableData) {
                                return JSON.stringify({
                                    items: d.tableData,
                                    currentPage: d.currentPage,
                                    total: d.tableDataTotal
                                });
                            }
                        }
                    }
                    return null;
                })()
            """,
            "returnByValue": True,
            "timeout": 5000
        }
    }
    ws_send(sock, json.dumps(cmd))
    result = ws_recv(sock, timeout=10)
    if result and result.get('result', {}).get('result', {}).get('value'):
        return json.loads(result['result']['result']['value'])
    return None

def main():
    print("=" * 60)
    print("富通公海客户全量爬取 v4")
    print(f"目标: {TOTAL_RECORDS} 条 / {TOTAL_PAGES} 页")
    print("=" * 60)
    
    sock = ws_connect(CDP_WS)
    print("✅ 已连接")
    
    # 先回到第1页
    print("\n回到第1页...")
    read_page_data(sock, 1)
    time.sleep(1)
    
    # 读取第1页数据
    data = read_page_data(sock, 1)
    if not data:
        print("❌ 读取失败")
        return
    
    all_customers = list(data['items'])
    print(f"第1页: {len(all_customers)} 条 | 总计: {data['total']}")
    
    start_time = time.time()
    
    # 逐页读取
    for page in range(2, TOTAL_PAGES + 1):
        data = read_page_data(sock, page)
        
        if data and data.get('items'):
            all_customers.extend(data['items'])
            count = len(all_customers)
            
            if page % 50 == 0 or page == TOTAL_PAGES:
                elapsed = time.time() - start_time
                speed = page / elapsed if elapsed > 0 else 0
                eta = (TOTAL_PAGES - page) / speed if speed > 0 else 0
                pct = count / TOTAL_RECORDS * 100
                print(f"第{page}/{TOTAL_PAGES}页 | {count}/{TOTAL_RECORDS} ({pct:.1f}%) | {speed:.1f}页/秒 | ETA:{eta/60:.0f}分")
        else:
            if page % 100 == 0:
                print(f"⚠️ 第{page}页失败")
        
        # 每100页保存
        if page % 100 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_customers, f, ensure_ascii=False)
            print(f"  💾 已保存 {len(all_customers)} 条")
    
    sock.close()
    
    # 最终保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_customers, f, ensure_ascii=False)
    
    elapsed = time.time() - start_time
    print(f"\n✅ 完成！{len(all_customers)} 条 / {elapsed/60:.1f} 分钟")
    print(f"保存: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
