#!/usr/bin/env python3
"""Quick test: DuckDuckGo LinkedIn X-Ray queries"""
import urllib.request, urllib.parse, json, re, time

def ddgs_search(query, limit=10):
    """Search via DuckDuckGo lite"""
    url = "https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({"q": query}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return []
    
    results = []
    # Parse DDG lite results - they use <a> tags with rel="nofollow" then class
    # Actually let's use a different approach - regex
    # Find result blocks
    blocks = re.findall(r'<tr[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</tr>', html, re.DOTALL)
    if not blocks:
        # Try alternate DDG format
        blocks = re.findall(r'<div[^>]*class="[^"]*result[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    
    for block in blocks:
        link_match = re.search(r'href="(https://[^"]+)"[^>]*>(.*?)</a>', block, re.DOTALL)
        snippet_match = re.search(r'class="[^"]*snippet[^"]*"[^>]*>(.*?)</', block, re.DOTALL)
        
        if link_match:
            url = link_match.group(1).split('?')[0]
            title = re.sub(r'<[^>]+>', '', link_match.group(2)).strip()
            snippet = ""
            if snippet_match:
                snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
            
            if 'linkedin.com/in/' in url:
                results.append({"title": title, "url": url, "snippet": snippet})
    
    return results[:limit]


queries = [
    'site:linkedin.com/in/ "system integrator" "South Africa"',
    'site:linkedin.com/in/ "IIoT" "Africa" engineer gateway',
    'site:linkedin.com/in/ "remote monitoring" "Africa" SCADA',
    'site:linkedin.com/in/ "industrial automation" Kenya Nigeria',
    'site:za.linkedin.com/in/ "PLC" OR "SCADA"',
    'site:linkedin.com/in/ "automation" "South Africa" engineer',
    'site:linkedin.com/in/ "industrial" "IoT" "Africa" engineer',
]

all_results = []
seen_urls = set()

for i, q in enumerate(queries):
    print(f"\n[{i+1}/{len(queries)}] {q[:70]}")
    results = ddgs_search(q, limit=10)
    print(f"  → {len(results)} LinkedIn results")
    
    for r in results:
        url = r['url']
        if url not in seen_urls:
            seen_urls.add(url)
            all_results.append(r)
            # Parse: "Name - Title - Company | LinkedIn"
            title = r['title'].replace(' | LinkedIn', '').replace(' - 领英', '').strip()
            parts = [p.strip() for p in title.split(' - ')]
            name = parts[0] if len(parts) >= 1 else '?'
            job = parts[1] if len(parts) >= 2 else '?'
            company = parts[2] if len(parts) >= 3 else ''
            snippet = r['snippet'][:100]
            print(f"  ✓ {name:25s} | {job:30s} | {company or '-':20s}")
    
    time.sleep(1)

print(f"\n{'='*60}")
print(f"📊 TOTAL: {len(all_results)} unique LinkedIn profiles found")
print(f"{'='*60}")