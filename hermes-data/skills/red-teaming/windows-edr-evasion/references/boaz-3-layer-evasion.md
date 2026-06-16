# BOAZ Multi-Layered Evasion — Architecture Analysis

**Repo:** `thomasxm/BOAZ_beta`
**Files Read:** README.md (full 3-layer architecture)
**Conference:** BlackHat USA 2024 Arsenal | DEFCON 33

## Overview

BOAZ (Bypass, Obfuscate, Adapt, Zero-trace) is a multi-layered evasion framework that combines signature, heuristic, and behavioral bypass techniques. Takes x64 PE or raw .bin, outputs an undetectable polymorphic binary. Written in C++/C with Python orchestrator.

## Layer 1: Signature Evasion

### Payload Encodings (10 types)
```
UUID      → Each 16 bytes of shellcode = one UUID, array decoded at runtime
XOR       → Single-byte or multi-byte key
MAC       → 6 bytes = XX:XX:XX:XX:XX:XX format, 1500 bytes = 250 MACs
IPv4      → 4 bytes = dotted decimal
base64    → Standard base64
base45    → QR-code optimized encoding
base58    → Bitcoin address encoding (removes confusing chars: 0/O/I/l)
ChaCha20  → Stream cipher
RC4       → SystemFunction032/033 (native Windows API!)
AES + Divide&Conquer → Split into chunks, decrypt separately to bypass logical path hijacking
DES       → SystemFunction002 (native Windows API!)
```

### LLVM IR-Level Obfuscation

Two LLVM-based obfuscator compilers integrated as build tools:

**Pluto passes:**
- `bcf` — Bogus Control Flow (insert fake branches that never execute)
- `fla` — Control Flow Flattening (convert all branches to switch-case with state variable)
- `gle` — Global Variable Encryption (encrypt all global variables at compile time)
- `mba` — Mixed-Boolean Arithmetic (replace `a+b` with `(a^b) + 2*(a&b)` — functionally same, signature different)
- `sub` — Instruction Substitutions
- `idc` — Indirect Call Promotion (replace direct calls with function pointers)

**Akira passes:**
- Indirect jumps with encrypted jump targets
- Encrypted indirect function calls
- Encrypted indirect global variable references
- String encryption (all strings encrypted at compile time)
- Procedure-related control flow flattening

### Additional Signature Techniques
- Stripped binary (remove debug info, symbol table, resource sections)
- Entropy reduction — pad null bytes or Pokemon names to bring entropy below AV threshold
- Fake signed certificate (Masquerade as legitimate software)
- Metadata copied from Windows system binary

## Layer 2: Heuristic Evasion

### Anti-Emulation Checks
Multiple checks that detect running in a sandbox/emulator:
- File system operation timing (real disk vs simulated)
- Process list analysis (typical emulator processes missing)
- Network connectivity patterns
- Registry key existence
- "Offer you have to refuse" — if 2+ checks fail, execution stops

### API Unhooking (3 methods)
1. Read syscall stub from original ntdll → rewrite hooked stub
2. Perun's Fart — custom unhooking
3. Halo's Gate (TartarusGate) — find clean syscall via address sorting

### Sifu Memory Guard
Hardware breakpoint-based memory protection:
```
Instead of VirtualProtect(PAGE_GUARD) which EDR can detect:
→ Set Dr0-Dr3 breakpoints on shellcode pages
→ When EDR tries to scan that page → VEH handler fires
→ Return zeroed/encrypted data to scanner
→ When our code accesses the page → VEH handler allows it
```
Multiple guard variants: PG→VEH, PG→VEH→VCH (vectored continued handler), virtual table hooking execution guard.

### Sleep Mask & Stack Encryption
- Custom Ekko implementation using `CreateTimerQueueTimer` (not `WaitForSingleObjectEx`)
- Sleeps: encrypt all local variables + shellcode on stack, then call sleep
- Wakes: decrypt, continue execution
- During sleep, memory scanner sees only encrypted garbage

### PIC Converters (6 types)
- Donut (The Wover) — PE → shellcode
- PE2SH (hasherezade) — position-independent PE
- RC4 encrypted converter
- Amber (Ege Balcı)
- Shoggoth (frkngksl)
- Stardust (5pider)

## Layer 3: Behavioral Evasion

### Code Execution / Process Injection (50+ Loaders)
Various loaders organized by evasion scenario — the README references them by number (`-l 1` through `-l 50+`). Each uses different API combinations to avoid behavioral signatures.

### ETW Bypass (3 Methods)

**Method 1: Hot Patch**
```asm
; Overwrite NtTraceEvent entry:
xor rax, rax    ; 48 31 C0
ret              ; C3
; All ETW events silently dropped
```
Detection risk: EDR can detect code modification in ntdll.

**Method 2: VEH Patchless Bypass (from README)**
```
1. Set Vectored Exception Handler
2. Configure HWBP on EtwEventWrite/EtwEventWriteFull using RtlCaptureContext
3. When EtwEventWrite is called → VEH fires
4. In handler: redirect RIP to RET after syscall instruction
5. Set RAX = 0 (success code)
6. ETW event is silently skipped — NO memory modification
```
This is similar to LayeredSyscall's VEH technique but targets ETW specifically.

**Method 3: PG→VEH→VCH Stealth Guard**
Progressive guard chain: page guard → vectored exception handler → vectored continued handler. The most stealthy option.

### Anti-Forensics
- **Self-deletion:** Binary marks itself for deletion on the next reboot (`FILE_FLAG_DELETE_ON_CLOSE`)
- **AmCache wipe:** Delete execution traces from AmCache.hve
- **ShimCache wipe:** Clear ShimCache registry entries
- **Timestomp:** Copy `$STANDARD_INFORMATION` timestamps from legitimate files
- **Zone identifier removal:** Delete Mark of the Web

### Other Techniques
- Parent PID spoofing
- Control Flow Guard/SEHOP/XFG mitigation policy bypass
- API name spoofing via IAT (CallObfuscator)
- DLL/CPL sideloading output
- Threadless execution primitives (VEH→VCH, threadless proxy call stub)

## CLI Usage Example

```bash
python3 Boaz.py -f notepad.exe -o output.exe -t donut -l 16 -e uuid -c akira
# -t donut: PIC shellcode from PE
# -l 16: loader #16
# -e uuid: UUID encoding
# -c akira: Akira LLVM obfuscator
```

## Project Status

No longer actively maintained (README says so). But the technique catalogue is comprehensive and each technique is independently implementable.