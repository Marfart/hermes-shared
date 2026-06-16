import zipfile, xml.etree.ElementTree as ET

p = r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料\ARM高性能网关\BE116\BLIIOT BE116 High-Performance Smart Grid Edge Gateways Data Sheet V1.0.docx"

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
    
    for kw in ["IEC104", "IEC 104", "IEC 60870", "timestamp", "time stamp", "CP56", "downlink", "uplink", "protocol", "substation", "power", "transformer"]:
        matches = [(i, t) for i, t in enumerate(texts) if kw.lower() in t.lower()]
        if matches:
            print(f"=== {kw} ({len(matches)} matches) ===")
            for i, t in matches[:8]:
                print(f"  P{i}: {t[:300]}")
            print()
    
    # Also check for supported protocols section
    print("=== Full Protocol/Downlink/Uplink content ===")
    for i, t in enumerate(texts):
        if any(x in t.lower() for x in ["downlink", "uplink", "protocol", "rtu master", "dlt"]):
            print(f"P{i}: {t[:350]}")
