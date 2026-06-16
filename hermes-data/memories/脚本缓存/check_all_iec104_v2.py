import zipfile, xml.etree.ElementTree as ET

files = [
    ("BE190 IEC104 I/O Module", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\IOy系列多功能可编程远程IO\规格书\BLIIOT BE190 IOy Series IEC104 Edge IO Module Data Sheet V1.0.docx"),
    ("BE115P Energy Gateway", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BE10系列规格书\BLIIOT BE115P Data Sheet.docx"),
    ("BE115 Energy Gateway", r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BE10系列规格书\BLIIOT BE115 Data Sheet.docx"),
]

for name, path in files:
    print(f"\n{'='*80}")
    print(f"=== {name} ===")
    print(f"{'='*80}")
    try:
        with zipfile.ZipFile(path) as z:
            xml_content = z.read("word/document.xml")
            root = ET.fromstring(xml_content)
            texts = []
            for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                pt = []
                for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
                    if t.text: pt.append(t.text)
                full = "".join(pt).strip()
                if full: texts.append(full)
        
        # Search time-related keywords
        keywords = ["time", "Time", "NTP", "SNTP", "clock", "CP56", "second", "sync", "synchroni", "tag", "Tag", "stamp", "date", "hour", "minute"]
        found = False
        for kw in keywords:
            matches = [(i, t) for i, t in enumerate(texts) if kw.lower() in t.lower()]
            if matches:
                found = True
                print(f"\n--- {kw} ({len(matches)} matches) ---")
                for i, t in matches[:8]:
                    print(f"  P{i}: {t[:300]}")
        
        if not found:
            print("  (无时间相关内容)")
            
        # Print key paragraphs about IEC104
        print("\n--- IEC104 相关内容 ---")
        for i, t in enumerate(texts):
            if "iec104" in t.lower() or "iec 104" in t.lower() or "downlink" in t.lower() or "uplink" in t.lower() or "protocol" in t.lower():
                if len(t) > 15:
                    print(f"P{i}: {t[:350]}")
                    
    except Exception as e:
        print(f"  Error: {e}")
