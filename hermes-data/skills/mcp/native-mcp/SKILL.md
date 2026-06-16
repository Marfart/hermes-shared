---
name: native-mcp
description: "MCP client: connect servers, register tools (stdio/HTTP)."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [MCP, Tools, Integrations]
    related_skills: [mcporter]
---

# Native MCP Client

Hermes Agent has a built-in MCP client that connects to MCP servers at startup, discovers their tools, and makes them available as first-class tools the agent can call directly. No bridge CLI needed -- tools from MCP servers appear alongside built-in tools like `terminal`, `read_file`, etc.

## When to Use

Use this whenever you want to:
- Connect to MCP servers and use their tools from within Hermes Agent
- Add external capabilities (filesystem access, GitHub, databases, APIs) via MCP
- Run local stdio-based MCP servers (npx, uvx, or any command)
- Connect to remote HTTP/StreamableHTTP MCP servers
- Have MCP tools auto-discovered and available in every conversation

For ad-hoc, one-off MCP tool calls from the terminal without configuring anything, see the `mcporter` skill instead.

## Prerequisites

- **mcp Python package** -- optional dependency; install with `pip install mcp`. If not installed, MCP support is silently disabled.
- **Node.js** -- required for `npx`-based MCP servers (most community servers)
- **uv** -- required for `uvx`-based MCP servers (Python-based servers)

Install the MCP SDK:

```bash
pip install mcp
# or, if using uv:
uv pip install mcp
```

## Quick Start

Add MCP servers to `~/.hermes/config.yaml` under the `mcp_servers` key:

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

Restart Hermes Agent. On startup it will:
1. Connect to the server
2. Discover available tools
3. Register them with the prefix `mcp_time_*`
4. Inject them into all platform toolsets

You can then use the tools naturally -- just ask the agent to get the current time.

## Configuration Reference

Each entry under `mcp_servers` is a server name mapped to its config. There are two transport types: **stdio** (command-based) and **HTTP** (url-based).

### Stdio Transport (command + args)

```yaml
mcp_servers:
  server_name:
    command: "npx"             # (required) executable to run
    args: ["-y", "pkg-name"]   # (optional) command arguments, default: []
    env:                       # (optional) environment variables for the subprocess
      SOME_API_KEY: "value"
    timeout: 120               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### HTTP Transport (url)

```yaml
mcp_servers:
  server_name:
    url: "https://my-server.example.com/mcp"   # (required) server URL
    headers:                                     # (optional) HTTP headers
      Authorization: "Bearer sk-..."
    timeout: 180               # (optional) per-tool-call timeout in seconds, default: 120
    connect_timeout: 60        # (optional) initial connection timeout in seconds, default: 60
```

### All Config Options

| Option            | Type   | Default | Description                                       |
|-------------------|--------|---------|---------------------------------------------------|
| `command`         | string | --      | Executable to run (stdio transport, required)     |
| `args`            | list   | `[]`    | Arguments passed to the command                   |
| `env`             | dict   | `{}`    | Extra environment variables for the subprocess    |
| `url`             | string | --      | Server URL (HTTP transport, required)             |
| `headers`         | dict   | `{}`    | HTTP headers sent with every request              |
| `timeout`         | int    | `120`   | Per-tool-call timeout in seconds                  |
| `connect_timeout` | int    | `60`    | Timeout for initial connection and discovery      |

Note: A server config must have either `command` (stdio) or `url` (HTTP), not both.

## How It Works

### Startup Discovery

When Hermes Agent starts, `discover_mcp_tools()` is called during tool initialization:

1. Reads `mcp_servers` from `~/.hermes/config.yaml`
2. For each server, spawns a connection in a dedicated background event loop
3. Initializes the MCP session and calls `list_tools()` to discover available tools
4. Registers each tool in the Hermes tool registry

### Tool Naming Convention

MCP tools are registered with the naming pattern:

```
mcp_{server_name}_{tool_name}
```

Hyphens and dots in names are replaced with underscores for LLM API compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp_filesystem_read_file`
- Server `github`, tool `list-issues` → `mcp_github_list_issues`
- Server `my-api`, tool `fetch.data` → `mcp_my_api_fetch_data`

### Auto-Injection

