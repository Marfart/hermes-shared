#!/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe
"""Post-process the saved docx to add watermark transparency to the header blip"""

import zipfile, os, shutil, tempfile
from lxml import etree as ET

INPUT = r"C:\Users\Admin\AppData\Local\hermes\更新后新文件.docx"
OUTPUT = r"C:\Users\Admin\Desktop\Working\津巴布尔客户\签署文件\更新后新文件_v3.0.docx"

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

tmpdir = tempfile.mkdtemp()
outdir = os.path.join(tmpdir, 'unpacked')

# Extract
with zipfile.ZipFile(INPUT, 'r') as z:
    z.extractall(outdir)

# Find and modify header files
for root, dirs, files in os.walk(outdir):
    for f in files:
        if f.startswith('header') and f.endswith('.xml'):
            path = os.path.join(root, f)
            tree = ET.parse(path)
            # Find all a:blip elements
            for blip in tree.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
                # Check if it's our watermark (from image size or context)
                # Add effects
                # Remove existing effects
                for child in list(blip):
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag in ('grayscl', 'alphaModFix', 'biLevel', 'clrChange', 'duotone'):
                        blip.remove(child)
                # Add grayscale
                grayscl = ET.SubElement(blip, '{http://schemas.openxmlformats.org/drawingml/2006/main}grayscl')
                # Add transparency
                alpha = ET.SubElement(blip, '{http://schemas.openxmlformats.org/drawingml/2006/main}alphaModFix')
                alpha.set('amt', '18000')
                print("  Added transparency to blip in: %s" % f)
            tree.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)

# Repack
output_dir = os.path.dirname(OUTPUT) if os.path.dirname(OUTPUT) else '.'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for root, dirs, files in os.walk(outdir):
        for f in files:
            fp = os.path.join(root, f)
            arcname = os.path.relpath(fp, outdir)
            zout.write(fp, arcname)

shutil.rmtree(tmpdir)
print("Done! Output: %s" % OUTPUT)
