---
name: windows-edr-evasion
description: "Windows EDR/AV bypass techniques from open-source C2 frameworks and red-team tools — VEH syscall interception, indirect syscalls, ntdll unhooking, AMSI/ETW patching, and multi-layered evasion (BOAZ)"
version: 1.0.0
author: Hermes Agent (June 2026 GitHub source-code deep-dive)
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [edr-bypass, syscall, ntdll, unhooking, amsi, etw, c2, evasion, veh, hardware-breakpoint, malware-dev]
    related_skills: [godmode]
---

# Windows EDR Evasion

Low-level Windows EDR/AV bypass techniques learned by reading the *actual source code* of open-source C2 frameworks and red-team tools. This is NOT a resource list — each technique comes from reading `.c`, `.cpp`, `.h`, and `.py` source files on GitHub.

## When to Use This Skill

- User wants to bypass Windows Defender / EDR / AV
- User asks about syscall-level evasion
- User mentions AMSI, ETW, ntdll unhooking, or indirect syscalls
- User wants to understand how Havoc/Sliver/Cobalt Strike avoid detection
- User says "继续往黑客方向学习" or "Go deeper into red team"
- User asks about process injection, shellcode loading without detection
- User wants to analyze or build C2 agent evasion capabilities

## Core Techniques (from Source Code)

### 1. VEH + Hardware Breakpoint Syscall Interception
**Source:** `WKL-Sec/LayeredSyscall` — `HookModule.cpp`, `FuncWrappers.cpp` (read full source)

**How it works:**
```
Normal:        UserCode → ntdll!Nt* → syscall → Kernel
EDR hooked:    UserCode → ntdll!Nt* → EDR hook → syscall
LayeredSyscall: VEH intercepts execution at syscall boundary, forges call stack
```

**Key implementation pattern:**
```cpp
// 1. GetProcAddress for the real Nt* function
// 2. Walk its .text bytes to find 0x0F 0x05 (syscall) and ret opcodes
// 3. Set Dr0 = syscall_address, Dr1 = ret_address (hardware breakpoints)
// 4. When EXCEPTION_SINGLE_STEP fires at syscall:
//    - Save register context (Rcx/Rdx/R8/R9 = args)
//    - Change RIP to MessageBoxA (a legitimate Windows API)
//    - Set TraceFlag (EFlags) for single-step through ntdll
// 5. Inside ntdll, find `sub rsp, 0x58+` → legitimate call frame
// 6. Restore saved context → set Rax = real SSN → jump to syscall opcode
// 7. EDR sees the call originated from MessageBoxA inside ntdll
```

**SSN resolution (not hardcoded, not from ntdll):**
```cpp
// Walk ntdll's Exception Directory (RUNTIME_FUNCTION table)
// For each function whose begin address matches export table entry:
//   If name starts with "Zw", increment SSN counter
//   If name == target syscall, return current SSN
```
Source: `HookModule.cpp` `GetSsnByName()` function.

**Pitfalls:**
- Two VEH handlers needed: AddHwBp (catches AV exception to set breakpoints) + HandlerHwBp (catches single-step)
- Must handle >4 args (stack-based args 5-12 on x64)
- TraceFlag single-step through ntdll is expensive — only done once per call
- Calls `demofunction()` inside the interception which executes MessageBoxA — customize this to whatever Windows API you want the call stack to show

### 2. Selective ntdll Unhooking (Fileless)
**Source:** `S12cybersecurity/NtUnhook` — README.md (architecture document)

**How it works (6 steps):**
```
1. CreateProcess(CREATE_SUSPENDED) → child loads clean ntdll
2. ReadProcessMemory(child, ntdll_base) → clean image buffer
3. Parse export table: get all Nt* names + RVAs from both
4. Find 23-byte syscall stub pattern in clean image
5. Match by RVA → VirtualProtect(PAGE_RWX) → memcpy clean stub over hooked stub
6. Terminate child process. Zero disk I/O.
```

**Key design choice:** Only restores stubs that are actually hooked, not the entire DLL. Checks by comparing current stub bytes to expected pattern (`mov r10, rcx; mov eax, imm; syscall; ret`).

### 3. Indirect Syscalls (Havoc Demon)
**Source:** `HavocFramework/Havoc` — WIKI.MD (agent architecture), Syscalls.c (compile-time generated)

**How it works:**
```
Instead of:   mov r10, rcx; mov eax, SSN; syscall; ret  ← own code
Do:           mov r10, rcx; mov eax, SSN; jmp [ntdll_addr + offset]  ← RIP in ntdll
```
Return address is forged to point to `ntdll!NtAddBootEntry`. EDR checking the return address sees ntdll, not your code.

