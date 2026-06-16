import zipfile, xml.etree.ElementTree as ET

files_to_check = [
    ("BL116", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\ARM高性能网关\BL116\BLIIOT BL116 IIoT High-Performance Edge Gateway Data Sheet V1.0.docx"),
    ("BE116", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\ARM高性能网关\BE116\BLIIOT BE116 High-Performance Smart Grid Edge Gateways Data Sheet V1.0.docx"),
    ("BA116", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\ARM高性能网关\BA116\BLIIOT BA116 High-Performance Building HVAC Edge Gateway Data Sheet V1.0.docx"),
    ("BL118", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\ARM高性能网关\BL118\BLIIOT BL118 Node-RED Edge Gateway Datasheet V1.0.docx"),
    ("BL101", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BL10系列规格书\BLIIOT BL101 Data Sheet.docx"),
    ("BL110", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BL10系列规格书\BLIIOT BL110 Data Sheet.docx"),
    ("BL120", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BL120系列规格书\BLIIOT BL120 Data Sheet.docx"),
    ("BL121", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BL121系列规格书\BLIIOT BL121 Data Sheet.docx"),
]

keywords = ['vpn', 'firewall', 'dmz', 'it/ot', 'isolation', 'tls', 'ssl', 'encrypt', 'security', 
            'watchdog', 'reconnect', 'reconnection', 'remote', 'upgrade', 'opc ua', 'mqtt', 
            'modbus', 'sage', 'erp', 'historian', 'kpi', 'alarm', 'database', 'di', 'ai', 'do', 
            'io', 'local', 'cortex', 'processor', 'mcu', 'clock', 'mhz', 'rs485', 'rs232', 
            'rj45', 'ethernet', 'din', 'rail', '24v', 'power', 'voltage']

for name, path in files_to_check:
    print("=" * 60)
    print("=== " + name + " ===")
    print("=" * 60)
    try:
        z = zipfile.ZipFile(path)
        tree = ET.parse(z.open('word/document.xml'))
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        texts = []
        for p in tree.findall('.//w:p', ns):
            t = [t.text for t in p.findall('.//w:t', ns) if t.text]
            if t:
                texts.append(''.join(t))
        
        for kw in keywords:
            for line in texts:
                if kw in line.lower():
                    print("  [" + kw + "] " + line[:150])
                    break
    except Exception as e:
        print("  ERROR: " + str(e))
