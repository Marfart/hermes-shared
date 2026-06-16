with open('smart_watchdog_v8.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有 add_msg 调用的参数，检查 GBK 可编码性
import re
for m in re.finditer(r'add_msg\(([^)]+)\)', content):
    arg = m.group(1)
    # 模拟 GBK 编码+cp936解码
    try:
        encoded = arg.encode('gbk')
        decoded = encoded.decode('cp936')
        ok = True
    except UnicodeEncodeError as e:
        ok = False
        bad_char = arg[e.start:e.end] if hasattr(e, 'start') else '?'
        print(f'[FAIL] 不可编码: {arg[:50]}... -> {e}')
    except:
        ok = True  # f-string with variables, skip
