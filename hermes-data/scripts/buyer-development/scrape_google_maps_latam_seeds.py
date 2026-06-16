#!/usr/bin/env python3
"""Scrape Google Maps Latin America fresh leads via CDP"""
import asyncio, json, os, re, sys
from playwright.async_api import async_playwright

CDP_URL = "http://127.0.0.1:9226"
OUTPUT_DIR = r"C:\Users\Admin\AppData\Local\hermes\memories\buyer-development"
OLD_SEED = r"C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_seed_leads_2026-06-02.json"

QUERIES = [
    ("automação industrial São Paulo", "Brazil"),
    ("CLP SCADA Rio de Janeiro", "Brazil"),
    ("industrial automation Mexico City", "Mexico"),
    ("automatización industrial Buenos Aires", "Argentina"),
    ("system integrator Santiago Chile", "Chile"),
    ("automation control Bogotá", "Colombia"),
    ("IIoT integración industrial Lima", "Peru"),
    ("building automation Belo Horizonte", "Brazil"),
    ("SCADA Monterrey", "Mexico"),
    ("industrial control Campinas", "Brazil"),
]

def normalize_name(name):
    n = re.sub(r'\(.*?\)', '', name.lower())
    n = re.sub(r'\b(pty|ltd|limited|llc|inc|corp|company|co|gmbh|srl|bv|sa|spa|ltda|eireli|mei)\b', '', n)
    n = re.sub(r'[^a-z0-9]+', ' ', n).strip()
    return n

def normalize_phone(raw):
    digits = re.sub(r'\D', '', str(raw or ''))
    return f"+{digits}" if digits else ""

def parse_rating(text):
    m = re.search(r'([0-5]\.\d)', str(text or ''))
    return float(m.group(1)) if m else 0.0

async def main():
    with open(OLD_SEED, 'r', encoding='utf-8') as f:
        old_seeds = json.load(f)
    old_names = {normalize_name(s.get('name','')) for s in old_seeds}

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = await context.new_page()

        fresh = []
        seen = set()

        for query, country in QUERIES:
            if len(fresh) >= 40:
                break
            print(f"\n--- {query} ({country}) ---")

            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}?hl=en"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(8000)
            except Exception as e:
                print(f"  NAV ERR: {e}")
                continue

            links = await page.evaluate("""
                () => {
                    const links = [...document.querySelectorAll('a[href*="/maps/place/"]')];
                    const seen = new Set();
                    return links.filter(a => {
                        const name = (a.getAttribute('aria-label') || '').trim();
                        if (!name || seen.has(name)) return false;
                        seen.add(name);
                        return true;
                    }).slice(0, 15).map(a => ({
                        name: (a.getAttribute('aria-label') || '').trim(),
                        href: a.href
                    }));
                }
            """)

            for cand in links:
                if len(fresh) >= 40:
                    break
                nname = normalize_name(cand['name'])
                if not nname or nname in old_names or nname in seen:
                    continue

                ok = False
                for attempt in range(3):
                    try:
                        href = cand['href']
                        href = href.replace('hl=zh-CN','hl=en').replace('hl=zh','hl=en').replace('hl=ja','hl=en')
                        await page.goto(href, wait_until="domcontentloaded", timeout=60000)
                        await page.wait_for_timeout(7000)
                        ok = True
                        break
                    except:
                        await page.wait_for_timeout(3000)
                if not ok:
                    print(f"  SKIP (load fail): {cand['name']}")
                    continue

                data = await page.evaluate("""
                    () => {
                        const title = document.querySelector('h1')?.textContent?.trim() || '';
                        const website = document.querySelector('a[data-item-id="authority"]')?.href ||
                            document.querySelector('a[aria-label*="Website"]')?.href || '';
                        const phoneAria = document.querySelector('button[data-item-id^="phone:tel:"]')?.getAttribute('aria-label') || '';
                        const telHref = document.querySelector('a[href^="tel:"]')?.getAttribute('href') || '';
                        const addrAria = document.querySelector('button[data-item-id="address"]')?.getAttribute('aria-label') || '';
                        const body = document.body.innerText || '';
                        const typeEl = document.querySelector('button[class*="DkEaL"]');
                        const typeText = typeEl?.textContent?.trim() || '';
                        return { title, website, phoneAria, telHref, addrAria, body, typeText };
                    }
                """)

                body = data.get('body','')
                phone_match = re.search(r'\+55[\d\s\(\)-]{8,}\d', body) or \
                             re.search(r'\+52[\d\s\(\)-]{8,}\d', body) or \
                             re.search(r'\+56[\d\s\(\)-]{8,}\d', body) or \
                             re.search(r'\+57[\d\s\()-]{8,}\d', body) or \
                             re.search(r'\+51[\d\s\(\)-]{8,}\d', body) or \
                             re.search(r'\+54[\d\s\(\)-]{8,}\d', body) or \
                             re.search(r'\+\d[\d\s\(\)-]{6,}\d', body)

                phone = normalize_phone(phone_match.group(0) if phone_match else '')
                if not phone:
                    continue

                rating = parse_rating(body)
                if rating > 0 and rating < 4.0:
                    continue

                seen.add(nname)
                seed = {
                    'name': data['title'] or cand['name'],
                    'country': country,
                    'phone': phone,
                    'rating': rating,
                    'type': data.get('typeText','') or '',
                    'website': data.get('website',''),
                    'place_url': cand['href'],
                    'search_keyword': query,
                    'address': data.get('addrAria','').replace('Address: ','').strip(),
                }
                fresh.append(seed)
                print(f"  [{len(fresh)}] {seed['name'][:35]:35s} | ★{rating} | {phone[:18]:18s} | {country}")

        await browser.close()

    print(f"\n\n=== TOTAL FRESH SEEDS: {len(fresh)} ===")
    out_path = os.path.join(OUTPUT_DIR, "google_maps_latam_fresh_seeds_2026-06-02.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(fresh, f, indent=2, ensure_ascii=False)
    print(f"Saved: {out_path}")
    if fresh:
        print("Sample:", json.dumps(fresh[:3], indent=2, ensure_ascii=False))

if __name__ == '__main__':
    asyncio.run(main())