After discovery, MCP tools are automatically injected into all `hermes-*` platform toolsets (CLI, Discord, Telegram, etc.). This means MCP tools are available in every conversation without any additional configuration.

### Connection Lifecycle

- Each server runs as a long-lived asyncio Task in a background daemon thread
- Connections persist for the lifetime of the agent process
- If a connection drops, automatic reconnection with exponential backoff kicks in (up to 5 retries, max 60s backoff)
- On agent shutdown, all connections are gracefully closed

### Idempotency

`discover_mcp_tools()` is idempotent -- calling it multiple times only connects to servers that aren't already connected. Failed servers are retried on subsequent calls.

## Transport Types

### Stdio Transport

The most common transport. Hermes launches the MCP server as a subprocess and communicates over stdin/stdout.

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"]
```

The subprocess inherits a **filtered** environment (see Security section below) plus any variables you specify in `env`.

### HTTP / StreamableHTTP Transport

For remote or shared MCP servers. Requires the `mcp` package to include HTTP client support (`mcp.client.streamable_http`).

```yaml
mcp_servers:
  remote_api:
    url: "https://mcp.example.com/mcp"
    headers:
      Authorization: "Bearer sk-..."
```

If HTTP support is not available in your installed `mcp` version, the server will fail with an ImportError and other servers will continue normally.

## Custom Python MCP Servers

When an npm-based MCP server package returns a 404 or doesn't exist, you can write a custom MCP server in Python using the `mcp` Python package. This is useful for databases, internal APIs, or any service that doesn't have a published MCP server.

### Stdio Transport Protocol (JSON-RPC over stdin/stdout)

The Hermes MCP client communicates with servers over stdin/stdout using JSON-RPC 2.0. A minimal Python MCP server sends/receives JSON lines:

- **Initialize**: Respond to `initialize` with protocol version and capabilities
- **tools/list**: Return the list of available tools with their input schemas
- **tools/call**: Execute the tool and return results as text content
- **notifications/initialized**: No response needed (ack only)

### Template Structure

```python
#!/usr/bin/env python3
import json, sys

def send(msg: dict):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def recv() -> dict | None:
    line = sys.stdin.readline()
    return json.loads(line.strip()) if line else None

def handle(msg: dict) -> dict | None:
    method = msg.get("method", "")
    rid = msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "my-server", "version": "1.0.0"},
        }}
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [...]}}
    elif method == "tools/call":
        result = do_work(msg["params"])
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps(result)}]
        }}
    elif method == "notifications/initialized":
        return None

while True:
    msg = recv()
    if not msg: break
    resp = handle(msg)
    if resp: send(resp)
```

### Config in Hermes

```yaml
mcp_servers:
  sqlite:
    command: "python"
    args: ["C:\\path\\to\\mcp_sqlite_server.py", "--db", "C:\\path\\to\\data.db"]
```

The server process inherits a filtered shell environment. Tools appear as `mcp_sqlite_query`, `mcp_sqlite_tables`, etc.

### Reference Implementation

See `scripts/mcp_sqlite_server.py` for a working SQLite MCP server with read-only query enforcement. See `scripts/mcp_filesystem_server_windows.py` for a custom filesystem server with directory whitelist security (faster and more reliable than the npx counterpart on Windows).

## Security

### Environment Variable Filtering

For stdio servers, Hermes does NOT pass your full shell environment to MCP subprocesses. Only safe baseline variables are inherited:

- `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`
- Any `XDG_*` variables

All other environment variables (API keys, tokens, secrets) are excluded unless you explicitly add them via the `env` config key. This prevents accidental credential leakage to untrusted MCP servers.

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      # Only this token is passed to the subprocess
      GITHUB_PERSONAL_ACCESS_TOKEN: "***PAT_PREFIX***_..."
```

### Credential Stripping in Error Messages

If an MCP tool call fails, any credential-like patterns in the error message are automatically redacted before being shown to the LLM. This covers:

- GitHub PATs (`***PAT_PREFIX***_XXXXXXXXXXXX`)
- OpenAI-style keys (`sk-...`)
- Bearer tokens
- Generic `token=`, `key=`, `API_KEY=`, `password=`, `secret=` patterns

