---
name: workspace-document-retrieval
title: Workspace Document Retrieval
description: Find, validate, and deliver product documents (datasheets, manuals, specs) from a user's business workspace — including fallback when direct file transfer fails.
tags: [file-search, pdf, document-delivery, fallback, send_message, wechat]
---

# Workspace Document Retrieval

Find a product document the user asks for, verify it's valid, and attempt delivery. **Only extract content as a last resort** — when asked for a file, deliver the file.

## Workflow

### 1. Search for the file

Use `search_files(target='files')` with multiple patterns to locate documents:

```
search_files(pattern='*BL335*', target='files')                    # glob by product name
search_files(pattern='*BL335*.pdf', target='files')                 # narrow to PDFs
search_files(pattern='BL335', path='产品规格书')                     # search under specific dir
```

Check both language-directory mirrors (e.g. `产品规格书` and `英文资料`) since documents often exist in both.

Common document types to expect:
- Datasheets (`*Datasheet V*.pdf`, `*Datasheet V*.docx`)
- User manuals (`*User Manual V*.pdf`)
- Product images (`*.png`, `*.jpg`)
- Price lists (`*Price List*.xls`, `*Price List*.xlsx`)

### 2. Validate file integrity

Use `file` command to confirm the file is valid before attempting delivery:

```bash
file "/path/to/file.pdf"
# Expected: "PDF document, version X.Y, N page(s)"
```

Check file size with `ls -lh` — very small PDFs may be truncated/corrupt.

### 3. Attempt file delivery (send the file, not the content)

**DO NOT extract and present the document content first. When the user asks for a file, deliver the file itself.** A brief confirmation of what you found (title, format, page count) is OK, but do not dump the full content.

#### Method A: send_message with MEDIA path (PREFERRED — most reliable)

```python
# Copy file to Hermes-accessible location first
cp "/path/to/original/file.pdf" "/c/Users/Admin/AppData/Local/hermes/file.pdf"

# Send via send_message with MEDIA:path in the message text
send_message(
    target="weixin",  # or the appropriate platform
    message="File Name.pdf\nMEDIA:C:\Users\Admin\AppData\Local\hermes\file.pdf"
)
```

The `MEDIA:` prefix in the message text triggers native file delivery on the platform. On WeChat, inline `MEDIA:/path` in the assistant text response does NOT work — you MUST use send_message.

#### Method B: Inline MEDIA: in response text (less reliable)

Some platforms support `MEDIA:/absolute/path/to/file.pdf` in the assistant's text response. WeChat does NOT reliably deliver files this way — prefer Method A.

#### Method C: Format fallback

If PDF delivery fails (common on WeChat), try sending the DOCX version instead:

```
cp "/path/to/Datasheet V1.0.docx" "/c/Users/Admin/AppData/Local/hermes/Datasheet.docx"
send_message(target="weixin", message="Datasheet V1.0.docx\nMEDIA:C:\Users\Admin\AppData\Local\hermes\Datasheet.docx")
```

DOCX files often transfer more reliably than PDFs on mobile chat platforms.

### 4. Content extraction (LAST RESORT only)

Only extract and present content inline when:
- The user confirms file delivery failed after trying all delivery methods above
- The user explicitly asks to "see what's inside" or "tell me about the file"
- File transfer is fundamentally not supported on the current platform

**Never extract full content unprompted when the user asked for a file.**

```bash
pdftotext "/path/to/file.pdf" - 2>/dev/null
```

When presenting extracted content, format as a clean markdown summary:
1. **Header block**: Title, version, date, manufacturer
2. **Key specifications table**: CPU, memory, I/O, power, dimensions
3. **Feature highlights**: bullet points
4. **Offer related files**: images, price lists, user manuals

## Pitfalls

- **On WeChat, PDF/DOCX file transfer may silently fail via inline MEDIA:. Always use send_message with MEDIA: embedded in the message text.**
- Copy the file to `C:\Users\Admin\AppData\Local\hermes\` before attempting send_message delivery — the Hermes media delivery system may require files to be under configured allowed directories.
- If the user says "打不开" (can't open), try the alternative format (PDF ↔ DOCX) before resorting to content extraction.
- If send_message fails too, check file permissions and confirm the file actually exists at the path you're referencing.
- **User preference discovered**: This user explicitly rejected content extraction ("不要内容，我要文件"). Respect this — always try harder to deliver the actual file.

## User preferences to respect

- On WeChat, always attempt send_message delivery with MEDIA path before considering fallbacks.
- After successful delivery, optionally offer related files (images, price lists, manuals) so the user can ask for the next one.
- Present summaries in the user's language (Chinese for Chinese-speaking users).
