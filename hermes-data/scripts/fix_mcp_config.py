#!/usr/bin/env python3
"""Add mcp_servers.sqlite config back to config.yaml, pointing to bliiot.db"""
import yaml

config_path = r"C:\Users\Admin\AppData\Local\hermes\config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find where to insert mcp_servers (after model section)
insert_pos = None
for i, line in enumerate(lines):
    if line.strip().startswith("providers:"):
        insert_pos = i
        break

if insert_pos is None:
    print("Could not find insert position")
else:
    mcp_config = """mcp_servers:
  sqlite:
    command: python
    args:
    - \"C:\\Users\\Admin\\AppData\\Local\\hermes\\scripts\\mcp_sqlite_server.py\"
    - --db
    - \"C:\\Users\\Admin\\AppData\\Local\\hermes\\scripts\\bliiot.db\"
"""
    # Insert before providers: line
    new_lines = lines[:insert_pos] + [mcp_config] + lines[insert_pos:]
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("✅ mcp_servers.sqlite added back, pointing to bliiot.db")
    
    # Verify
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "mcp_servers" in content and "bliiot.db" in content:
        print("✅ Verified: config contains mcp_servers with bliiot.db")
