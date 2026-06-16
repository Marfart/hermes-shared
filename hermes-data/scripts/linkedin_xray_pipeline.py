#!/usr/bin/env python3
"""
LinkedIn X-ray + Company Email Finder — 免登录爬取
====================================================
核心思路：
1. 用 DuckDuckGo 搜 LinkedIn 公开资料（X-ray 搜索）
2. 从 profile 页面提取人名、公司名、职位
3. 用公司名搜官网 → 爬 Contact/About 页取邮箱
4. 输出结构化 JSON 供 downstream 管道使用

完全不需 LinkedIn 登录，完全合法（Google 公开数据）
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlparse

import httpx

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("xray")

# ====================================================================
# 数据模型
# ====================================================================

@dataclass
class LinkedInLead:
    name: str
    title: str
    company: str
    location: str = ""
    linkedin_url: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    whatsapp: str = ""
    source_query: str = ""

@dataclass
class SearchConfig:
    queries: list[str] = field(default_factory=lambda: [
        # Africa - SCADA/PLC/IIoT
        'site:linkedin.com/in "SCADA" "South Africa" "system integrator"',
        'site:linkedin.com/in "PLC" "South Africa" "automation"',
        'site:linkedin.com/in "IIoT" "South Africa" "engineer"',
        'site:linkedin.com/in "industrial automation" "Nigeria" "engineer"',
        'site:linkedin.com/in "SCADA" "Kenya" "engineer"',
        'site:linkedin.com/in "PLC" "Zambia" OR "Zimbabwe" "engineer"',
        # Global - System Integrators
        'site:linkedin.com/company "system integrator" "industrial automation"',
        'site:linkedin.com/company "IIoT" "automation" "solutions"',
        'site:linkedin.com/in "SCADA" "PLC" "remote monitoring" "engineer" OR "manager"',
    ])
    max_results_per_query: int = 10

# ====================================================================
# 搜索引擎
# ====================================================================

class DuckDuckGoSearch:
    """用 DuckDuckGo 搜 LinkedIn 公开资料（免登录、免API key）"""
    
    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/134.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=15.0,
        )
    
    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """搜 DuckDuckGo HTML 页面，提取链接 + 标题 + 描述"""
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            resp = self.client.get(url)
            resp.raise_for_status()
        except Exception as e:
            log.warning(f"  ⚠️ 搜索失败: {e}")
            return []
        
        html = resp.text
        
        # 提取结果
        leads = []
        # 匹配 DuckDuckGo 的结果格式
        # <a rel="nofollow" href="...">title</a>
        # <a class="result__a" href="...">
        blocks = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )
        
        seen_urls = set()
        for url, title_html in blocks:
            # clean title
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            
            # 只保留 LinkedIn 链接
            if 'linkedin.com' not in url.lower():
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
            # 提取公司/人名
            company = self._extract_company(title, url)
            
            leads.append({
                "url": url,
                "title": title,
                "company": company,
                "query": query,
            })
            
            if len(leads) >= max_results:
                break
        
        return leads
    
    def _extract_company(self, title: str, url: str) -> str:
        """从 LinkedIn URL 和标题提取公司名"""
        # 公司页: /company/name
        m = re.search(r'/company/([^/?]+)', url)
        if m:
            return m.group(1).replace('-', ' ').title()
        # 个人页: 从标题末尾找公司
        m = re.search(r'at\s+([A-Z][A-Za-z0-9\s&.]+)', title)
        if m:
            return m.group(1).strip()
        return ""


class CompanyCrawler:
    """爬公司官网找联系信息"""
    
    def __init__(self):
        self.client = httpx.Client(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=15.0,
            follow_redirects=True,
        )
    
    def find_website(self, company: str) -> Optional[str]:
        """搜公司官网"""
        query = f'"{company}" official website'
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            resp = self.client.get(url)
            html = resp.text
            # 找第一个非linkedin的链接
            blocks = re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]+)"',
                html
            )
            for link in blocks:
                if ('linkedin.com' not in link.lower() 
                    and 'facebook.com' not in link.lower()
                    and 'twitter.com' not in link.lower()):
                    return link.split('?')[0]  # 去掉跟踪参数
        except Exception:
            pass
        return None
    
    def crawl_contact_page(self, website: str) -> dict:
        """爬网站找联系方式"""
        emails = set()
        phones = set()
        
        # 要爬的页面
        pages = [
            website.rstrip('/'),
            f"{website.rstrip('/')}/contact",
            f"{website.rstrip('/')}/contact-us",
            f"{website.rstrip('/')}/about",
            f"{website.rstrip('/')}/about-us",
        ]
        
        email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        phone_pattern = re.compile(
            r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
        )
        
        for page in pages:
            try:
                resp = self.client.get(page)
                text = resp.text
                
                # 找邮箱
                for m in email_pattern.finditer(text):
                    email = m.group().lower()
                    # 过滤掉图片/base64/示例邮箱
                    if any(x in email for x in ['example', 'test@', '@domain', 
                                                  '.png', '.jpg', '.gif', 'base64']):
                        continue
                    emails.add(email)
                
                # 找电话
                for m in phone_pattern.finditer(text):
                    phone = m.group().strip()
                    if len(phone) >= 7:  # 至少7位才算有效电话
                        phones.add(phone)
                        
            except Exception:
                continue
        
        return {
            "emails": sorted(emails)[:10],
            "phones": sorted(phones)[:5],
        }


# ====================================================================
# 主流程
# ====================================================================

class LinkedInXrayPipeline:
    def __init__(self):
        self.searcher = DuckDuckGoSearch()
        self.crawler = CompanyCrawler()
        self.leads: list[LinkedInLead] = []
    
    def run(self, config: Optional[SearchConfig] = None) -> list[LinkedInLead]:
        cfg = config or SearchConfig()
        all_leads: list[LinkedInLead] = []
        
        print(f"{'='*56}")
        print(f"  🔍 LinkedIn X-ray Search — 免登录爬取")
        print(f"  查询数: {len(cfg.queries)}  ×  每查询: {cfg.max_results_per_query}")
        print(f"{'='*56}\n")
        
        for i, query in enumerate(cfg.queries, 1):
            print(f"\n[{i}/{len(cfg.queries)}] 🔎 {query[:60]}...")
            
            results = self.searcher.search(query, cfg.max_results_per_query)
            print(f"   找到 {len(results)} 个 LinkedIn 链接")
            
            for r in results:
                lead = LinkedInLead(
                    name=r["title"].split(" - ")[0] if " - " in r["title"] else r["title"].split(" | ")[0],
                    title=r["title"],
                    company=r["company"],
                    linkedin_url=r["url"],
                    source_query=query[:40],
                )
                
                # 如果有公司名，找官网和邮箱
                if lead.company:
                    print(f"   📡 {lead.name[:25]:25s} @ {lead.company[:25]:25s} ... ", end="")
                    website = self.crawler.find_website(lead.company)
                    if website:
                        lead.website = website
                        print(f"🌐", end="")
                        contact = self.crawler.crawl_contact_page(website)
                        if contact["emails"]:
                            lead.email = contact["emails"][0]
                            print(f" 📧", end="")
                        if contact["phones"]:
                            lead.phone = contact["phones"][0]
                            # 南非/肯尼亚号码 = WhatsApp 可用
                            if any(lead.phone.startswith(cc) for cc in ['+27', '+234', '+254', '+263']):
                                lead.whatsapp = lead.phone
                                print(f" 💬", end="")
                        print()
                    else:
                        print(f"❌ 无官网")
                
                all_leads.append(lead)
            
            time.sleep(1)  # 礼貌延迟
        
        self.leads = all_leads
        return all_leads
    
    def export_json(self, path: Optional[str] = None) -> str:
        """导出为 JSON（与 buyer-development 管道兼容）"""
        output = {
            "pipeline": "linkedin-xray",
            "generated_at": datetime.now().isoformat(),
            "total": len(self.leads),
            "with_company": sum(1 for l in self.leads if l.company),
            "with_website": sum(1 for l in self.leads if l.website),
            "with_email": sum(1 for l in self.leads if l.email),
            "with_whatsapp": sum(1 for l in self.leads if l.whatsapp),
            "leads": [asdict(l) for l in self.leads],
        }
        
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
            log.info(f"\n📁 已保存: {path}")
        
        return json.dumps(output, indent=2, ensure_ascii=False)


# ====================================================================
# 入口
# ====================================================================

def main():
    pipeline = LinkedInXrayPipeline()
    leads = pipeline.run()
    
    print(f"\n{'='*56}")
    print(f"  爬取完成!")
    print(f"  总计: {len(leads)} 个 LinkedIn 线索")
    companies = sum(1 for l in leads if l.company)
    websites = sum(1 for l in leads if l.website)
    emails = sum(1 for l in leads if l.email)
    phones = sum(1 for l in leads if l.phone)
    print(f"  有公司名: {companies}  |  有官网: {websites}  |  有邮箱: {emails}  |  有电话: {phones}")
    print(f"{'='*56}\n")
    
    # 保存
    out_dir = Path.home() / "AppData" / "Local" / "hermes" / "memories" / "buyer-development"
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"linkedin_xray_leads_{datetime.now().strftime('%Y-%m-%d')}.json"
    out_path = out_dir / fname
    pipeline.export_json(str(out_path))
    
    # 打印有邮箱的高价值客户
    print(f"\n💰 高价值客户（有邮箱/电话）:")
    for l in leads:
        if l.email or l.whatsapp:
            print(f"  {l.name[:20]:20s} | {l.company[:20]:20s} | {l.email or '':25s} | {l.phone or '':15s} {'💬' if l.whatsapp else ''}")


if __name__ == "__main__":
    main()