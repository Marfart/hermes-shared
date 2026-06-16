#!/usr/bin/env python3
"""添加 Playwright MCP 到 Hermes 配置"""
import yaml
from pathlib import Path

cfg_path = Path.home() / "AppData" / "Local" / "hermes" / "config.yaml"
cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

# 添加 playwright MCP
if "playwright" not in cfg.get("mcp_servers", {}):
    cfg.setdefault("mcp_servers", {})["playwright"] = {
        "command": "npx",
        "args": ["-y", "@playwright/mcp@latest"],
        "enabled": True,
    }
    cfg_path.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    print("✅ Playwright MCP 已添加到配置")
else:
    print("ℹ️ Playwright MCP 已存在")
