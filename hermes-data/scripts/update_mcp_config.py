#!/usr/bin/env python3
"""Update MCP config to point to the real database."""
import yaml

config_path = r"C:\Users\Admin\AppData\Local\hermes\config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# Update the args to include --db pointing to the real database
config["mcp_servers"]["sqlite"]["args"] = [
    r"C:\Users\Admin\AppData\Local\hermes\scripts\mcp_sqlite_server.py",
    "--db",
    r"C:\Users\Admin\AppData\Local\hermes\scripts\bliiot.db",
]

with open(config_path, "w", encoding="utf-8") as f:
    yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)

print("✅ config.yaml 已更新，MCP 指向 bliiot.db")
