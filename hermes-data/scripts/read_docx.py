import zipfile, xml.etree.ElementTree as ET, sys

path = sys.argv[1]
z = zipfile.ZipFile(path)
xml_content = z.read('word/document.xml')
root = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
texts = []
for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
    if t.text:
        texts.append(t.text)
print('\n'.join(texts))
