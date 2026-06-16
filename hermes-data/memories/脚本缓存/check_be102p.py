import zipfile, xml.etree.ElementTree as ET

# Check BE102P datasheet for timestamp/time/NTP details
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
    
    for kw in ["time", "Time", "TIME", "timestamp", "Time stamp", "NTP", "SNTP", "clock", "CP56", "second", "minute", "hour", "date", "calendar", "sync", "synchroni"]:
        matches = [(i, t) for i, t in enumerate(texts) if kw.lower() in t.lower()]
        if matches:
            print(f"=== {kw} ({len(matches)} matches) ===")
            for i, t in matches[:10]:
                print(f"  P{i}: {t[:250]}")
            print()
    
    # Also dump key structural content
    print("=== Full text dump (all significant paragraphs) ===")
    for i, t in enumerate(texts):
        if len(t) > 15:
            print(f"P{i}: {t[:300]}")
