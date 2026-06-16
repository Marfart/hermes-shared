# Digital File / Ebook Search Methodology

> Kali expects thorough multi-source searching before reporting "not found".
> Frustration signal: "你搜过资源都不行吗" — means I gave up too early.
> CORRECTION 2026-06-08: Did NOT search LibGen (libgen.ee, accessible via browser) or multiple Z-Lib domains before concluding. Search was shallow — only web_search then gave up. Must go browser → LibGen → Z-Lib (try 3+ domains) → Anna's Archive in sequence.

## Search Priority Chain

When searching for a digital file (ebook PDF/EPUB, software download, etc.):

### Phase 1 — Official / Author Sources (always check first)
1. Author's own website (e.g. `rudyrucker.com/mirrorshades/` — many authors host their own work)
2. Internet Archive (`archive.org/details/<id>` — huge catalog, many formats)
3. GitHub releases / repo README links
4. Publisher's site / official download page

### Phase 2 — Shadow Libraries (use browser, not just web_search)
1. **Library Genesis** (`libgen.ee` or any `.li/.lc/.vg/.la/.bz/.gl` mirror) — search by ISBN or exact title. Accessible via browser (no Cloudflare). Try both "Fiction" and "Libgen" sections.
2. **Z-Library** (`z-lib.fm`, `1lib.sk`, `z-library.sk`, `z-lib.gd`, `z-lib.gl`, `z-lib.fo`) — often Cloudflare-blocked; try multiple domains. If 503 on one, try another.
3. **Anna's Archive** (`annas-archive.org` / `annas-archive.gl`) — aggregates LibGen + Z-Lib + Sci-Hub
4. **OceanofPDF** (`oceanofpdf.com`) — good for popular English titles
5. **PDFCoffee** (`pdfcoffee.com`) — user-uploaded PDFs

### Phase 3 — Chinese eBook Sharing Sites (for Chinese titles)
1. **微信读书** (`weread.qq.com`) — largest Chinese ebook platform; paid membership required
2. **当当云阅读** (`e.dangdang.com`) — paid
3. **小哈图书下载中心** (`qciss.net`) — metadata only, check for real links
4. **荷花书海** (`zyfttc.github.io/qingchunwenxue/`) — metadata only, links are `javascript:void(0)` placeholders
5. **教客网** (`jiaokey.com`) — may require registration
6. **百度网盘 / 阿里云盘** — search via web search `site:pan.baidu.com` or `site:aliyundrive.com`

### Phase 4 — General Web Search Strategies
- Search by ISBN: `9787569947038 epub 下载`
- Search by exact title in quotes: `"镜影：赛博朋克文学选" 下载`
- Try different file extensions: `pdf`, `epub`, `mobi`, `azw3`
- Try different keywords: `百度网盘`, `百度云`, `阿里云盘`
- Try Chinese forums: 知乎专栏, 贴吧, etc.

## File Format Preferences (Kali)
- **PDF** — best for reading on any device
- **EPUB** — best for ebook readers / phones
- **MOBI** — Kindle format
- ✅ **EPUB from author's own site** — best quality, trusted source (confirmed: Rudy Rucker hosts mirrorshades.epub at rudyrucker.com/mirrorshades/)
- ❌ **HTML** — do NOT give HTML when PDF/EPUB exists
- ❌ **Text excerpts** — do NOT paste book content as text message

## Book Name Accuracy

- Always verify the EXACT title before searching. If user says "静影" and search returns nothing, check if it might be "镜影" (common mishearing in Chinese).
- For translated books, search by:
  - Chinese title (`镜影：赛博朋克文学选`)
  - English original title (`Mirrorshades: The Cyberpunk Anthology`)
  - ISBN (`9787569947038`)
  - Author name (Bruce Sterling)

## When a File Isn't Available Free

If after checking ALL sources above the file is unavailable:
1. Report specifically which sources were checked and what each returned
2. Note if it's a recent publication (post-2020 / post-2023) — these are usually not on shadow libraries
3. Offer the nearest alternative (e.g. English original if Chinese unavailable)
4. Note paid access routes (微信读书会员, 当当购买, etc.)
5. Do NOT just say "can't find it" — give Kali options

## Verification After Download
- Check file size is reasonable (e.g. 500KB+ for a book EPUB, not 37KB scrap)
- For EPUB: should be 500KB-5MB for a full book
- For PDF: should be 2MB-50MB depending on images
- If suspiciously small, it's probably a sample/scrap — try another source

## Real Case: 镜影：赛博朋克文学选 (2026-06-08)

Search sequence and results:
1. ❌ web_search("镜影 赛博朋克文学选 pdf") — poor results, mostly unrelated
2. ✅ web_search("Mirrorshades: Cyberpunk Anthology epub") — found Rudy Rucker's official EPUB at rudyrucker.com/mirrorshades/mirrorshades.epub — **downloaded successfully**
3. ✅ Internet Archive (archive.org/details/mirrorshades00bruc) — has the English original
4. ❌ Z-Library (z-lib.fm, 1lib.sk) — 503 / Cloudflare blocked
5. ✅ LibGen (libgen.ee via browser) — searched by Chinese title and ISBN, 0 results
6. ❌ 小哈图书下载中心 (qciss.net) — metadata only, no real links
7. ❌ 荷花书海 (zyfttc.github.io) — download links all javascript:void(0) placeholders
8. ✅ 微信读书 (weread.qq.com) — has the Chinese version, paid only

**Result**: English EPUB acquired (author-official). Chinese version is 2023 publication, not on any shadow library. Only available via 微信读书会员 or purchase.

**Lesson**: 2023 Chinese publications are almost never on shadow libraries. Don't waste time on Chinese ebook aggregation sites (their download links are fake). Go straight to 微信读书 for Chinese new books.
