#!/usr/bin/env python3
"""
Content Feed Harvester v8 — 信息顶端系统
早晚7点推送，60+源，5层信息架构
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

# 5层信息源
SOURCES = [
    # ═══ L1: 原始发布层（距离事实源头最近）═══
    # 🧠 AI官方实验室
    ('https://blog.google/technology/ai/rss/', False, 'google_ai', '🧠', 'Google AI'),
    ('https://venturebeat.com/category/ai/feed/', False, 'venturebeat', '🧠', 'VentureBeat'),
    ('https://techcrunch.com/feed/', False, 'techcrunch', '🧠', 'TechCrunch'),
    ('https://blogs.nvidia.com/feed/', False, 'nvidia', '🧠', 'NVIDIA'),
    ('https://huggingface.co/blog/feed.xml', False, 'huggingface', '🧠', 'HuggingFace'),
    ('https://www.w3.org/blog/news/feed/', False, 'w3c', '🧠', 'W3C'),
    # 📄 论文预印本
    ('https://arxiv.org/rss/cs.AI', False, 'arxiv_ai', '📄', 'arXiv AI'),
    ('https://arxiv.org/rss/cs.LG', False, 'arxiv_lg', '📄', 'arXiv ML'),
    ('https://arxiv.org/rss/cs.CL', False, 'arxiv_cl', '📄', 'arXiv NLP'),
    ('https://arxiv.org/rss/cs.CV', False, 'arxiv_cv', '📄', 'arXiv Vision'),
    ('https://arxiv.org/rss/cs.CR', False, 'arxiv_cr', '📄', 'arXiv安全'),
    ('https://arxiv.org/rss/quant-ph', False, 'arxiv_qp', '📄', 'arXiv量子'),
    ('https://arxiv.org/rss/astro-ph', False, 'arxiv_astro', '📄', 'arXiv天文'),
    ('https://arxiv.org/rss/q-fin', False, 'arxiv_qfin', '📄', 'arXiv量化金融'),
    ('https://arxiv.org/rss/stat.ML', False, 'arxiv_sml', '📄', 'arXiv统计ML'),
    ('https://arxiv.org/rss/econ', False, 'arxiv_econ', '📄', 'arXiv经济'),
    # 🔬 顶级期刊
    ('https://www.nature.com/nature.rss', False, 'nature', '🔬', 'Nature'),
    ('https://www.nature.com/nclimate.rss', False, 'nature_climate', '🌱', 'Nature Climate'),
    ('https://www.pnas.org/rss/current.xml', False, 'pnas', '🔬', 'PNAS'),
    ('https://www.cell.com/cell/current.rss', False, 'cell', '🧬', 'Cell'),
    ('https://www.thelancet.com/rssfeed/lancet_current.xml', False, 'lancet', '🏥', 'Lancet'),
    ('https://www.nejm.org/action/showFeed?jc=nejm&type=etoc', False, 'nejm', '🏥', 'NEJM'),
    # 🏛️ 央行/监管
    ('https://www.federalreserve.gov/feeds/press_all.xml', False, 'fed', '🏛️', '美联储'),
    ('https://www.federalreserve.gov/feeds/speeches.xml', False, 'fed_speech', '🏛️', '美联储演讲'),
    ('https://www.federalreserve.gov/feeds/feds.xml', False, 'fed_research', '🏛️', '美联储论文'),
    ('https://www.ecb.europa.eu/rss/press.html', False, 'ecb', '🏛️', '欧洲央行'),
    ('https://www.imf.org/en/News/RSS', False, 'imf', '🏛️', 'IMF'),
    # 🌍 政府/国际组织
    ('https://www.ipcc.ch/feed/', False, 'ipcc', '🌍', 'IPCC气候'),
    ('https://www.unocha.org/rss.xml', False, 'unocha', '🌍', 'UN OCHA'),
    ('https://ec.europa.eu/commission/presscorner/api/rss', False, 'eu', '🌍', 'EU委员会'),
    ('https://www.cisa.gov/news.xml', False, 'cisa', '🛡️', 'CISA安全'),
    ('https://www.federalregister.gov/documents/search.rss', False, 'fedreg', '📜', '联邦公报'),
    # 🌌 太空
    ('https://www.nasa.gov/rss/dyn/breaking_news.rss', False, 'nasa', '🌌', 'NASA'),
    ('https://www.space.com/feeds/all', False, 'space', '🌌', 'Space.com'),
    ('https://spacenews.com/feed/', False, 'spacenews', '🌌', 'SpaceNews'),
    # 🌎 环境/健康
    ('https://www.noaa.gov/rss.xml', False, 'noaa', '🌎', 'NOAA气候'),
    ('https://www.who.int/rss-feeds/news-english.xml', False, 'who', '🏥', 'WHO'),
    
    # ═══ L2: 专家解释层 ═══
    ('https://www.technologyreview.com/topic/artificial-intelligence/feed/', False, 'mit_ai', '🔬', 'MIT Tech AI'),
    ('https://www.technologyreview.com/feed/', False, 'mit_all', '🔬', 'MIT Tech'),
    ('https://sciencedaily.com/rss/all.xml', False, 'sciencedaily', '🔬', 'ScienceDaily'),
    ('https://www.quantamagazine.org/feed/', False, 'quanta', '🔬', 'Quanta'),
    ('https://www.newscientist.com/feed/home/', False, 'newsci', '🔬', 'New Scientist'),
    ('https://feeds.feedburner.com/IeeeSpectrum', False, 'ieee', '⚡', 'IEEE Spectrum'),
    ('https://aeon.co/feed.rss', False, 'aeon', '📖', 'Aeon'),
    ('https://thenextweb.com/rss/index.xml', False, 'tnw', '🧠', 'TNW'),
    
    # ═══ L3: 聚合发现层 ═══
    ('https://hnrss.org/frontpage', False, 'hackernews', '🔍', 'Hacker News'),
    ('https://blog.cloudflare.com/rss/', False, 'cloudflare', '⚡', 'Cloudflare'),
    
    # ═══ 文化与审美 ═══
    ('https://blog.ted.com/feed/', False, 'ted', '🎨', 'TED Talks'),
    ('https://www.eurogamer.net/feed', False, 'eurogamer', '🎮', '游戏'),
    ('https://www.animenewsnetwork.com/rss.xml', False, 'ann', '🌸', '动漫'),
    ('https://www.freejazzblog.org/feeds/posts/default', False, 'freejazz', '🎷', '爵士'),
    ('https://www.stereogum.com/feed', False, 'stereogum', '🎵', '音乐'),
    
    # ═══ 经济/市场 ═══
    ('https://feeds.bloomberg.com/markets/news.rss', False, 'bloomberg', '💰', '财经'),
    ('https://feeds.marketwatch.com/marketwatch/topstories', False, 'marketwatch', '📈', '市场'),
    
    # ═══ 综合科技 ═══
    ('https://feeds.arstechnica.com/arstechnica/index', False, 'ars', '⚡', 'Ars Technica'),
]

def is_negative(text):
    if not text: return True
    tl = text.lower()
    return any(kw in tl for kw in NEGATIVE_KEYWORDS)

def fetch_one_source(url, is_atom):
    try:
        r = subprocess.run(['curl', '-s', '--connect-timeout', '8', '--max-time', '15', '-L', url],
                         capture_output=True, text=True, timeout=18)
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
                for item in root.findall('.//item')[:8]:
                    t = item.find('title')
                    l = item.find('link')
                    if t is not None and t.text:
                        title = t.text.strip()
                        link = l.text.strip() if l is not None else ''
                        if not is_negative(title):
                            items.append({'title': title, 'link': link})
            except ET.ParseError:
                return []
        return items[:4]
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
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for url, is_atom, key, _, _ in SOURCES:
            futures[executor.submit(fetch_one_source, url, is_atom)] = key
        
        results = {}
        for fut in as_completed(futures):
            key = futures[fut]
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
            output_lines.append("")
    
    save_status(status)
    
    if output_lines:
        print("\n".join(output_lines))

if __name__ == '__main__':
    main()