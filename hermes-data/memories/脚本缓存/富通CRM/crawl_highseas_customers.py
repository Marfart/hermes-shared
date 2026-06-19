"""
富通公海客户全量爬取脚本
通过CDP WebSocket连接已登录的Chrome，用fetch批量拉取客户数据
"""
import json, socket, base64, struct, time, os, sys

CDP_WS = "ws://127.0.0.1:9226/devtools/page/09B7ECBE4020E3E37AA5C19C37CB1DDB"
OUTPUT_FILE = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'Working', '富通CRM_公海客户_全量.json')
PAGE_SIZE = 200  # 每页200条

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

def ws_recv(sock, timeout=60):
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
    """拉取一页数据"""
    for attempt in range(max_retries):
        cmd = {
            "id": page_num + 1000,
            "method": "Runtime.evaluate",
            "params": {
                "expression": f"""
                    (async () => {{
                        let r = await fetch('/rapi/d/customers?num={page_num}&paging=true&size={PAGE_SIZE}&tab=1');
                        let j = await r.json();
                        return JSON.stringify({{total: j.data?.total, values: j.data?.values || []}});
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
            return val
        print(f"  第{page_num}页重试 {attempt+1}/{max_retries}...")
        time.sleep(2)
    return None

def main():
    print("=" * 60)
    print("富通公海客户全量爬取")
    print("=" * 60)
    
    # 连接CDP
    print("\n连接CDP...")
    sock = ws_connect(CDP_WS)
    print("✅ 已连接")
    
    # 先获取总数
    print("\n获取总数...")
    first_page = fetch_page(sock, 1)
    if not first_page:
        print("❌ 无法获取数据")
        return
    
    total = first_page['total']
    all_customers = first_page['values']
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    
    print(f"总客户数: {total}")
    print(f"每页: {PAGE_SIZE}")
    print(f"总页数: {total_pages}")
    print(f"第1页获取: {len(all_customers)} 条")
    
    # 逐页拉取
    for page in range(2, total_pages + 1):
        data = fetch_page(sock, page)
        if data and data.get('values'):
            all_customers.extend(data['values'])
            count = len(all_customers)
            pct = count / total * 100
            print(f"第{page}/{total_pages}页: +{len(data['values'])}条 | 累计{count}/{total} ({pct:.1f}%)")
        else:
            print(f"⚠️ 第{page}页获取失败，跳过")
        
        # 每10页保存一次
        if page % 10 == 0:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_customers, f, ensure_ascii=False)
            print(f"  💾 已保存 {len(all_customers)} 条")
        
        # 短暂延迟避免过快
        time.sleep(0.3)
    
    sock.close()
    
    # 最终保存
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_customers, f, ensure_ascii=False)
    
    print(f"\n✅ 爬取完成！共 {len(all_customers)} 条客户数据")
    print(f"保存位置: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