## Windows Pitfalls

### Windows Path Escaping in YAML

On Windows, paths like `C:\Users\...` in double-quoted YAML strings cause `\U` to be interpreted as a unicode escape, crashing the config parser. See `references/windows-yaml-paths.md` for the fix and all solutions.

### `hermes mcp add --args -y` Bug (Windows)

On Windows (git-bash/MSYS), `hermes mcp add filesystem --command npx --args "-y" --args "@modelcontextprotocol/server-filesystem"` **fails** — the CLI parser treats `-y` as an unknown Hermes flag rather than an MCP server argument:

```
hermes: error: unrecognized arguments: -y @modelcontextprotocol/server-filesystem
```

**Workaround A — Pre-install globally (recommended for npx servers):**

```bash
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-memory
npm install -g @modelcontextprotocol/server-sequential-thinking

hermes mcp add filesystem --command npx \
  --args "@modelcontextprotocol/server-filesystem" \
  --args "C:/Users/Admin/Desktop/Working"
```

**Workaround B — Custom Python server (more reliable):**

Python-based servers connect faster (~200ms vs npx's ~3s startup), avoid npm overhead, and allow custom security policies:

```bash
hermes mcp add filesystem --command python \
  --args "path/to/mcp_filesystem_server_windows.py"
```

See `scripts/mcp_filesystem_server_windows.py` for a full implementation with directory whitelist.

**Workaround C — Edit config.yaml directly:**

Use `hermes config edit` to add the entry manually:

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "C:/Users/Admin/Desktop/Working"]
    timeout: 60
```

Then run `/reload-mcp` in-session (or start a fresh session) to activate.

### GitHub MCP Token Requirement

The GitHub MCP server starts without a token, but all API calls return 401. Pass the token explicitly:

```bash
gh auth token   # get your current token
hermes mcp add github --command npx \
  --args "@modelcontextprotocol/server-github" \
  --env "GITHUB_PERSONAL_ACCESS_TOKEN=<token>"
```

### Hot-Reload Without Full Restart

After adding/removing MCP servers via config edit (not CLI), use the in-session slash command:

```
/reload-mcp
```

This reconnects all configured servers without restarting the entire agent. If unavailable, start a fresh session with `/reset` or `/new`.

## Recommended Server Quick-Reference

All 9 servers below were verified working on Windows (git-bash + Hermes CLI):

| Server | Config Command | Tools | Notes |
|--------|---------------|-------|-------|
| **sqlite** | `python scripts/mcp_sqlite_server.py --db data.db` | 3 | Database query; read-only enforced |
| **time** | `uvx mcp-server-time` | 2 | Timezone-aware current time + conversion |
| **filesystem** | `python scripts/mcp_filesystem_server_windows.py` | 5 | Custom; directory-whitelisted (reliable) |
| **github** | `npx @modelcontextprotocol/server-github` | 26 | Needs `GITHUB_PERSONAL_ACCESS_TOKEN` env |
| **fetch** | `uvx mcp-server-fetch` | 1 | Web content fetching (replaces curl for text) |
| **sequential-thinking** | `npx @modelcontextprotocol/server-sequential-thinking` | 1 | Step-by-step reasoning tool |
| **memory** | `npx @modelcontextprotocol/server-memory` | 9 | Knowledge graph; persistent entity/relation store |
| **git** | `uvx mcp-server-git` | 12 | Status, diff, commit, branch, log, show |

**Tool prefix convention after registration:**
- `mcp_time_get_current_time`
- `mcp_github_search_repositories`
- `mcp_git_git_status`
- `mcp_memory_create_entities`

## Troubleshooting

### "MCP SDK not available -- skipping MCP tool discovery"

The `mcp` Python package is not installed. Install it:

```bash
pip install mcp
```

### "No MCP servers configured"

No `mcp_servers` key in `~/.hermes/config.yaml`, or it's empty. Add at least one server.

### "Failed to connect to MCP server 'X'"

Common causes:
- **Command not found**: The `command` binary isn't on PATH. Ensure `npx`, `uvx`, or the relevant command is installed.
- **Package not found**: For npx servers, the npm package may not exist or may need `-y` in args to auto-install. On Windows, pre-install globally with `npm install -g` and omit `-y`.
- **Timeout**: The server took too long to start. Increase `connect_timeout`.
- **Port conflict**: For HTTP servers, the URL may be unreachable.
- **Windows npx spawn failure**: The `hermes mcp add` CLI has a known `-y` parsing bug on Windows. Use workaround options above.

### "MCP server 'X' requires HTTP transport but mcp.client.streamable_http is not available"

Your `mcp` package version doesn't include HTTP client support. Upgrade:

```bash
pip install --upgrade mcp
```

### Tools not appearing

- Check that the server is listed under `mcp_servers` (not `mcp` or `servers`)
- Ensure the YAML indentation is correct
- Look at Hermes Agent startup logs for connection messages
- Tool names are prefixed with `mcp_{server}_{tool}` -- look for that pattern
- Try `/reload-mcp` if you edited config.yaml directly without restarting

### Connection keeps dropping

The client retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s, capped at 60s). If the server is fundamentally unreachable, it gives up after 5 attempts. Check the server process and network connectivity.

## Examples

### Time Server (uvx)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
```

