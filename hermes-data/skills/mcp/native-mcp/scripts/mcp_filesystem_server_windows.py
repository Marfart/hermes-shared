#!/usr/bin/env python3
"""Minimal filesystem MCP server for Hermes on Windows.
Provides: list_directory, read_file, write_file, search_files
"""
import json, sys, os, datetime, stat

ALLOWED_DIRS = [
    r'C:\Users\Admin\Desktop\Working',
    r'C:\Users\Admin\Documents',
]

def _safe_path(path: str) -> str:
    abs_path = os.path.abspath(os.path.normpath(path))
    for d in ALLOWED_DIRS:
        d_abs = os.path.abspath(d)
        if abs_path == d_abs or abs_path.startswith(d_abs + os.sep):
            return abs_path
    raise PermissionError(f"Access denied: {path} is outside allowed directories")

def handle(method: str, params: dict) -> dict:
    if method == "list_directory":
        path = _safe_path(params["path"])
        entries = []
        for name in os.listdir(path):
            full = os.path.join(path, name)
            st = os.stat(full)
            entries.append({
                "name": name,
                "type": "directory" if stat.S_ISDIR(st.st_mode) else "file",
                "size": st.st_size,
                "modified": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(),
            })
        entries.sort(key=lambda e: (-(1 if e["type"] == "directory" else 0), e["name"].lower()))
        return {"entries": entries}

    elif method == "read_file":
        path = _safe_path(params["path"])
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"content": content, "size": len(content)}

    elif method == "write_file":
        path = _safe_path(params["path"])
        with open(path, 'w', encoding='utf-8') as f:
            f.write(params["content"])
        return {"success": True, "size": len(params["content"])}

    elif method == "search_files":
        root = _safe_path(params.get("path", ALLOWED_DIRS[0]))
        pattern = params.get("pattern", "").lower()
        results = []
        for dirpath, dirnames, filenames in os.walk(root):
            for fn in filenames:
                if pattern in fn.lower():
                    full = os.path.join(dirpath, fn)
                    results.append(full)
            if len(results) >= 100:
                break
        return {"results": results}

    elif method == "get_file_info":
        path = _safe_path(params["path"])
        st = os.stat(path)
        return {
            "name": os.path.basename(path),
            "type": "directory" if stat.S_ISDIR(st.st_mode) else "file",
            "size": st.st_size,
            "modified": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(),
            "created": datetime.datetime.fromtimestamp(st.st_ctime).isoformat(),
        }

    raise ValueError(f"Unknown method: {method}")

TOOLS = [
    {
        "name": "list_directory",
        "description": "List files and directories in a path. Allowed: Working/, Documents/",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "read_file",
        "description": "Read a file's contents",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files by pattern in a directory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Root directory"},
                "pattern": {"type": "string", "description": "Filename pattern to match"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "get_file_info",
        "description": "Get file metadata (size, type, dates)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path"}
            },
            "required": ["path"]
        }
    },
]

def send(msg: dict):
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def recv() -> dict | None:
    line = sys.stdin.readline()
    return json.loads(line.strip()) if line else None

# Initialize: wait for initialize request
while True:
    msg = recv()
    if not msg:
        break
    rid = msg.get("id")
    method = msg.get("method", "")

    if method == "initialize":
        send({
            "jsonrpc": "2.0", "id": rid,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "windows-filesystem", "version": "1.0.0"}
            }
        })
    elif method == "notifications/initialized":
        pass  # no response
    elif method == "tools/list":
        send({
            "jsonrpc": "2.0", "id": rid,
            "result": {"tools": TOOLS}
        })
    elif method == "tools/call":
        try:
            tool_name = msg["params"]["name"]
            arguments = msg["params"].get("arguments", {})
            result = handle(tool_name, arguments)
            send({
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2, ensure_ascii=False)}]
                }
            })
        except Exception as e:
            send({
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": json.dumps({"error": str(e)})}]
                }
            })
    else:
        send({
            "jsonrpc": "2.0", "id": rid,
            "result": {"content": [{"type": "text", "text": json.dumps({"error": f"Unknown method: {method}"})}]}
        })
