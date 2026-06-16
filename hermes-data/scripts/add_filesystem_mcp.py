#!/usr/bin/env python3
"""Add filesystem MCP server to config.yaml"""
import sys
sys.path.insert(0, r'C:\Users\Admin\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages')

import yaml

path = r'C:\Users\Admin\AppData\Local\hermes\config.yaml'
with open(path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

cfg['mcp_servers']['filesystem'] = {
    'command': 'npx',
    'args': ['-y', '@modelcontextprotocol/server-filesystem', 'C:/Users/Admin/Desktop/Working'],
    'timeout': 60,
}

with open(path, 'w', encoding='utf-8') as f:
    yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)

print('Done')