### Filesystem Server (npx — Windows-safe via pre-install)

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["@modelcontextprotocol/server-filesystem", "C:/Users/Admin/Desktop/Working"]
    timeout: 30
```

### GitHub Server with Authentication

```yaml
mcp_servers:
  github:
    command: "npx"
    args: ["@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***PAT_PREFIX***_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    timeout: 60
```

### Remote HTTP Server

```yaml
mcp_servers:
  company_api:
    url: "https://mcp.mycompany.com/v1/mcp"
    headers:
      Authorization: "Bearer sk-xxxxxxxxxxxxxxxxxxxx"
      X-Team-Id: "engineering"
    timeout: 180
    connect_timeout: 30
```

### Multiple Servers (Full Stack)

```yaml
mcp_servers:
  time:
    command: "uvx"
    args: ["mcp-server-time"]
  filesystem:
    command: "python"
    args: ["scripts/mcp_filesystem_server_windows.py"]
  github:
    command: "npx"
    args: ["@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "***PAT_PREFIX***_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  fetch:
    command: "uvx"
    args: ["mcp-server-fetch"]
  git:
    command: "uvx"
    args: ["mcp-server-git"]
  sequential-thinking:
    command: "npx"
    args: ["@modelcontextprotocol/server-sequential-thinking"]
  memory:
    command: "npx"
    args: ["@modelcontextprotocol/server-memory"]
```

All tools from all servers are registered and available simultaneously. Each server's tools are prefixed with its name to avoid collisions.

## Sampling (Server-Initiated LLM Requests)

Hermes supports MCP's `sampling/createMessage` capability — MCP servers can request LLM completions through the agent during tool execution. This enables agent-in-the-loop workflows (data analysis, content generation, decision-making).

Sampling is **enabled by default**. Configure per server:

```yaml
mcp_servers:
  my_server:
    command: "npx"
    args: ["-y", "my-mcp-server"]
    sampling:
      enabled: true           # default: true
      model: "gemini-3-flash" # model override (optional)
      max_tokens_cap: 4096    # max tokens per request
      timeout: 30             # LLM call timeout (seconds)
      max_rpm: 10             # max requests per minute
      allowed_models: []      # model whitelist (empty = all)
      max_tool_rounds: 5      # tool loop limit (0 = disable)
      log_level: "info"       # audit verbosity
```

Servers can also include `tools` in sampling requests for multi-turn tool-augmented workflows. The `max_tool_rounds` config prevents infinite tool loops. Per-server audit metrics (requests, errors, tokens, tool use count) are tracked via `get_mcp_status()`.

Disable sampling for untrusted servers with `sampling: { enabled: false }`.

## Notes

- MCP tools are called synchronously from the agent's perspective but run asynchronously on a dedicated background event loop
- Tool results are returned as JSON with either `{"result": "..."}` or `{"error": "..."}`
- The native MCP client is independent of `mcporter` -- you can use both simultaneously
- Server connections are persistent and shared across all conversations in the same agent process
- Adding or removing servers requires restarting the agent (no hot-reload currently), but `/reload-mcp` reconnects already-configured servers without full restart
