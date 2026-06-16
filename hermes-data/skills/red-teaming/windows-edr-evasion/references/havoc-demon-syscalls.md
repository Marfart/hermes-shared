# Havoc C2 Demon — Agent Architecture

**Repo:** `HavocFramework/Havoc`
**Files Read:** WIKI.MD (full agent architecture)
**Agent Source Directory:** `Havoc/payloads/Demon/Source/`

## Demon Agent Layout

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `Source/Asm` | Assembly — return address stack spoofing | `.asm` files for x64 |
| `Source/Core` | Core — transport layer, Win32 API wrappers, syscall logic | `Syscalls.c`, `Transport.c`, `Win32.c` |
| `Source/Crypt` | AES encryption for C2 traffic | AES implementation |
| `Source/Extra` | KaynLdr — reflective DLL loader | |
| `Source/Inject` | Process injection functions | |
| `Source/Loader` | COFF Loader + Beacon API | Compatible with Cobalt Strike BOFs |
| `Source/Main` | Entry points — PE (.exe), DLL, RDLL | |

## Indirect Syscall Implementation

Build-time generated. When compiled with `OBF_SYSCALL` flag:

### Step 1: Read clean ntdll from disk
Syscall stubs are dynamically crafted from `ntdll.dll` on disk at compile time.

### Step 2: Modify return address
The return address of each syscall is forged to point to `ntdll!NtAddBootEntry (0x180024b6)`.

### Step 3: Indirect call pattern
```asm
; Instead of executing syscall in our own code:
mov r10, rcx
mov eax, SSN
syscall          ; ← RIP is in our .text section → EDR detects us
ret

; Do this (indirect):
mov r10, rcx
mov eax, SSN
jmp [ntdll_syscall_addr]  ; ← RIP appears to be in ntdll
; The syscall executes from ntdll's memory region
; Return address points to ntdll!NtAddBootEntry
```

## Sleep Mask Techniques

Three techniques selectable via profile config:

| ID | Technique | Mechanism |
|----|-----------|-----------|
| 0 | WaitForSingleObjectEx | No obfuscation — just sleep |
| 1 | FOLIAGE | Obfuscate during sleep |
| 2 | Ekko | Timer-based sleep with encryption |

During sleep (with masking enabled):
1. No active job threads running
2. Encrypt agent memory with session key
3. Return address spoofing hides the real call chain
4. Wait for delay period
5. Decrypt memory
6. Check-in to teamserver

## C2 Transport

### Listener Configuration (yaotl profile format)
```hcl
Listeners {
    Http {
        Name = "HTTPS Listener"
        Hosts = ["10.0.0.10"]
        PortBind = 443
        Method = "POST"
        Secure = true
        Uris = ["/funny_cat.gif", "/index.php", "/test.txt"]
        Headers = ["X-Havoc: true"]
        Response {
            Headers = ["Content-type: text/plain"]
        }
    }
}
```

### Supported Channels
- HTTP/HTTPS (primary)
- ExternalC2 (custom channel support)

### Key Profile Options
- `KillDate` — Agent terminates itself at specified UTC time
- `WorkingHours` — Only check-in during specified hours (defensive evasion)
- `Jitter` — Randomized sleep percentage to avoid pattern detection

## Evasion Features

1. **Indirect syscalls** (OBF_SYSCALL compile flag)
2. **Return address spoofing** — Assembly-level stack manipulation
3. **Sleep mask obfuscation** — 3 techniques
4. **Per-binary asymmetric keys** — Each generated implant has unique crypto keys
5. **Dynamic code generation** — Implant compiled per-session
6. **COFF/BOF in-memory loader** — Run Cobalt Strike BOFs without touching disk

## Pitfalls

- Source code is in `teamserver/data/implants/Demon/` directory (teamserver-generated)
- Not on raw github at `payloads/Demon/` — that directory exists at build time
- Syscalls.c is built by the teamserver's `builder` class with compile flags
- `--debug-dev` adds `-D DEBUG` flag, removes `-nostdlib`, links stdlib → larger binary