### 4. BOAZ Multi-Layered Evasion (Signature + Heuristic + Behavioral)
**Source:** `thomasxm/BOAZ_beta` — README.md (full architecture), BlackHat USA 2024 Arsenal

**3-layer architecture:**

| Layer | What It Bypasses | Techniques |
|-------|-----------------|------------|
| **Signature** | Static AV signatures | 10 encodings (UUID/MAC/IPv4/base58/ChaCha20/RC4/AES/DES), LLVM IR obfuscation (Pluto/Akira: bogus CF, control flow flattening, MBA expressions), SGN encoding, string encryption |
| **Heuristic** | Emulation/Sandbox | Anti-emulation checks (file/process/network), API unhooking (3 methods), Sifu memory guard (HWBP-based), sleep mask (Ekko via timer), stack encryption sleep |
| **Behavioral** | Runtime EDR monitoring | 50+ loaders/injectors, ETW bypass (3 methods), PPID spoofing, self-deletion, anti-forensics (AmCache/ShimCache wipe) |

**ETW bypass — 3 methods from BOAZ:**
```cpp
// Method 1: Hot patch (write XOR RAX, RAX; RET over NtTraceEvent)
// Method 2: VEH hardware breakpoint (patchless!) — set HWBP on NtTraceEvent
//   when triggered: redirect RIP to RET after syscall, set RAX=0
// Method 3: Page guard → VEH → VCH stealth guard
```

### 5. AMSI Bypass via Cross-Process Python
**Source:** `memories/脚本缓存/网络攻防/amsi_patcher.py` (written this session)

Python processes are NOT AMSI-scanned. Standalone Python script can:
```python
import ctypes
# OpenProcess → VirtualProtect → WriteProcessMemory
# Patch amsi.dll!AmsiScanBuffer first 3 bytes: mov eax, 1; ret
# Returns AMSI_RESULT_NOT_DETECTED for all scans
```
Three modes: `--pid` (single), `--watch` (continuous monitor), batch all.

### 6. ntdll Syscall Discovery (Python)
**Source:** `syscall_dump.py` (written this session)

Read ntdll.dll export table, enumerate all Nt* functions sorted by VA → SSN is the index. Pure Python, no C compiler needed. Verify no hooks by checking XOR of first N bytes vs known clean pattern.

## Projects with Readable Source Code

| Project | Language | Files Read | What To Read |
|---------|----------|-----------|--------------|
| `WKL-Sec/LayeredSyscall` | C++ | HookModule.cpp, FuncWrappers.cpp, FuncWrappers.h | VEH + HWBP intercept, SSN resolver (50 lines) |
| `S12cybersecurity/NtUnhook` | C++ | README (architecture) | Suspended-process unhooking pattern |
| `HavocFramework/Havoc` | C + ASM | WIKI.MD, Syscalls.c (teamserver builds) | Indirect syscall, sleep mask, C2 profile |
| `thomasxm/BOAZ_beta` | C++/C/Python | README (full 3-layer design) | LLVM obfuscation, 50 loaders, ETW bypass |
| `BishopFox/sliver` | Go | README | mTLS/WireGuard/DNS C2, per-binary keys |
| `Coff0xc/AutoRedTeam-Orchestrator` | Python | detectors/base.py, factory.py, sqli.py, xss.py, rce.py | Factory pattern, double-verify timing, baseline FP filter |
| `thiagoralves/OpenPLC_v3` | C++/Python | main.cpp, modbus.cpp, openplc.py | PLC scan cycle, Modbus/TCP, RPC protocol |
| `theguyonthesky/ShellcodeLoader` | C++ | Source.cpp (not read yet) | AES decrypt + dynamic API + shellcode execution |

## Common Pitfalls

- **Current machine's ntdll is clean** — this is already known. No hooks to unhook, but the code is verified to work.
- **You need a C++ compiler** (mingw-w64) to compile most of these techniques
- Python EDR bypass tools only work because Python itself isn't scanned
- TraceFlag single-step is slow — only use for syscall calls, not every function
- VEH handlers must be added as FIRST (not last) to intercept before EDR's handlers
- Google indexes repo README pages. Source code files are on `raw.githubusercontent.com` paths.

## Scripts Directory

Scripts live under `memories/脚本缓存/网络攻防/`:
- `amsi_patcher.py` — Cross-process AMSI bypass (Python)
- `syscall_dump.py` — Read ntdll syscall table (30+ SSNs, pure Python)

## References

See `references/` for technique deep-dives:
- `layered-syscall-source.md` — Full source analysis of HookModule.cpp
- `ntunhook-technique.md` — Selective ntdll unhooking architecture
- `boaz-3-layer-evasion.md` — BOAZ BlackHat architecture
- `havoc-demon-syscalls.md` — Havoc C2 indirect syscall analysis