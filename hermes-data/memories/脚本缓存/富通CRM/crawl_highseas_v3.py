"""
富通公海客户全量爬取 v3 - 使用 /rapi/d/customers/public API
每页500条，共133页，总计66224条
"""
import json, socket, base64, struct, time, os, sys

CDP_WS = "ws://127.0.0.1:9226/devtools/page/09B7ECBE4020E3E37AA5C19C37CB1DDB"
OUTPUT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Working', '富通CRM_公海客户_全量.json')
PROGRESS_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Working', 'crawl_progress.json')
PAGE_SIZE = 500
TOTAL_PAGES = 133  # 66224 / 500 = 133

def ws_connect(url):
    url = url.replace('ws://', '')
    host_port, path = url.split('/', 1)
    host, port = host_port.split(':')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(120)
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

def fetch_page(sock, page_num, max_retries=3):
    for attempt in range(max_retries):
        cmd = {
            "id": page_num + 1000,
            "method": "Runtime.evaluate",
            "params": {
                "expression": f"""
                    (async () => {{
                        let r = await fetch('/rapi/d/customers/public?num={page_num}&paging=true&size={PAGE_SIZE}&sortColumn=lastTransferTime&sortType=desc');
                        let j = await r.json();
                        return JSON.stringify({{totalRecords: j.totalRecords, values: j.data?.values || []}});
                    }})()
                """,
                "awaitPromise": True,
                "returnByValue": True
            }
        }
        ws_send(sock, json.dumps(cmd))
        result = ws_recv(sock, timeout=30)
        if result and result.get('result', {}).get('result', {}).get('value'):
            val = json.loads(result['result']['result']['value'])
            if val.get('values'):
                return val
        print(f"  第{page_num}页重试 {attempt+1}/{max_retries}...")
        time.sleep(2)
    return None

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'last_page': 0, 'total_records': 0}

def save_progress(page, total):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({'last_page': page, 'total_records': total}, f)

def main():
    print("=" * 60)
    print("富通公海客户全量爬取 v3")
    print(f"API: /rapi/d/customers/public")
    print(f"总记录: 66224, 每页: {PAGE_SIZE}, 总页数: {TOTAL_PAGES}")
    print("=" * 60)
    
    # 加载进度
    progress = load_progress()
    start_page = progress['last_page'] + 1
    all_customers = []
    
    if start_page > 1:
        print(f"从第{start_page}页继续（断点续爬）")
        # 加载已爬取的数据
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                all_customers = json.load(f)
            print(f"已加载 {len(all_customers)} 条已有数据")
    
    sock = ws_connect(CDP_WS)
    print("✅ 已连接CDP")
    
    failed_pages = []
    start_time = time.time()
    
    for page in range(start_page, TOTAL_PAGES + 1):
        data = fetch_page(sock, page)
        if data and data.get('values'):
            all_customers.extend(data['values'])
            count = len(all_customers)
            
            if page % 10 == 0 or page == TOTAL_PAGES:
                elapsed = time.time() - start_time
                speed = count / elapsed if elapsed > 0 else 0
                pct = count / 66224 * 100
                eta = (66224 - count) / speed if speed > 0 else 0
                print(f"第{page}/{TOTAL_PAGES}页: +{len(data['values'])}条 | 累计{count}/66224 ({pct:.1f}%) | {speed:.0f}条/s | ETA:{eta:.0f}s")
            
            # 每20页保存一次
            if page % 20 == 0:
                with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                    json.dump(all_customers, f, ensure_ascii=False)
                save_progress(page, count)
                print(f"  💾 已保存 {count} 条")
        else:
            print(f"⚠️ 第{page}页获取失败")
            failed_pages.append(page)
        
        time.sleep(0.1)  # 避免过快
    
    sock.close()
    
    # 最终保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_customers, f, ensure_ascii=False)
    save_progress(TOTAL_PAGES, len(all_customers))
    
    elapsed = time.time() - start_time
    print(f"\n✅ 爬取完成！共 {len(all_customers)} 条，耗时 {elapsed:.1f}s")
    if failed_pages:
        print(f"⚠️ 失败页面: {failed_pages}")
    print(f"保存: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
