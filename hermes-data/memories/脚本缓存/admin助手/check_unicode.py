import re

with open(r'C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\admin助手\gen_finance_pdf.py', 'rb') as f:
    data = f.read()

remaining = re.findall(b'\\\\u[0-9a-fA-F]{4}', data)
if remaining:
    print(f'Found {len(remaining)} remaining unicode escapes')
    for m in re.finditer(b'\\\\u[0-9a-fA-F]{4}', data):
        print(f'  Byte {m.start()}: {m.group().decode()}')
else:
    print('All clean!')
