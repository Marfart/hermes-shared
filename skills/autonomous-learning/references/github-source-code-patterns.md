# GitHub Source Code Patterns (June 2026)

Extracted from reading SysWhispers4, AutoRedTeam-Orchestrator, Outflank Dumpert, the-book-of-secret-knowledge, and pure-bash-bible.

## 1. SysWhispers4 — EDR Bypass via Direct Syscalls

**Repo:** JoasASantos/SysWhispers4 (Python-based syscall stub generator)
**Core files:** `core/generator.py` (90KB), `core/models.py`, `README.md`

### Architecture

```
8 SSN Resolution Methods:
  Static            — embedded j00ru table (fastest, least stealthy)
  FreshyCalls       — sort Nt* exports by VA → index = SSN (default, hook-resistant)
  Hell's Gate       — read SSN from stub opcode bytes (fails if hooked)
  Halo's Gate       — Hell's Gate + neighbor scan ±8 stubs
  Tartarus' Gate    — detects E9/FF25/EB/CC hooks, ±16 neighbors
  SyscallsFromDisk  — map clean ntdll from \KnownDlls\ (bypasses ALL hooks)
  RecycledGate      — FreshyCalls + opcode cross-validation (most resilient)
  HW Breakpoint     — DR0 + VEH to extract SSN without reading function bytes

4 Invocation Methods:
  Embedded    — syscall in your stub (RIP in your PE)
  Indirect    — jmp to syscall;ret gadget in ntdll (RIP in ntdll)
  Randomized  — random gadget from pool of 64 per call
  Egg Hunt    — no 0F 05 opcode in binary on disk

8 Evasion Techniques:
  AMSI Bypass, ETW Bypass, ntdll Unhooking, Anti-Debug (6 checks),
  Sleep Encryption (Ekko-style), XOR SSN encryption,
  Call Stack Spoofing, Junk Instruction Injection (14 variants)
```

### Key Code Pattern: FreshyCalls Algorithm

```python
# Sort all Nt* exports by virtual address → sorted index = SSN
# Works even if EVERY stub is hooked (reads only VAs, not function bytes)
exports = []
for i in range(num_names):
    name = get_export_name(i)
    if name.startswith("Nt"):
        exports.append({"address": get_export_addr(i), "hash": djb2_hash(name)})
sort_by_address(exports)
# exports[0].address < exports[1].address < ...
# SSN for function at sorted index i = i
```

### Key Code Pattern: ntdll Unhooking

```c
// Map clean ntdll from \KnownDlls\, overwrite hooked .text section
NtOpenSection(&hSection, SECTION_MAP_READ, &oa);
NtMapViewOfSection(hSection, -1, &pClean, ...);
// Find .text section in both copies
memcpy(pHooked + .text_offset, pClean + .text_offset, .text_size);
// All EDR hooks removed
```

---

## 2. AutoRedTeam-Orchestrator — AI Red Team Platform

**Repo:** Coff0xc/AutoRedTeam-Orchestrator (v3.1.0, 132 MCP tools)
**Core files:** `mcp_stdio_server.py`, `handlers/__init__.py`, `handlers/recon_handlers.py`, `handlers/detector_factory.py`, `handlers/redteam_handlers.py`

### Architecture

```
MCP (JSON-RPC)  |  Python SDK  |  Typer CLI
        ↓               ↓               ↓
    handlers/ (132 tools across 21 modules)
        ↓
    core/ Engine Layer
    ├── detectors/    26 pure-Python detectors (SQLi/XSS/SSRF/RCE...)
    ├── exploit/      Exploitation engine
    ├── recon/        10-stage recon (port/DNS/fingerprint/subdomain/dir)
    ├── lateral/      Lateral movement (SMB/SSH/WMI/WinRM/PsExec)
    ├── c2/           C2 framework (Beacon + DNS/HTTP/WS tunnels)
    ├── orchestrator/ MCTS planner + 8-stage pipeline
    ├── nuclei_engine Pure Python Nuclei YAML template engine
    ├── llm/          Unified LLM provider (optional)
    ├── sandbox/      Docker sandbox executor (optional)
    └── knowledge/    SQLite knowledge graph (17 entity types)
```

### Key Code Pattern: Factory-Generated Detectors

```python
# 26 detectors with ~70% structural overlap → factory pattern
DETECTOR_CONFIGS = [
    DetectorConfig(name="sqli_scan", detector_class="SQLiDetector",
                   description="SQL注入检测", vuln_type="支持: 错误/布尔/时间/联合"),
    DetectorConfig(name="xss_scan", detector_class="XSSDetector",
                   description="XSS漏洞检测", vuln_type="支持: 反射/存储/DOM"),
    # ... 26 total
]

def create_detector_tool(config, mcp, logger):
    async def _detect(url, params=None, **kwargs):
        detector_cls = getattr(detectors_module, config.detector_class)
        detector = detector_cls()
        results = await detector.async_detect(url, params=params or {}, **kwargs)
        return {"success": True, "vulnerable": len(findings) > 0, ...}
    _detect.__name__ = config.name
    _detect.__doc__ = config.description
    return tool(mcp, name=config.name)(_detect)
```

### Key Code Pattern: Decorator Chain for Error Handling

```python
@tool(mcp)
@require_critical_auth          # Authorization layer
@validate_inputs(target="target") # Input validation
@handle_errors(logger, ErrorCategory.RECON, extract_target)  # Unified error handling
async def port_scan(target, ports="1-1000", timeout=2.0):
    ...
```

---

## 3. pure-bash-bible — Pure Bash Replacement for External Commands

**Repo:** dylanaraps/pure-bash-bible (36k⭐)
**Core files:** README.md

### Key Techniques

| Technique | External Command Replaced | Bash Equivalent |
|-----------|--------------------------|-----------------|
| Parameter expansion `${VAR##}` / `${VAR%%}` | `basename`, `dirname`, `cut`, `sed` | `${path##*/}` = basename, `${path%/*}` = dirname |
| Case conversion `${VAR,,}` / `${VAR^^}` | `tr A-Z a-z` | `${str,,}` = lowercase, `${str^^}` = uppercase |
| Substring replacement `${VAR//old/new}` | `sed s/old/new/g` | `${str//find/replace}` |
| `$_` magic variable + `:` builtin | Temp variables | `: "${str// /_}"` then `printf '%s\n' "$_"` |
| `printf -v` for formatting | External loops | `printf -v bar "%${n}s"` then `${bar// /#}` for progress bars |
| Background jobs + `wait` | GNU Parallel | `cmd &` + `wait $pid` + temp files for output |

---

## 4. the-book-of-secret-knowledge — CLI Weapon Library

**Repo:** trimstray/the-book-of-secret-knowledge (113K⭐)
**Core files:** README.md (211KB)

### CLI One-Liners

```bash
# Network scanning
masscan 10.0.0.0/8 -p443 --rate=10000    # Scan entire A-class in 10s
nmap -sV --script=http-enum target.com     # Web service enumeration

# Exploitation
sqlmap -u "http://target.com/page?id=1" --batch --dbs
hydra -l admin -P rockyou.txt ssh://target

# Reverse engineering
objdump -d binary | grep "syscall"         # Find syscall instructions

# Forensics
strings memory.dump | grep -E "password|secret|key"
volatility -f memory.dump imageinfo
```