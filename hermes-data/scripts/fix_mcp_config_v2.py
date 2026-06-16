#!/usr/bin/env python3
"""Add mcp_servers.sqlite config back - using single quotes to avoid \U escapes"""
import yaml

config_path = r"C:\Users\Admin\AppData\Local\hermes\config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find where to insert mcp_servers (after model section, before providers:)
insert_pos = None
for i, line in enumerate(lines):
    if line.strip().startswith("providers:"):
        insert_pos = i
        break

if insert_pos is None:
    print("Error: Could not find 'providers:' line")
else:
    # Use single quotes in YAML to avoid \U escaping issue
    # Or better: use forward slashes which Windows also accepts
    scripts_path = "C:/Users/Admin/AppData/Local/hermes/scripts"
    
    mcp_config = f"""mcp_servers:
  sqlite:
    command: python
    args:
    - '{scripts_path}/mcp_sqlite_server.py'
    - --db
    - '{scripts_path}/bliiot.db'
"""
    new_lines = lines[:insert_pos] + [mcp_config] + lines[insert_pos:]
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    # Verify with YAML parser
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    
    if "mcp_servers" in cfg:
        print(f"✅ mcp_servers added successfully!")
        print(f"   Command: {cfg['mcp_servers']['sqlite']['command']}")
        print(f"   Args: {cfg['mcp_servers']['sqlite']['args']}")
    else:
        print("❌ Something went wrong - mcp_servers not in parsed config")
