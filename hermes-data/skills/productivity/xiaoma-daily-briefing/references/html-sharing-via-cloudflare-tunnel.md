# HTML Sharing via Cloudflare Tunnel

## Method 1: Cloudflare Tunnel (Primary — works from China, no VPN needed)

### Prerequisites
- cloudflared binary at `C:\Users\Admin\Desktop\Working\cf.exe` (v2026.6.0+)
- Original download at `C:\Users\Admin\Desktop\Working\cloudflared.exe` (may be file-locked by background processes)
- Local HTTP server running on port 8899

### ⛔ Critical: Do NOT compress images for upload!

Cloudflare Tunnel has NO file size limit. The daily HTML can be 9MB+ and still transfer fine (tested at 9.5MB, 39s transfer, HTTP 200).

**Kali explicitly rejected compressed images**: When I compressed images to 400px q35 to fit under hosting size limits, she said "图这么糊，你在搞什么，对应的图也没了". 

**Rule: 1200px width minimum, JPEG q85, never sacrifice quality for file size.**

### Steps

1. Kill existing servers if needed:
```bash
pkill -f "http.server 8899"
pkill -f "cf.exe tunnel"
```

2. Start local HTTP server (background):
```bash
cd ~/Desktop/Working/Hermes && python -m http.server 8899 --bind 0.0.0.0 &
```
Or use terminal(background=true) for long-lived server.

3. Start Cloudflare tunnel (background):
```bash
/c/Users/Admin/Desktop/Working/cf.exe tunnel --url http://localhost:8899 2>&1 | tee /tmp/cf_tunnel.log &
```
**Note**: The original `cloudflared.exe` gets file-locked by background downloads. Always use the `cf.exe` copy instead.

4. Wait for URL (appears in log within ~10-15s):
```bash
sleep 15 && grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/cf_tunnel.log | head -1
```

5. Verify:
```bash
curl --noproxy "*" -s -o /dev/null -w "HTTP %{http_code}, size %{size_download}" "https://XXXXX.trycloudflare.com/Small_Horse_Daily_YYYY-MM-DD.html"
```
For large files (>5MB), use `--max-time 120` for the transfer.

6. Share: `https://XXXXX.trycloudflare.com/Small_Horse_Daily_YYYY-MM-DD.html`

### Important Notes
- URL changes every time tunnel restarts (random subdomain)
- No account needed (quick tunnel mode)
- Works from China without VPN — this is THE method for sharing with Kali's contacts
- Tunnel stays alive as long as the process runs
- Scanning bots will probe the tunnel URL on random ports — these ERR entries in the log are normal and harmless
- For large files (9MB+), allow 30-60s for full transfer verification
- If tunnel process dies, just restart — you'll get a new URL

### Troubleshooting
- **cloudflared.exe file locked**: Use `cf.exe` copy instead. Original gets locked by background curl processes.
- **HTTP 530 from tunnel**: Tunnel not ready yet. Wait 10-15 seconds and retry.
- **Old URL not working**: Tunnel URLs are ephemeral. Restart gives new URL.
- **Port 8899 occupied**: `pkill -f "http.server 8899"` then restart.

## Method 2: File Hosting Services (ALL FAILED as of 2026-06-12)

### catbox.moe — DOES NOT WORK for HTML
- Returns "Invalid uploader" for HTML files via API
- Only works for image/video files

### litter.catbox.moe — DOES NOT WORK (API path changed)
- Old endpoint returns 404
- 24h temp hosting no longer functional for HTML

### 0x0.st — DISABLED
- "uploads disabled because it's been almost nothing but AI botnet spam"

### file.io — REDIRECTS TO MARKETING PAGE
- Returns HTML marketing page instead of JSON upload response

### tmpfiles.org — REJECTS HTML
- Returns 422 "Invalid file type" for .html files

### transfer.sh — SSL FAILURE
- Connection refused / SSL EOF on Windows

### pixeldrain — REQUIRES AUTH
- 401 authentication required for API uploads

### gofile.io — API CHANGED
- Server endpoint lookup returns "error-notFound"

### GitHub Gist — PAT LACKS PERMISSION
- Returns 403 "Resource not accessible by personal access token"

### GitHub Pages — PAT LACKS REPO CREATION
- Cannot create new repos via PAT

### rentry.co — Text only, no HTML rendering
- Works for plain text paste only
- Does NOT render HTML

## Summary: Use Cloudflare Tunnel (Method 1) for ALL HTML sharing. No reliable free file host currently accepts HTML files. NEVER compress images to fit size limits — Cloudflare Tunnel has no size limit.