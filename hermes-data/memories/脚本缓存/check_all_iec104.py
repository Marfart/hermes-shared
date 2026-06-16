import zipfile, xml.etree.ElementTree as ET

# === Check BE102P datasheet more thoroughly ===
p = r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\BL系列塑胶壳新型网关\英文规格书\BE10系列规格书\BLIIOT BE102P Data Sheet.docx"

with zipfile.ZipFile(p) as z:
    xml_content = z.read("word/document.xml")
    root = ET.fromstring(xml_content)
    texts = []
    for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        pt = []
        for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
            if t.text: pt.append(t.text)
        full = "".join(pt).strip()
        if full: texts.append(full)

print("=== BE102P 全文 ===")
for i, t in enumerate(texts):
    print(f"P{i}: {t[:300]}")

print("\n\n" + "="*80)

# === Check BE116 datasheet for timestamp/time tag ===
p2 = r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\ARM高性能网关\BE116\BLIIOT BE116 High-Performance Smart Grid Edge Gateways Data Sheet V1.0.docx"

with zipfile.ZipFile(p2) as z:
    xml_content = z.read("word/document.xml")
    root = ET.fromstring(xml_content)
    texts2 = []
    for para in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
        pt = []
        for t in para.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"):
            if t.text: pt.append(t.text)
        full = "".join(pt).strip()
        if full: texts2.append(full)

print("\n=== BE116 全文 ===")
for i, t in enumerate(texts2):
    print(f"P{i}: {t[:300]}")

print("\n\n=== BE116 中时间戳相关查找 ===")
for kw in ["time", "Time", "NTP", "SNTP", "clock", "CP56", "second", "minute", "hour", "date", "sync", "synchroni", "timestamp", "tag"]:
    matches = [(i, t) for i, t in enumerate(texts2) if kw.lower() in t.lower()]
    if matches:
        print(f"\n--- {kw} ({len(matches)} matches) ---")
        for i, t in matches[:5]:
            print(f"  P{i}: {t[:300]}")
