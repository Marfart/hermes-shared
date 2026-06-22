# Legacy .doc Format Extraction

BLIIOT's older product manuals (S275, K9, K5S, etc.) use the `.doc` format (Word 97-2003), not `.docx`. These cannot be opened with `python-docx` or `textract`.

## Working Methods

### 1. `antiword` (preferred, fast)
```bash
antiword /path/to/file.doc
# Available at: C:\Users\Admin\AppData\Local\hermes\git\mingw64\bin\antiword.exe
# Returns plain text to stdout
```

### 2. `win32com` (fallback, slower, requires Word installed)
```python
import win32com.client, os
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
doc = word.Documents.Open(os.path.abspath(path))
text = doc.Content.Text
doc.Close(False)
word.Quit()
```

### 3. `textract` (does NOT work on .doc)
```bash
textract file.doc  # Returns empty string — binary .doc not supported
```

## Known Legacy .doc Files

| File | Product | antiword result |
|------|---------|-----------------|
| S275 User Manual V1.3 | S275 RTU | 0 chars (corrupt/empty) |
| K9 User Manual V1.0 | K9 alarm panel | 39529 chars ✅ |
| K5S Data Sheet V1.3 | K5S DTU | 0 chars (corrupt/empty) |
| S475 User Manual V1.6.4 | S475 controller | 0 chars (corrupt/empty) |

If antiword returns 0 chars, the .doc file may be:
- Corrupted / zero-byte
- Actually a .docx file with wrong extension (try python-docx first)
- Contains only images (scanned document) — no text layer available

## For .doc Files That Yield No Text

1. Try renaming to .docx and opening with python-docx
2. Try win32com (sometimes handles corrupt files better)
3. Check file size — if < 1KB, it's likely corrupt
4. Search for a newer version of the same manual (BLIIOT has been migrating to .docx)
5. Contact the factory for an updated datasheet
