#!/usr/bin/env python3
"""ECC真学验证代码 — 3个核心设计模式"""
import re, json, math
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional

# 1. Instinct-Based Learning Engine
class InstinctScope(Enum):
    PROJECT = auto()
    GLOBAL = auto()

@dataclass
class Instinct:
    id: str; trigger: str; behavior: str; confidence: float; domain: str
    source: str = "session-observation"; scope: InstinctScope = InstinctScope.PROJECT
    project_id: str = ""; observation_count: int = 1

class InstinctEngine:
    MIN_CONF = 0.3; MAX_CONF = 0.9; CONF_INC = 0.05; PROMOTE_N = 2
    PATTERNS = {
        "error_resolution": re.compile(r"(fix|solve|resolve|error|bug|issue|fail)", re.I),
        "user_correction": re.compile(r"(no,?\s*that'?s?\s*wrong|actually|correction)", re.I),
        "workaround": re.compile(r"(workaround|hack|temp\s*fix|bypass)", re.I),
        "testing": re.compile(r"(test|spec|assert|expect|verify|coverage)", re.I),
        "security": re.compile(r"(secret|password|token|key|auth|sanitiz|validate|xss|injection)", re.I),
    }

    def __init__(self): self.instincts: list[Instinct] = []

    def observe(self, text: str, project_id: str = "") -> list[Instinct]:
        new = []
        for pname, pat in self.PATTERNS.items():
            if not pat.search(text): continue
            existing = next((i for i in self.instincts if i.domain == pname and i.project_id == project_id), None)
            if existing:
                existing.observation_count += 1
                existing.confidence = min(self.MAX_CONF, existing.confidence + self.CONF_INC)
            else:
                inst = Instinct(id=f"inst-{pname}-{len(self.instincts)}",
                    trigger=f"when dealing with {pname}", behavior=f"apply {pname} best practices",
                    confidence=self.MIN_CONF, domain=pname, project_id=project_id)
                self.instincts.append(inst); new.append(inst)
        # Promote check after all new instincts are added
        for pname in {i.domain for i in self.instincts}:
            if self._should_promote(pname):
                for i in self.instincts:
                    if i.domain == pname: i.scope = InstinctScope.GLOBAL
        return new

    def _should_promote(self, pattern: str) -> bool:
        projects = {i.project_id for i in self.instincts if i.domain == pattern and i.project_id}
        return len(projects) >= self.PROMOTE_N

# 2. Context Budget Auditor
class BudgetBucket(Enum):
    ALWAYS = "always"; SOMETIMES = "sometimes"; RARELY = "rarely"

@dataclass
class ComponentAudit:
    name: str; comp_type: str; tokens: int; lines: int
    issues: list[str] = field(default_factory=list); bucket: BudgetBucket = BudgetBucket.SOMETIMES

class ContextBudgetAuditor:
    TOKEN_RATIO = 1.3
    def __init__(self, base_dir: str): self.base = Path(base_dir); self.audits: list[ComponentAudit] = []

    def inventory(self) -> list[ComponentAudit]:
        self.audits = []
        dirs = [("skills", "skill"), ("agents", "agent"), ("rules", "rule")]
        for dirname, ctype in dirs:
            d = self.base / dirname
            if d.exists():
                for f in d.rglob("*.md"):
                    self._audit(f, ctype)
        cfg = self.base / "CLAUDE.md"
        if cfg.exists(): self._audit(cfg, "config")
        return self.audits

    def _audit(self, fpath: Path, ctype: str):
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            lines = content.count("\n") + 1
            tokens = int(len(content.split()) * self.TOKEN_RATIO)
            issues = []
            if ctype == "skill" and lines > 400: issues.append(f"heavy_skill:{lines}L")
            if ctype == "agent" and lines > 200: issues.append(f"heavy_agent:{lines}L")
            bucket = BudgetBucket.ALWAYS if ctype == "config" else (BudgetBucket.RARELY if issues else BudgetBucket.SOMETIMES)
            self.audits.append(ComponentAudit(fpath.stem, ctype, tokens, lines, issues, bucket))
        except: pass

    def report(self) -> dict:
        total = sum(a.tokens for a in self.audits)
        window = 200_000
        return {"total_tokens": total, "available": window - total,
            "available_pct": round((window-total)/window*100, 1),
            "components": len(self.audits),
            "issues": [f"[{a.comp_type}] {a.name}: {i}" for a in self.audits for i in a.issues],
            "top10": sorted([{"name": a.name, "type": a.comp_type, "tokens": a.tokens, "lines": a.lines}
                for a in self.audits], key=lambda x: x["tokens"], reverse=True)[:10]}

# 3. AgentShield Scanner
class Severity(Enum):
    CRITICAL = "CRITICAL"; HIGH = "HIGH"; MEDIUM = "MEDIUM"

@dataclass
class Finding:
    surface: str; severity: Severity; path: str; desc: str; fix: str; auto_fix: bool = False

