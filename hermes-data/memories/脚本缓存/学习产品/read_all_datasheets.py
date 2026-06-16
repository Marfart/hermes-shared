#!/usr/bin/env python
"""Read ALL Data Sheet .docx files under 产品规格书/英文资料 - no skips, no shortcuts!"""
from docx import Document
import os, sys

base = r"C:\Users\Admin\Desktop\Working\产品规格书\英文资料"

# Find ALL *Data Sheet*.docx files
all_sheets = []
for root, dirs, files in os.walk(base):
    for f in files:
        if 'Data Sheet' in f and f.endswith('.docx'):
            all_sheets.append(os.path.join(root, f))

all_sheets.sort()
print(f"Total *Data Sheet* docx found: {len(all_sheets)}")
print()

for fpath in all_sheets:
    rel = os.path.relpath(fpath, base)
    try:
        doc = Document(fpath)
        pars = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        
        print(f"\n{'='*60}")
        print(f"📄 {rel}")
        print(f"{'='*60}")
        
        # Print ALL meaningful text (up to 30 lines)
        count = 0
        for p in pars:
            if len(p) > 5:
                # Skip only pure copyright/website boilerplate
                if p in ['www.bliiot.com', 'https://www.bliiot.com/', 'https://bliiot.com']:
                    continue
                print(f"  {p[:300]}")
                count += 1
                if count >= 30:
                    remaining = len([x for x in pars if len(x) > 5]) - count
                    if remaining > 0:
                        print(f"  ... and {remaining} more lines")
                    break
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"📄 {rel}")
        print(f"{'='*60}")
        print(f"  ❌ ERROR: {e}")
    
    sys.stdout.flush()

print(f"\n{'='*60}")
print(f"✅ DONE! Read {len(all_sheets)} datasheets total")
print(f"{'='*60}")
