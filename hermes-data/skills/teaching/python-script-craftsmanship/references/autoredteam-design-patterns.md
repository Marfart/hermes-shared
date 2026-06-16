# AutoRedTeam Design Patterns (June 2026)

Extracted from reading `Coff0xc/AutoRedTeam-Orchestrator` v3.1.0 source code.
Core files read: `mcp_stdio_server.py`, `handlers/__init__.py`, `handlers/recon_handlers.py`, `handlers/detector_factory.py`, `handlers/redteam_handlers.py`

## Pattern 1: Factory-Generated Tool Registration

**Problem:** 26 vulnerability detectors with ~70% structural overlap. Writing each one individually creates massive code duplication.

**Solution:** Configuration-driven factory that generates tool functions from declarative configs.

```python
@dataclass
class DetectorConfig:
    name: str                    # tool name (e.g. "sqli_scan")
    detector_class: str          # class name (e.g. "SQLiDetector")
    description: str             # tool description
    vuln_type: str = ""          # vulnerability type details
    extra_params: Dict[str, Any] = field(default_factory=dict)
    result_formatter: Optional[Callable] = None

# 26 detectors defined as data, not code
DETECTOR_CONFIGS = [
    DetectorConfig(name="sqli_scan", detector_class="SQLiDetector",
                   description="SQL注入检测", vuln_type="支持: 错误/布尔/时间/联合"),
    DetectorConfig(name="xss_scan", detector_class="XSSDetector",
                   description="XSS漏洞检测", vuln_type="支持: 反射/存储/DOM"),
    # ... 24 more
]

def create_detector_tool(config, mcp, logger):
    """Factory: generates a tool function from config"""
    async def _detect(url, params=None, **kwargs):
        detector_cls = getattr(detectors_module, config.detector_class)
        detector = detector_cls()
        results = await detector.async_detect(url, params=params or {}, **kwargs)
        return {"success": True, "vulnerable": len(findings) > 0, ...}
    
    # Set function metadata BEFORE decorator application
    _detect.__name__ = config.name
    _detect.__doc__ = f"{config.description}\n{config.vuln_type}\n..."
    
    # Apply decorator chain
    wrapped = handle_errors(logger, ...)(_detect)
    wrapped = validate_inputs(url="url")(wrapped)
    wrapped = tool(mcp, name=config.name)(wrapped)
    return wrapped

# Batch registration
for config in DETECTOR_CONFIGS:
    create_detector_tool(config, mcp, logger)
```

**Key design decisions:**
- Configs are data (dataclass), not code — easy to add/remove/modify
- Function metadata (`__name__`, `__doc__`) set BEFORE decorators so MCP sees correct names
- Factory returns the registered function — no global registry needed
- Special-case tools (vuln_scan, nuclei_scan) registered separately outside factory

## Pattern 2: Three-Layer Decorator Chain

**Problem:** Every tool function needs authorization, input validation, and error handling. Writing this in every function is repetitive and error-prone.

**Solution:** Stacked decorators that each handle one cross-cutting concern.

```python
@tool(mcp)                          # Layer 3: Register with MCP
@require_critical_auth              # Layer 2a: Authorization
@validate_inputs(target="target")   # Layer 2b: Input validation
@handle_errors(logger, ErrorCategory.RECON, extract_target)  # Layer 1: Error handling
async def port_scan(target, ports="1-1000", timeout=2.0):
    """端口扫描 - 探测目标开放端口和服务"""
    from core.recon import async_scan_ports
    results = await async_scan_ports(target, ports, timeout=timeout)
    return {"success": True, "open_ports": [...], ...}
```

**Decorator order (outermost to innermost):**
1. `@tool(mcp)` — outermost, registers with MCP last (after all wrappers applied)
2. `@require_critical_auth` — checks auth before allowing execution
3. `@validate_inputs(...)` — validates and sanitizes parameters
4. `@handle_errors(...)` — innermost, wraps the actual function in try/except

**Error handling decorator pattern:**
```python
def handle_errors(logger, category, context_extractor=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValidationError as e:
                return {"success": False, "error": str(e), "category": category.value}
            except TimeoutError as e:
                return {"success": False, "error": f"Timeout: {e}"}
            except Exception as e:
                logger.error(f"[{category.value}] {func.__name__}: {e}")
                return {"success": False, "error": str(e)}
        return wrapper
    return decorator
```

