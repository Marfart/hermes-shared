# Windows YAML Path Escaping for MCP Server Args

## Problem

Adding a Windows path (e.g. `C:\Users\Admin\...`) to `mcp_servers` config as a YAML **double-quoted string** causes a parse crash:

```yaml
# ❌ CRASHES — YAML treats \U as unicode escape
mcp_servers:
  sqlite:
    command: python
    args:
      - "C:\Users\Admin\scripts\server.py"
```

YAML double-quoted strings interpret `\U` as the start of an 8-hex-digit unicode escape (`\Uxxxxxxxx`). Since `\Users` is not valid hex, the scanner throws `ScannerError: expected escape sequence of 8 hexadecimal numbers, but found 's'`.

The entire `config.yaml` fails to load — Hermes falls back to empty defaults, and MCP is silently missing.

## Solutions

### ✅ Solution 1: Forward slashes (recommended)

Windows accepts forward slashes in most APIs. YAML treats them as plain text:

```yaml
mcp_servers:
  sqlite:
    command: python
    args:
      - 'C:/Users/Admin/scripts/mcp_sqlite_server.py'
      - --db
      - 'C:/Users/Admin/scripts/bliiot.db'
```

### ✅ Solution 2: Single quotes (also avoids escape processing)

YAML single-quoted strings do NOT process escape sequences:

```yaml
mcp_servers:
  sqlite:
    command: python
    args:
      - 'C:\Users\Admin\scripts\server.py'
```

### ✅ Solution 3: Double backslashes

Only works inside double-quoted strings — easy to forget and fragile:

```yaml
mcp_servers:
  sqlite:
    command: python
    args:
      - "C:\\Users\\Admin\\scripts\\server.py"
```

## Verification

After editing, verify the config is valid YAML:

```bash
python -c "import yaml; yaml.safe_load(open(r'C:\Users\Admin\AppData\Local\hermes\config.yaml'))"
```

If it doesn't error, the config will load correctly.

## Reload

After fixing the config:

```bash
# Check MCP status
hermes mcp list

# If config was empty before, restart Hermes (or use /reload-mcp in session)
```

## Why This Happens

- **YAML double-quoted** strings (`"..."`) parse C-style escape sequences: `\n`, `\t`, `\uXXXX`, `\UXXXXXXXX`
- `\U` expects exactly 8 hex digits — `\Users` has `s` which is not hex, causing the scanner error
- **Single-quoted** strings (`'...'`) treat every character literally — no escapes at all
- **Unquoted** scalars are also safe, but can cause issues if the value contains `:`, `#`, or leading special chars
- Forward slashes work on Windows at the Win32 API level (most file operations accept both `/` and `\`)
