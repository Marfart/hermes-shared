#!/usr/bin/env python3
"""
Content Feed Harvester v5.1 - No-agent mode feeds for cron agent to read & summarize
8 sources, 6 categories, parallel fetch with proxy-safe concurrency
"""
import json, os, re, subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import xml.etree.ElementTree as ET

STATUS_FILE = r"C:\Users\Admin\AppData\Local\hermes\scripts\feed_status.json"

NEGATIVE_KEYWORDS = ['战争','死亡','选举','政治','暴力','冲突','斗争','战乱','灾难','伤亡','政变','政策','政府','战场',
                   'death','war','election','politics','violence','trump','biden','dies','dead','killed','assault',
                   'shooting','bomb','terror','murder','suicide','屠杀','枪击','炸弹','恐怖',
                   'airstrike','military','missile','sanction','deportation','mass deportation',
                   'truce','clashes','iran','congress just','dhs funding','reconciliation bill']

SOURCES = [
    ('https://www.theverge.com/rss/index.xml', True, 'verge', '🤖', '科技AI'),
    ('https://www.eurogamer.net/feed', False, 'eurogamer', '🎮', '游戏'),
    ('https://www.animenewsnetwork.com/rss.xml', False, 'ann', '🌸', '动漫'),
    ('https://www.stereogum.com/feed', False, 'stereogum', '🎵', '音乐'),
    ('https://www.freejazzblog.org/feeds/posts/default', False, 'freejazz', '🎷', '爵士'),
    ('https://feeds.bloomberg.com/markets/news.rss', False, 'bloomberg', '💰', '财经'),
    ('https://www.technologyreview.com/feed/', False, 'mit_tech', '🔬', '前沿科技'),
    ('https://feeds.arstechnica.com/arstechnica/index', False, 'ars', '⚡', 'Ars Technica'),
]

def is_negative(text):
    if not text: return True
    tl = text.lower()
    return any(kw in tl for kw in NEGATIVE_KEYWORDS)

def fetch_one_source(url, is_atom):
    try:
        r = subprocess.run(['curl', '-s', '--connect-timeout', '8', '--max-time', '12', '-L', url],
                         capture_output=True, text=True, timeout=15)
        content = r.stdout
        if not content or len(content) < 100:
            return []
        items = []
        if is_atom:
            titles = re.findall(r'<title[^>]*><!\[CDATA\[([^\]]+)\]\]></title>', content)
            links = re.findall(r'<link[^>]+href="([^"]+)"[^>]*/>', content)
            feed_start = 2
            for i, t in enumerate(titles):
                link = links[i+feed_start] if i+feed_start < len(links) else ''
                if link and not is_negative(t):
                    items.append({'title': t.strip(), 'link': link.strip()})
        else:
            try:
                root = ET.fromstring(content)
                for item in root.findall('.//item')[:10]:
                    t = item.find('title')
                    l = item.find('link')
                    if t is not None and t.text:
                        title = t.text.strip()
                        link = l.text.strip() if l is not None else ''
                        if not is_negative(title):
                            items.append({'title': title, 'link': link})
            except ET.ParseError:
                return []
        return items[:5]
    except:
        return []

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    s = {}
    for _, _, key, _, _ in SOURCES:
        s[key] = []
    return s

def save_status(status):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def main():
    now = datetime.now()
    if 1 <= now.hour < 7:
        return
    status = load_status()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for url, is_atom, key, _, _ in SOURCES:
            futures[executor.submit(fetch_one_source, url, is_atom)] = (url, is_atom, key)
        results = {}
        for fut in as_completed(futures):
            _, _, key = futures[fut]
            try:
                results[key] = fut.result()
            except:
                results[key] = []
    output_lines = []
    for url, is_atom, key, emoji, label in SOURCES:
        items = results.get(key, [])
        seen = set(status.get(key, []))
        new_items = []
        for item in items:
            link = item.get('link', '')
            if link and link not in seen:
                new_items.append(item)
                seen.add(link)
        status[key] = list(seen)[-50:]
        if not new_items:
            continue
        picks = new_items[:min(2, len(new_items))]
        for item in picks:
            output_lines.append(f"{emoji} {label}: {item['title']}")
            output_lines.append(f"LINK:{item['link']}")
    save_status(status)
    if output_lines:
        print("\n".join(output_lines))

if __name__ == '__main__':
    main()