## Pattern 3: Modular Handler Registration

**Problem:** 132 tools across 21 categories in one file is unmaintainable.

**Solution:** Each category gets its own module with a `register_*_tools(mcp, counter, logger)` function. A central `__init__.py` imports and calls them all.

```python
# handlers/__init__.py
from .recon_handlers import register_recon_tools
from .detector_factory import register_detector_tools
from .redteam_handlers import register_redteam_tools
# ... 18 more imports

def register_all_handlers(mcp, counter, logger):
    handlers = [
        ("侦察工具", register_recon_tools),
        ("漏洞检测工具", register_detector_tools),
        ("红队工具", register_redteam_tools),
        # ... 21 total
    ]
    for name, register_func in handlers:
        try:
            register_func(mcp, counter, logger)
        except ImportError as e:
            logger.warning(f"{name}注册失败: {e}")
        except Exception as e:
            logger.warning(f"{name}注册失败: {type(e).__name__}: {e}")
```

**Each handler module pattern:**
```python
def register_recon_tools(mcp, counter, logger):
    @tool(mcp)
    async def port_scan(target, ...):
        ...
    
    @tool(mcp)
    async def fingerprint(url):
        ...
    
    # ... 7 more tools
    
    counter.add("recon", 9)
    logger.info(f"[Recon] 已注册 9 个侦察工具")
```

## Pattern 4: Passive Recon (Zero-Traffic Intelligence)

**Problem:** Active scanning alerts the target. Need to gather intel without touching their servers.

**Solution:** Query 6 public data sources that already have the target's data cached.

```python
sources = [
    "crt.sh",           # Certificate Transparency logs — every SSL cert ever issued
    "HackerTarget",     # Passive DNS database
    "ThreatCrowd",      # Threat intelligence platform
    "URLScan.io",       # Website screenshot & resource archive
    "AlienVault OTX",   # Open Threat Exchange
    "RapidDNS"          # DNS history records
]

async def discover_subdomains_with_sources(domain):
    by_source = {}
    for source_name, source_fn in sources.items():
        try:
            results = await source_fn(domain)
            by_source[source_name] = results
        except Exception:
            by_source[source_name] = []
    return by_source
```

## Pattern 5: Post-Exploit Evasion Chain

**Problem:** EDR detects individual evasion techniques. Need a coordinated sequence.

**Solution:** Chain techniques in the correct order — AMSI first, then ETW, then stager.

```python
# Complete EDR bypass chain (order matters!)
chain = [
    post_exploit_amsi_bypass(),    # 1. Patch AMSI first (blocks PowerShell scanning)
    post_exploit_etw_bypass(),     # 2. Then patch ETW (blocks event logging)
    post_exploit_stager(),         # 3. Generate stager with both bypasses baked in
    post_exploit_evasion_chain()   # 4. Full evasion chain (unhook ntdll, indirect syscalls)
]
```

## Pattern 6: Tool Counter for Runtime Statistics

**Problem:** Need to know how many tools are registered at runtime without hardcoding counts.

**Solution:** A simple counter class that each module increments.

```python
class ToolCounter:
    def __init__(self):
        self.counts = {
            "recon": 0, "detector": 0, "redteam": 0,
            "lateral": 0, "persistence": 0, "ad": 0,
            # ... 16 categories
        }
        self.total = 0
    
    def add(self, category: str, count: int = 1):
        self.counts[category] += count
        self.total += count
    
    def summary(self) -> str:
        parts = [f"{k}={v}" for k, v in self.counts.items() if v > 0]
        return f"总计 {self.total} 个工具 ({', '.join(parts)})"
```

## Comparison with Existing Patterns

| AutoRedTeam Pattern | Existing python-script-craftsmanship Pattern | Notes |
|---|---|---|
| Factory-generated tools | — | **New.** Not covered by existing patterns |
| Three-layer decorator chain | Decorator泛化 (Pattern F) | Similar concept, but AutoRedTeam's auth+validation+error chain is more structured |
| Modular handler registration | — | **New.** Not covered by existing patterns |
| Passive recon | — | **New.** Not covered by existing patterns |
| Evasion chain | — | **New.** Not covered by existing patterns |
| Tool counter | — | **New.** Not covered by existing patterns |
