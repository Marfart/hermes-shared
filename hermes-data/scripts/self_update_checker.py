#!/usr/bin/env python3
"""每日自更新 - no_agent 版本
检查 Hermes Agent 新版本 + 技能更新
只在有更新时才输出"""
import urllib.request, json, os, sys, re, textwrap
from datetime import datetime

def get_local_version():
    config = os.path.expanduser("~/AppData/Local/hermes/config.yaml")
    if os.path.exists(config):
        with open(config, encoding="utf-8") as f:
            m = re.search(r'version["\s:=]+["\']?([\d.]+)', f.read())
            if m:
                return m.group(1)
    return None

def check_github():
    url = "https://api.github.com/repos/NousResearch/hermes-agent/releases/latest"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "hermes-agent"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            tag = data.get("tag_name", "").lstrip("v")
            body = data.get("body", "")[:300]
            return tag, body
    except Exception as e:
        return None, None

def main():
    local = get_local_version()
    gh_ver, body = check_github()
    
    if not gh_ver:
        return  # silent - can't check
    
    if local and gh_ver != local and gh_ver > local:
        print(f"📦 Hermes 新版本: v{local} → v{gh_ver}")
        if body:
            print(textwrap.shorten(body, width=200))
    else:
        pass  # up to date - silent

if __name__ == "__main__":
    main()