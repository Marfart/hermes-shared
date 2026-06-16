"""
==========================================================
sqlmap 核心架构贯通理解
从源码读取中学习的7大设计要点 + 微型实现验证
==========================================================

源码阅读:
  sqlmap.py          — 入口
  lib/core/agent.py  — Agent类
  lib/core/option.py — 选项初始化
  lib/controller/controller.py — 主控制流程
  lib/controller/checks.py     — 注入检测引擎
  lib/request/comparison.py    — 页面比较引擎
  lib/techniques/blind/inference.py — 盲注二分推断算法

7大核心设计:
  1. 边界 + payload 分离架构
  2. 注入类型分层 (Boolean/Error/Union/Time/Stacked)
  3. 页面比较引擎 (SequenceMatcher)
  4. 二分盲注推断
  5. Agent payload代理层
  6. 启发式预检测
  7. Tamper脚本系统
"""

import re
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

# ================================================================
# 核心设计1: 页面比较引擎 (comparison.py)
# ================================================================

class PageComparator:
    """模拟 sqlmap 的页面比较引擎 (lib/request/comparison.py)"""
    UPPER_RATIO = 0.85
    LOWER_RATIO = 0.10

    def __init__(self, original_page):
        self.original = original_page
        self.dynamic_tokens = [
            r'\bcsrf_token[=:][a-f0-9]{32}\b',
            r'\bnonce[=:][a-f0-9]{16}\b',
            r'\btimestamp[=:]\d{10}\b',
        ]

    def _remove_dynamic(self, page):
        for pattern in self.dynamic_tokens:
            page = re.sub(pattern, 'DYNAMIC', page)
        return page

    def compare(self, page, get_ratio=False):
        if page is None:
            return None
        cleaned_orig = self._remove_dynamic(self.original)
        cleaned_page = self._remove_dynamic(page)
        if cleaned_orig == cleaned_page:
            ratio = 1.0
        elif len(cleaned_orig) == 0 or len(cleaned_page) == 0:
            ratio = 0.0
        else:
            shorter = min(len(cleaned_orig), len(cleaned_page))
            longer = max(len(cleaned_orig), len(cleaned_page))
            length_ratio = shorter / longer if longer > 0 else 0
            matches = sum(1 for a, b in zip(cleaned_orig, cleaned_page) if a == b)
            char_ratio = matches / longer if longer > 0 else 0
            ratio = (length_ratio + char_ratio) / 2
        if get_ratio:
            return ratio
        if ratio >= self.UPPER_RATIO:
            return True
        elif ratio <= self.LOWER_RATIO:
            return False
        return None

# ================================================================
# 核心设计2: Boundary + Payload 分离
# ================================================================

class Boundary:
    """sqlmap 边界 — 前缀/后缀/位置"""
    def __init__(self, place, prefix, suffix, where='ORIGINAL', level=1):
        self.place = place
        self.prefix = prefix
        self.suffix = suffix
        self.where = where
        self.level = level

BOUNDARIES = [
    Boundary('GET', "'", " -- "),
    Boundary('GET', "'", " #"),
    Boundary('GET', "", ""),
    Boundary('GET', " AND ", "", 'NEGATIVE'),
    Boundary('GET', ")", ""),
    Boundary('GET', '")', " -- "),
]

# ================================================================
# 核心设计3: 注入检测引擎
# ================================================================

