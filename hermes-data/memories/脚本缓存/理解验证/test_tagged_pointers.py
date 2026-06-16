"""
MicroPython 标记指针理解验证
从源码 py/obj.h 记忆中还原，不翻笔记

Repr A (ARM Cortex-M, 32-bit):
  bit0=1  → small int (1-bit tag)
  bit0=0, bit1=1  → QSTR (2-bit tag 0b10)
  bit0=0, bit1=0  → 指针 (2-bit tag 0b00)

Repr C (x86-64, 64-bit):
  NaN-boxing: float/double 直接用 64bit IEEE754
  非float: 0x7fff 前缀 + 数据
"""

def mp_obj_new_int(val: int) -> int:
    return (val << 1) | 1

def mp_obj_is_small_int(obj: int) -> bool:
    return (obj & 1) != 0

def mp_obj_new_qstr(qstr_id: int) -> int:
    return (qstr_id << 2) | 2

def mp_obj_is_qstr(obj: int) -> bool:
    return (obj & 0b11) == 0b10

def mp_obj_is_ptr(obj: int) -> bool:
    return (obj & 0b11) == 0

def mp_obj_get_int(obj: int) -> int:
    assert mp_obj_is_small_int(obj), "不是小整数"
    val = obj >> 1
    if val & (1 << 30):
        val |= ~((1 << 31) - 1)
    return val


print("=" * 50)
print("MicroPython 标记指针理解验证")
print("=" * 50)

# test 1: small int
print("\n[测试1] 小整数编码/解码")
for v in [0, 1, 42, 127, -1, -42]:
    obj = mp_obj_new_int(v)
    decoded = mp_obj_get_int(obj)
    ok = "✓" if decoded == v else "✗"
    print(f"  {v:>5} -> tagged={obj:#010x} -> decoded={decoded:>5} {ok}")

# test 2: QSTR
print("\n[测试2] QSTR 编码")
for qid in [1, 5, 42, 255]:
    obj = mp_obj_new_qstr(qid)
    print(f"  qstr[{qid:>3}] -> tagged={obj:#010x}")
    assert mp_obj_is_qstr(obj), f"QSTR检测失败 qid={qid}"

# test 3: 类型鉴别
print("\n[测试3] 类型鉴别准确率")
test_cases = [
    ("small_int=42",   mp_obj_new_int(42),   "small_int"),
    ("small_int=-1",   mp_obj_new_int(-1),   "small_int"),
    ("qstr_id=5",      mp_obj_new_qstr(5),   "qstr"),
    ("qstr_id=255",    mp_obj_new_qstr(255), "qstr"),
    ("ptr=0x20001000", 0x20001000 & ~0b11,    "ptr"),
]

for label, obj, expected in test_cases:
    is_si = mp_obj_is_small_int(obj)
    is_q = mp_obj_is_qstr(obj)
    is_p = mp_obj_is_ptr(obj)
    result = "small_int" if is_si else ("qstr" if is_q else ("ptr" if is_p else "unknown"))
    ok = "✓" if result == expected else "✗"
    print(f"  {label:>20} -> detected={result:>10} {ok}")

# test 4: Cell for closure
class MpHackedCell:
    def __init__(self, obj=None):
        self.obj = obj
    def set(self, val):
        self.obj = val
    def get(self):
        return self.obj

print("\n[测试4] 闭包Cell机制理解")
def make_counter(start):
    n_cell = MpHackedCell(mp_obj_new_int(start))
    def counter():
        val = mp_obj_get_int(n_cell.get())
        n_cell.set(mp_obj_new_int(val + 1))
        return val
    return counter

c = make_counter(10)
for i in range(5):
    print(f"  counter[{i}] = {c()}")

