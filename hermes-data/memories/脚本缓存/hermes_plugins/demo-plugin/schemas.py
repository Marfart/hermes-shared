# schemas.py — Hermes Plugin JSON Schemas

SYS_INFO_SCHEMA = {
    "name": "sys_info",
    "description": "Get system information: CPU, RAM, OS version, hostname",
    "parameters": {
        "type": "object",
        "properties": {
            "detail": {
                "type": "string",
                "description": "Detail level: 'basic' (default), 'full'",
                "enum": ["basic", "full"],
            }
        },
    },
}

SYS_DISK_USAGE_SCHEMA = {
    "name": "sys_disk_usage",
    "description": "Get disk usage statistics for all mounted drives",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Specific path to check (default: all drives on Windows, / on Linux)",
            }
        },
    },
}

SYS_UPTIME_SCHEMA = {
    "name": "sys_uptime",
    "description": "Get system uptime information",
    "parameters": {
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "description": "Output format: 'human' (default), 'seconds', 'dict'",
                "enum": ["human", "seconds", "dict"],
            }
        },
    },
}