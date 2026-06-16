#!/usr/bin/env python3
"""Read BLIIoT product specification documents."""
from docx import Document
import os

base = r"C:\Users\Admin\Desktop\Working\新建文件夹\EdgePlc\EdgePLC_Specification_Document"

files = [
    'EdgePLC BL233系列工业边缘控制器规格书V1.1.docx',
    'EdgePLC BL234系列工业边缘控制器规格书V1.1.docx',
    'EdgePLC BL237系列工业AI边缘控制器规格书V1.1.docx',
    'EdgePLC BL241系列工业AI边缘控制器规格书V1.1.docx',
    'EdgePLC BL244系列工业AI边缘控制器规格书V1.1.docx',
    'EdgePLC BL245系列工业AI边缘控制器规格书V1.1.docx',
    'EdgePLC BL246系列工业AI边缘控制器规格书V1.1.docx',
    'EdgePLC BL235系列工业边缘控制器规格书V1.1.docx',
]

for fname in files:
    path = os.path.join(base, fname)
    if not os.path.exists(path):
        print(f"=== {fname} === NOT FOUND")
        continue
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    product_name = paragraphs[0] if paragraphs else "Unknown"
    print(f"\n{'='*60}")
    print(f"📄 {fname}")
    print(f"{'='*60}")
    # Print first 40 meaningful paragraphs
    for i, p in enumerate(paragraphs[:50]):
        if len(p) > 3:  # Skip very short lines
            print(f"  {p[:300]}")
    print()

# Also check price lists for product lineup
price_base = r"C:\Users\Admin\Desktop\Working\1.报价文件"
import glob
xls_files = glob.glob(os.path.join(price_base, "*.xls")) + glob.glob(os.path.join(price_base, "*.xlsx"))
for f in sorted(xls_files):
    print(f"💰 Price List: {os.path.basename(f)}")
print()
