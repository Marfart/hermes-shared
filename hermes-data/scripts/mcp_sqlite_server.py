#!/usr/bin/env python3
"""
MCP SQLite Server — let Hermes query SQLite databases via MCP.
Usage: python mcp_sqlite_server.py [--db /path/to/database.db]
Defaults to demo.db in the same directory.
"""

import json
import sqlite3
import sys
import os
import argparse
from pathlib import Path
from typing import Any

# ── Parse args ──────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--db", default=None, help="Path to SQLite database")
args, _ = parser.parse_known_args()

DB_PATH = args.db or os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo.db")

# ── MCP over stdio (lightweight, no asyncio dependency) ─────
def mcp_send(msg: dict):
    """Send a JSON-RPC message to the MCP client over stdout."""
    line = json.dumps(msg, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()

def mcp_read() -> dict | None:
    """Read a JSON-RPC message from stdin."""
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line.strip())

def db_connect():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def handle_request(msg: dict) -> dict:
    """Handle an MCP JSON-RPC request."""
    method = msg.get("method", "")
    req_id = msg.get("id")
    params = msg.get("params", {})

    if method == "initialize":
        capabilities = {
            "tools": {
                "listChanged": False,
            }
        }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": capabilities,
                "serverInfo": {"name": "sqlite-mcp", "version": "1.0.0"},
            },
        }

    elif method == "tools/list":
        tools = [
            {
                "name": "query",
                "description": "Run a SELECT query against the SQLite database. Read-only.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL SELECT query to execute",
                        }
                    },
                    "required": ["sql"],
                },
            },
            {
                "name": "tables",
                "description": "List all tables in the database with their schema info.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "describe",
                "description": "Show column info for a specific table.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table": {
                            "type": "string",
                            "description": "Table name",
                        }
                    },
                    "required": ["table"],
                },
            },
        ]
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

    elif method == "resources/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": []}}

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            conn = db_connect()
            if tool_name == "query":
                sql = arguments.get("sql", "")
                sql_upper = sql.strip().upper()
                # Safety: only allow SELECT / PRAGMA / EXPLAIN
                if not any(sql_upper.startswith(kw) for kw in ["SELECT", "PRAGMA", "EXPLAIN", "WITH"]):
                    raise ValueError("Only SELECT, PRAGMA, EXPLAIN, and WITH queries are allowed.")
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                result = {"columns": columns, "rows": rows, "row_count": len(rows)}
            elif tool_name == "tables":
                cursor = conn.execute(
                    "SELECT name, type, sql FROM sqlite_master WHERE type='table' ORDER BY name"
                )
                tables = [dict(row) for row in cursor.fetchall()]
                result = {"tables": tables}
            elif tool_name == "describe":
                table = arguments.get("table", "")
                cursor = conn.execute(f"PRAGMA table_info('{table}')")
                columns = [dict(row) for row in cursor.fetchall()]
                result = {"table": table, "columns": columns}
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            conn.close()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                },
            }

    elif method == "notifications/initialized":
        return None  # No response needed

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"content": [{"type": "text", "text": f"Unknown method: {method}"}]},
        }


# ── Create demo database if not exists ─────────────────────
if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            model TEXT,
            category TEXT,
            price REAL,
            stock INTEGER DEFAULT 0,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            company TEXT,
            email TEXT,
            phone TEXT,
            region TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Insert demo BLIIOT-style products
        INSERT INTO products (name, model, category, price, stock, description) VALUES
            ('工业以太网IO模块', 'R6-IO-ETH', 'IO模块', 680.00, 150, '8路数字量输入/8路数字量输出，Modbus TCP协议'),
            ('远程IO数据采集模块', 'R6-DA-232', 'IO模块', 520.00, 200, 'RS232通讯，模拟量采集模块'),
            ('无线温度传感器', 'R6-TEMP-WL', '传感器', 350.00, 300, '无线传输，-40~85°C测温范围'),
            ('Modbus网关', 'R6-GW-MB', '网关', 890.00, 80, 'Modbus RTU转Modbus TCP网关'),
            ('4G远程终端单元', 'R6-RTU-4G', 'RTU', 1280.00, 45, '4G全网通，支持MQTT/HTTP'),
            ('工业路由器', 'R6-RTR-4G', '路由器', 960.00, 60, '4G工业路由器，双SIM卡备份');

        INSERT INTO customers (name, company, email, region) VALUES
            ('张三', '深圳智造科技有限公司', 'zhang@zhizao.com', '华南'),
            ('李四', '上海工业自动化研究所', 'li@auto-sh.com', '华东'),
            ('王五', '北京智能控制有限公司', 'wang@bjiot.com', '华北');

        INSERT INTO orders (customer_id, product_id, quantity, total_price, status) VALUES
            (1, 1, 10, 6800.00, 'completed'),
            (1, 4, 5, 4450.00, 'shipped'),
            (2, 3, 20, 7000.00, 'pending'),
            (3, 5, 3, 3840.00, 'completed'),
            (2, 6, 8, 7680.00, 'processing');
    """)
    conn.commit()
    conn.close()
    print(f"[MCP SQLite] Created demo database: {DB_PATH}", file=sys.stderr)

# ── Main loop ──────────────────────────────────────────────
print(f"[MCP SQLite] Server ready — DB: {DB_PATH}", file=sys.stderr)

while True:
    try:
        msg = mcp_read()
        if msg is None:
            break
        method = msg.get("method", "")
        # Skip notifications (no id)
        if msg.get("id") is None and method != "notifications/initialized":
            continue
        resp = handle_request(msg)
        if resp is not None:
            mcp_send(resp)
    except json.JSONDecodeError:
        continue
    except EOFError:
        break
    except Exception as e:
        print(f"[MCP SQLite] Error: {e}", file=sys.stderr)
        break
