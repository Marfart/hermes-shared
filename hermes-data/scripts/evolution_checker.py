#!/usr/bin/env python3
"""自主进化学习 - no_agent 版本
检查 GitHub trending + 新工具/技能，只在新东西有变化时输出"""
import urllib.request, json, os, re, textwrap
from datetime import datetime

CACHE_FILE = os.path.expanduser("~/AppData/Local/hermes/memories/进化缓存.json")

def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
    except: pass
    return {"last_trending": [], "last_seen": ""}

def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except: return None

def check_trending():
    """Check GitHub trending repos"""
    data = fetch("https://api.github.com/search/repositories?q=created:>2026-05-01+pushed:>2026-06-01&sort=stars&order=desc&per_page=10")
    if not data or "items" not in data:
        return []
    results = []
    for r in data["items"]:
        results.append({
            "name": r["full_name"],
            "stars": r["stargazers_count"],
            "desc": (r.get("description") or "")[:120],
            "url": r["html_url"]
        })
    return results

def main():
    cache = load_cache()
    trending = check_trending()
    
    if not trending:
        return  # silent on error
    
    # Find new items not in cache
    old_names = {r["name"] for r in cache.get("last_trending", [])}
    new_items = [r for r in trending if r["name"] not in old_names and r["stars"] > 20]
    
    if new_items:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        print(f"🔬 新发现 {len(new_items)} 个热门项目 ({timestamp}):")
        for item in new_items[:5]:
            print(f"\n• {item['name']} ⭐{item['stars']}")
            if item["desc"]:
                print(f"  {textwrap.shorten(item['desc'], width=100)}")
    
    # Save updated cache
    save_cache({"last_trending": trending, "last_seen": datetime.now().isoformat()})

if __name__ == "__main__":
    main()