class SQLInjectionEngine:
    """微型 sqlmap 注入引擎"""

    TECHNIQUE_BOOLEAN = 'BOOLEAN'
    TECHNIQUE_ERROR = 'ERROR'
    TECHNIQUE_UNION = 'UNION'
    TECHNIQUE_TIME = 'TIME'

    def __init__(self):
        self.original_page = None
        self.vulnerable = False
        self.technique = None
        self.boundary = None

    def _simulate_request(self, url, param_val):
        """模拟HTTP响应 — 模拟 SQL: SELECT * FROM users WHERE id = '1'"""
        p = str(param_val)
        # 布尔条件检测: X=X → True, X=Y(X!=Y) → False
        eq_match = re.search(r'(\d+)=(\d+)', p)
        if eq_match:
            a, b = int(eq_match.group(1)), int(eq_match.group(2))
            if a == b:
                return "<html><body>User: admin (ID: 1)</body></html>"
            else:
                return "<html><body><h1>No results found</h1></body></html>"
        # SQL 语法错误
        if "'" in p and "--" not in p and "#" not in p and not re.search(r'\d+=\d+', p):
            return '<html><body><h1>Database Error</h1><p>SQL syntax error</p></body></html>'
        # UNION 注入
        if "UNION" in p.upper():
            return "<html><body>User: admin (ID: 1) extra_data</body></html>"
        # 时间盲注
        if "SLEEP" in p.upper() or "WAITFOR" in p.upper():
            time.sleep(2.5)
        return "<html><body>User: admin (ID: 1)</body></html>"

    def _heuristic_check(self, param_val):
        """启发式检测 — 看特殊字符是否引起页面变化"""
        self.original_page = self._simulate_request("http://target/page.php?id=1", 1)
        for char in ["'", '"', ')', ';']:
            page = self._simulate_request("", f"1{char}")
            ratio = PageComparator(self.original_page).compare(page, get_ratio=True)
            if ratio < 0.95:
                log.info(f"  [启发式] 字符 '{char}' → 页面变化 ratio={ratio:.3f}")
                return char
        return None

    def _boolean_test(self, boundary, param_val):
        """Boolean-based 盲注检测"""
        marker = random.randint(1000, 9999)
        true_cond = f"{boundary.prefix}AND {marker}={marker}{boundary.suffix}"
        false_cond = f"{boundary.prefix}AND {marker}={marker + 1}{boundary.suffix}"
        true_page = self._simulate_request("", f"{param_val}{true_cond}")
        false_page = self._simulate_request("", f"{param_val}{false_cond}")
        cmp = PageComparator(self.original_page)
        tr = cmp.compare(true_page)
        fr = cmp.compare(false_page)
        log.info(f"    Bool: True={tr} False={fr}")
        return tr is True and fr is False

    def _union_test(self, param_val):
        """UNION 查询测试 — 逐列尝试 NULL"""
        for cols in [1, 2, 3]:
            nulls = ','.join(['NULL'] * cols)
            page = self._simulate_request("", f"{param_val}' UNION ALL SELECT {nulls} -- ")
            cmp = PageComparator(self.original_page)
            ratio = cmp.compare(page, get_ratio=True)
            if ratio < 0.95 and 'ERROR' not in page:
                log.info(f"  [UNION] 列数={cols} ratio={ratio:.3f}")
                return cols
        return None

    def _time_test(self, param_val):
        """Time-based 盲注检测"""
        start = time.time()
        self._simulate_request("", f"{param_val}' AND SLEEP(5) -- ")
        dur = time.time() - start
        start2 = time.time()
        self._simulate_request("", param_val)
        normal = time.time() - start2
        if dur - normal > 2:
            log.info(f"  [Time] 延迟 {dur:.1f}s vs 正常 {normal:.1f}s")
            return True
        return False

    def scan(self, url, param, param_val):
        log.info(f"\n{'='*50}")
        log.info(f"扫描: {url}?{param}={param_val}")
        log.info(f"{'='*50}")

        # 1. 启发式
        log.info("\n[阶段1] 启发式检测...")
        trigger = self._heuristic_check(param_val)
        if not trigger:
            log.info("  无发现 → 可能无注入")
            return False
        log.info(f"  触发字符: '{trigger}'")

        # 2. 遍历边界 × 技术
        log.info(f"\n[阶段2] 检测 {len(BOUNDARIES)} 个边界...")
        is_num = str(param_val).isdigit()

        for bi, b in enumerate(BOUNDARIES):
            if not is_num and "'" not in b.prefix and '"' not in b.prefix and b.prefix != '':
                continue
            log.info(f"  边界 {bi}: prefix={b.prefix!r} suffix={b.suffix!r}")
            if self._boolean_test(b, param_val):
                log.info("  → [漏洞] Boolean-based 盲注!")
                self.vulnerable = True
                self.technique = self.TECHNIQUE_BOOLEAN
                self.boundary = b
                return True

        log.info("  Boolean 无发现，尝试其他技术...")
        if self._union_test(param_val):
            log.info("  → [漏洞] UNION 查询!")
            self.vulnerable = True
            self.technique = self.TECHNIQUE_UNION
            return True
        if self._time_test(param_val):
            log.info("  → [漏洞] Time-based 盲注!")
            self.vulnerable = True
            self.technique = self.TECHNIQUE_TIME
            return True

        log.info("  无注入发现")
        return False


# ================================================================
# 测试
# ================================================================

print("=" * 60)
print("sqlmap 核心架构贯通验证")
print("读自: 7个核心源文件 (py源码)")
print("=" * 60)

# 测试1: 注入扫描
print("\n" + "-" * 60)
print("测试1: 模拟 SQL 注入扫描")
print("-" * 60)
eng = SQLInjectionEngine()
eng.scan("http://target/page.php", "id", "1")

# 测试2: 页面比较引擎
print("\n" + "-" * 60)
print("测试2: 页面比较引擎")
print("-" * 60)
pc = PageComparator("<html><body>User: admin</body></html>")
for name, pg in [
    ("相同", "<html><body>User: admin</body></html>"),
    ("动态token", '<html><body>User: admin csrf_token=abc123def456ghijklmnop1234567890</body></html>'),
    ("不同", "<html><body>ERROR 404</body></html>"),
]:
    r = pc.compare(pg, get_ratio=True)
    b = pc.compare(pg)
    print(f"  {name:>12}: ratio={r:.3f} → {b}")

# 测试3: 二分法字符推断 (blind injection)
print("\n" + "-" * 60)
print("测试3: 盲注二分法字符推断")
print("-" * 60)

def bisect(target):
    lo, hi, steps = 32, 126, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        steps += 1
        if ord(target) > mid:
            lo = mid + 1
        else:
            hi = mid - 1
    print(f"  {target!r} → ASCII {lo} ({chr(lo)}) 步数={steps} {'✓' if chr(lo) == target else '✗'}")
    return chr(lo)

for c in "SqL":
    bisect(c)

# 测试4: Tamper
print("\n" + "-" * 60)
print("测试4: Tamper 脚本链")
print("-" * 60)
def t_upper(p):
    return re.sub(r'\b(union|select)\b', lambda m: m.group(1).upper(), p, flags=re.I)
def t_space2comment(p):
    return p.replace(' ', '/**/')
p = "' UNION SELECT * FROM users --"
print(f"  原始: {p}")
print(f"  → t_upper: {t_upper(p)}")
print(f"  → t_upper+t_s2c: {t_space2comment(t_upper(p))}")

print("\n" + "=" * 60)
print("验证完成")
print("=" * 60)