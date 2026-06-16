#!/usr/bin/env python3
"""
Content Feed Harvester Template
No-agent mode hourly feed with deduplication and negative keyword filtering
"""
import json, os, sys, re, random, subprocess
from datetime import datetime

STATUS_FILE = os.path.expanduser("~/.hermes/scripts/feed_status.json")
NEGATIVE_KEYWORDS = ['战争','死亡','选举','政治','暴力','冲突','斗争','灾难','政变','政策','政府','war','death','election','politics']

SOURCES = {
    'gaming': 'https://rss.ign.com/web/ign-china',
    'anime': 'https://myanimelist.net/rss/news.php',
    'ai_news': 'https://techcrunch.com/category/ai/feed/',
    'music': ['https://daily.bandcamp.com/feed', 'https://pitchfork.com/rss/news/']
}

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {k: [] for k in SOURCES.keys()}

def save_status(status):
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False)

def is_negative(text):
    if not text: return False
    return any(kw in text.lower() for kw in NEGATIVE_KEYWORDS)

def fetch_rss(url):
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', '--connect-timeout', '10', '--max-time', '15', url],
            capture_output=True, text=True, timeout=20
        )
        items = []
        titles = re.findall(r'<title>([^<]+)</title>', result.stdout)
        links = re.findall(r'<link[^>]*>([^<]+)</link>', result.stdout)
        for i, title in enumerate(titles[3:15]):
            if i+1 < len(links):
                items.append({'title': title.strip(), 'link': links[i+1]})
        return items
    except:
        return []

def select_new(items, key, status, count=2):
    seen = set(status.get(key, []))
    new = [i for i in items if i.get('link', '') not in seen and not is_negative(i.get('title', ''))]
    if new:
        status[key] = list(seen | {i['link'] for i in new})[-30:]
        return random.sample(new, min(count, len(new))), status
    return [], status

def main():
    hour = datetime.now().hour
    if hour >= 1 and hour < 7:
        print("")
        return
    
    status = load_status()
    results = []
    
    for key, url in SOURCES.items():
        urls = url if isinstance(url, list) else [url]
        for u in urls:
            items = fetch_rss(u)
            if items:
                selected, status = select_new(items, key, status, 1)
                for s in selected:
                    results.append(f"{CATEGORY_EMOJI.get(key, '📰')} {CATEGORY_NAME.get(key, key)}: {s['title']}\n🔗 {s['link']}")
    
    save_status(status)
    
    if results:
        print("\n\n".join(random.sample(results, min(3, len(results)))))

CATEGORY_EMOJI = {'gaming': '🎮', 'anime': '🌸', 'ai_news': '🤖', 'music': '🎧'}
CATEGORY_NAME = {'gaming': '游戏', 'anime': '动漫', 'ai_news': 'AI资讯', 'music': '音乐'}