#!/usr/bin/env python3
"""Wiki Lint维护 - no_agent 版本
检查frontmatter格式 + 孤儿页面 + 损坏链接，只在有问题时输出"""
import os, re, sys
from datetime import datetime

WIKI_DIR = os.path.expanduser("~/Desktop/Working/wiki")

def check_frontmatter(filepath):
    """检查pages/下的md文件是否有正确frontmatter"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    issues = []
    
    # Check frontmatter exists
    if not content.startswith("---"):
        issues.append("缺少 frontmatter (不以 --- 开头)")
        return issues
    
    # Extract frontmatter
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        issues.append("frontmatter 未正确关闭")
        return issues
    
    fm = m.group(1)
    
    # Check required fields
    if not re.search(r'^title:', fm, re.MULTILINE):
        issues.append("缺少 title 字段")
    if not re.search(r'^date:', fm, re.MULTILINE):
        issues.append("缺少 date 字段")
    if not re.search(r'^tags?:', fm, re.MULTILINE):
        issues.append("缺少 tags 字段")
    
    return issues

def find_orphans():
    """找出不被任何页面引用的页面"""
    pages_dir = os.path.join(WIKI_DIR, "pages")
    if not os.path.isdir(pages_dir):
        return ["pages/ 目录不存在"]
    
    all_files = [f for f in os.listdir(pages_dir) if f.endswith(".md")]
    if not all_files:
        return ["pages/ 下没有md文件"]
    
    # Build filename -> path mapping
    file_map = {f: os.path.join(pages_dir, f) for f in all_files}
    
    # Build reference index
    referenced = set()
    for fname, fpath in file_map.items():
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        # [[links]]
        for m in re.finditer(r'\[\[(.+?)\]\]', content):
            linked = m.group(1)
            # Find matching file
            for f2 in all_files:
                if f2.replace(".md", "") == linked or linked in f2:
                    referenced.add(f2)
    
    orphans = [f for f in all_files if f not in referenced and f != "index.md"]
    return orphans

def find_bad_links():
    """查找 [[broken links]]"""
    pages_dir = os.path.join(WIKI_DIR, "pages")
    if not os.path.isdir(pages_dir):
        return {}
    
    all_files = set(os.listdir(pages_dir))
    bad = {}
    
    for f in os.listdir(pages_dir):
        if not f.endswith(".md"):
            continue
        fpath = os.path.join(pages_dir, f)
        with open(fpath, "r", encoding="utf-8") as fh:
            content = fh.read()
        
        for m in re.finditer(r'\[\[(.+?)\]\]', content):
            linked = m.group(1)
            # Check if any .md matches
            matched = any(linked == mf.replace(".md", "") or linked in mf for mf in all_files if mf.endswith(".md"))
            if not matched:
                if f not in bad:
                    bad[f] = []
                bad[f].append(linked)
    
    return bad

def main():
    if not os.path.isdir(WIKI_DIR):
        return  # No wiki yet, silent
    
    pages_dir = os.path.join(WIKI_DIR, "pages")
    if not os.path.isdir(pages_dir):
        return  # No pages dir, silent
    
    report = []
    
    # 1. Check frontmatter
    fm_issues = {}
    for f in sorted(os.listdir(pages_dir)):
        if f.endswith(".md"):
            fpath = os.path.join(pages_dir, f)
            issues = check_frontmatter(fpath)
            if issues:
                fm_issues[f] = issues
    
    if fm_issues:
        report.append(f"⚠️ {len(fm_issues)} 个页面frontmatter有问题:")
        for f, issues in sorted(fm_issues.items()):
            report.append(f"  • {f}: {'; '.join(issues)}")
    
    # 2. Find orphans
    orphans = find_orphans()
    if orphans and not isinstance(orphans[0], str) or (isinstance(orphans[0], str) and "不存在" not in orphans[0]):
        report.append(f"\n📄 孤儿页面 ({len(orphans)} 个未被引用):")
        for f in orphans[:10]:
            report.append(f"  • {f}")
        if len(orphans) > 10:
            report.append(f"  ... 还有 {len(orphans)-10} 个")
    
    # 3. Find broken links
    bad = find_bad_links()
    if bad:
        total = sum(len(v) for v in bad.values())
        report.append(f"\n🔗 {total} 个断链分布:")
        for f, links in sorted(bad.items()):
            report.append(f"  • {f}: {', '.join(links[:3])}")
            if len(links) > 3:
                report.append(f"    ... 还有 {len(links)-3} 个")
    
    if report:
        print(f"📋 Wiki Lint 报告 ({datetime.now().strftime('%Y-%m-%d')})")
        for line in report:
            print(line)
        print("\n请手动修复以上问题")

if __name__ == "__main__":
    main()