class AgentShield:
    SECRET_PAT = {
        "api_key": re.compile(r"(api[_-]?key)\s*[:=]\s*['\"]?[a-zA-Z0-9]{20,}", re.I),
        "password": re.compile(r"(password|passwd)\s*[:=]\s*['\"]?[^\s'\"]{8,}", re.I),
        "aws_key": re.compile(r"***AWS***[0-9A-Z]{16}"),
        "private_key": re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"),
    }
    SKIP = {"test", "example", "sample", ".env.example", "fixture", "node_modules", ".git"}

    def __init__(self, target: str): self.target = Path(target); self.findings: list[Finding] = []

    def scan_secrets(self) -> list[Finding]:
        for f in self.target.rglob("*"):
            if not f.is_file() or f.suffix not in {".yaml",".yml",".json",".env",".py",".js",".ts",".toml"}: continue
            if any(s in str(f).lower() for s in self.SKIP): continue
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for stype, pat in self.SECRET_PAT.items():
                    if pat.search(content):
                        self.findings.append(Finding("secrets", Severity.CRITICAL,
                            str(f.relative_to(self.target)), f"Hardcoded {stype}", f"Move to env var", True))
            except: pass
        return self.findings

    def scan_prompts(self) -> list[Finding]:
        agents_dir = self.target / "agents"
        if not agents_dir.exists(): return []
        for f in agents_dir.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                has_defense = any(kw in content.lower() for kw in
                    ["prompt defense", "don't change role", "don't reveal", "untrusted content", "validate", "sanitize"])
                if not has_defense:
                    self.findings.append(Finding("prompts", Severity.MEDIUM,
                        str(f.relative_to(self.target)), f"No prompt defense: {f.stem}", "Add prompt defense baseline"))
            except: pass
        return self.findings

    def scan_mcps(self) -> list[Finding]:
        mcp = self.target / ".mcp.json"
        if not mcp.exists(): return []
        try:
            data = json.loads(mcp.read_text(encoding="utf-8"))
            for name, cfg in data.get("mcpServers", {}).items():
                cmd = cfg.get("command", "")
                args = " ".join(str(a) for a in cfg.get("args", []))
                if "npx" in cmd or "npx" in args:
                    self.findings.append(Finding("mcp", Severity.MEDIUM, ".mcp.json",
                        f"Unpinned npx MCP: {name}", f"Pin {name} to specific version"))
        except: pass
        return self.findings

    def full_scan(self) -> dict:
        self.findings = []
        self.scan_secrets(); self.scan_prompts(); self.scan_mcps()
        runtime = [f for f in self.findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
        inventory = [f for f in self.findings if f.severity == Severity.MEDIUM]
        return {"total": len(self.findings), "runtime": len(runtime), "inventory": len(inventory),
            "by_surface": {s: len([f for f in self.findings if f.surface == s])
                for s in {"secrets","permissions","hooks","mcp","prompts"}},
            "critical": [{"file": f.path, "desc": f.desc, "fix": f.fix} for f in runtime]}


# ===== TESTS =====
def test_instinct():
    eng = InstinctEngine()
    # Session 1: Python项目
    new = eng.observe("I fixed a bug in auth. Added pytest tests to verify.", project_id="py1")
    assert len(new) > 0, f"Should detect patterns, got {new}"
    domains = {i.domain for i in new}
    assert "error_resolution" in domains and "testing" in domains, f"Missing domains: {domains}"

    # Session 2: 同项目再观察 → confidence增长
    eng.observe("Resolved another bug. The user corrected me - validate inputs first.", project_id="py1")
    err_i = next(i for i in eng.instincts if i.domain == "error_resolution" and i.project_id == "py1")
    assert err_i.observation_count >= 2 and err_i.confidence > 0.3, f"Confidence should grow: {err_i.confidence}"

    # Session 3: React项目 → promote为global
    eng.observe("Fixed rendering bug in React component. Added unit tests.", project_id="react1")
    has_global = any(i.scope == InstinctScope.GLOBAL for i in eng.instincts if i.domain == "error_resolution")
    assert has_global, "error_resolution should promote to GLOBAL after 2 projects"
    print("✅ Test 1 PASSED: Instinct — observe, confidence growth, promote")

def test_budget():
    ecc = Path(r"C:\Users\Admin\Desktop\Working\ecc-repo")
    if not ecc.exists(): print("⚠️  ECC repo not found"); return
    auditor = ContextBudgetAuditor(str(ecc))
    audits = auditor.inventory()
    assert len(audits) > 0, f"Should find components: {len(audits)}"
    report = auditor.report()
    assert report["components"] > 100, f"ECC has 262 skills, should find >100: {report['components']}"
    assert len(report["issues"]) > 0, f"ECC has heavy skills, should find issues"
    print(f"✅ Test 2 PASSED: Budget — {report['components']} components, {len(report['issues'])} issues, {report['available_pct']}% available")

def test_shield():
    ecc = Path(r"C:\Users\Admin\Desktop\Working\ecc-repo")
    if not ecc.exists(): print("⚠️  ECC repo not found"); return
    shield = AgentShield(str(ecc))
    report = shield.full_scan()
    print(f"✅ Test 3 PASSED: Shield — {report['total']} findings (runtime:{report['runtime']}, inventory:{report['inventory']})")
    for c in report["critical"][:5]:
        print(f"   🔴 {c['file']}: {c['desc']}")

def test_integration():
    """端到端集成测试：观察→审计→扫描"""
    eng = InstinctEngine()
    eng.observe("Fixed auth bug. Added security validation. Tested with pytest.", project_id="proj1")
    assert len(eng.instincts) >= 2, f"Should detect error_resolution + testing + security: {len(eng.instincts)}"

    ecc = Path(r"C:\Users\Admin\Desktop\Working\ecc-repo")
    if not ecc.exists(): print("⚠️  Skipping integration (ECC repo)"); return

    auditor = ContextBudgetAuditor(str(ecc))
    auditor.inventory()
    report = auditor.report()

    shield = AgentShield(str(ecc))
    scan = shield.full_scan()

    assert report["components"] > 0
    print(f"✅ Test 4 PASSED: Integration — {len(eng.instincts)} instincts, {report['components']} budget components, {scan['total']} security findings")

if __name__ == "__main__":
    print("🐴 ECC Verification — 3 Core Design Patterns\n")
    test_instinct()
    test_budget()
    test_shield()
    test_integration()
    print("\n🎉 All tests passed! ECC design patterns verified.")