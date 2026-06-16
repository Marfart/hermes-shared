#!/usr/bin/env python3
import yaml, os, json

home = os.environ.get("USERPROFILE", "C:/Users/Admin").replace("\\", "/")
scripts_dir = home + "/AppData/Local/hermes/scripts"

cfg_path = os.path.join(os.environ.get("LOCALAPPDATA", home + "/AppData/Local"), "hermes", "config.yaml")
cfg_path = cfg_path.replace("\\", "/")

with open(cfg_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

insert_pos = None
for i, line in enumerate(lines):
    if line.strip().startswith("providers:"):
        insert_pos = i
        break

if insert_pos is None:
    print("Error: Could not find providers: line")
else:
    mcp_config = (
        "mcp_servers:\n"
        "  sqlite:\n"
        "    command: python\n"
        "    args:\n"
        "    - '" + scripts_dir + "/mcp_sqlite_server.py'\n"
        "    - --db\n"
        "    - '" + scripts_dir + "/bliiot.db'\n"
    )
    new_lines = lines[:insert_pos] + [mcp_config] + lines[insert_pos:]
    
    with open(cfg_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    
    print("SUCCESS" if "mcp_servers" in cfg else "FAILED")
    print(json.dumps(cfg.get("mcp_servers", {}), indent=2))