# test 5: 值栈 VM
class MpVMStack:
    def __init__(self):
        self.stack = []
    def push(self, val):
        self.stack.append(val)
    def pop(self):
        return self.stack.pop()
    def top(self):
        return self.stack[-1] if self.stack else None
    def execute(self, bytecode):
        for i, (op, arg) in enumerate(bytecode):
            if op == 'LOAD_CONST':
                self.push(mp_obj_new_int(arg))
                print(f"  [{i}] LOAD_CONST {arg} -> stack=[{self._show()}]")
            elif op == 'BINARY_ADD':
                b = mp_obj_get_int(self.pop())
                a = mp_obj_get_int(self.pop())
                r = mp_obj_new_int(a + b)
                self.push(r)
                print(f"  [{i}] ADD {a}+{b}={a+b} -> stack=[{self._show()}]")
            elif op == 'BINARY_SUB':
                b = mp_obj_get_int(self.pop())
                a = mp_obj_get_int(self.pop())
                r = mp_obj_new_int(a - b)
                self.push(r)
                print(f"  [{i}] SUB {a}-{b}={a-b} -> stack=[{self._show()}]")
            elif op == 'RETURN_VALUE':
                return mp_obj_get_int(self.pop())
    def _show(self):
        return [mp_obj_get_int(x) if mp_obj_is_small_int(x) else hex(x) for x in self.stack]

print("\n[测试5] 字节码值栈模拟: a = 10 + 20 - 5")
vm = MpVMStack()
result = vm.execute([
    ('LOAD_CONST', 10),
    ('LOAD_CONST', 20),
    ('BINARY_ADD', None),
    ('LOAD_CONST', 5),
    ('BINARY_SUB', None),
    ('RETURN_VALUE', None),
])
print(f"  结果: {result} (应该=25) {'✓' if result==25 else '✗'}")

# test 6: GC模拟
class MpGC:
    def __init__(self, heap_size=256, block_size=16):
        self.block_size = block_size
        self.num_blocks = heap_size // block_size
        self.ATB = [0] * self.num_blocks
        self.MB = [0] * self.num_blocks
        self.heap = [None] * self.num_blocks
        self.next_free = 0
    
    def alloc(self, size_bytes):
        n = (size_bytes + self.block_size - 1) // self.block_size
        start = self.next_free
        scanned = 0
        while scanned < self.num_blocks:
            found = True
            for i in range(n):
                idx = (start + i) % self.num_blocks
                if self.ATB[idx] != 0:
                    found = False
                    start = (idx + 1) % self.num_blocks
                    break
            if found:
                break
            scanned += 1
        if not found:
            raise MemoryError("OOM")
        for i in range(n):
            idx = (start + i) % self.num_blocks
            self.ATB[idx] = 1 if i == 0 else 2
        self.next_free = (start + n) % self.num_blocks
        print(f"    分配 {size_bytes}B ({n}块) 在块{start}")
        return start
    
    def mark(self, block_idx):
        if self.MB[block_idx]:
            return
        self.MB[block_idx] = 1
        if self.ATB[block_idx] == 1:
            idx = block_idx + 1
            while idx < self.num_blocks and self.ATB[idx] == 2:
                self.MB[idx] = 1
                idx += 1
    
    def sweep(self):
        freed = 0
        for i in range(self.num_blocks):
            if self.ATB[i] != 0 and self.MB[i] == 0:
                self.ATB[i] = 0
                self.heap[i] = None
                freed += 1
            self.MB[i] = 0
        self.next_free = 0
        return freed

print("\n[测试6] GC模拟 (无free list)")
gc = MpGC(256, 16)
print(f"  堆: {gc.num_blocks} 块 x {gc.block_size}字节")
b1 = gc.alloc(32)
b2 = gc.alloc(16)
b3 = gc.alloc(48)
print(f"  GC前空闲块: {gc.ATB.count(0)}")
gc.mark(b1)
gc.mark(b3)
freed = gc.sweep()
print(f"  GC清扫回收: {freed} 块")
print(f"  GC后空闲块: {gc.ATB.count(0)}")

print("\n" + "=" * 50)
print("验证完成")
print("=" * 50)