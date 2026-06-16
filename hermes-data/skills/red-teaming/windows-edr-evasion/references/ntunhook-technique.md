# Selective ntdll Unhooking — Source Analysis

**Repo:** `S12cybersecurity/NtUnhook`
**Files Read:** README.md

## Core Concept

Spawn a suspended child process (which loads a clean, unhooked ntdll.dll), read that clean ntdll from the child's memory, then selectively overwrite only the hooked syscall stubs in the current process. Zero file I/O, minimal memory changes.

## 6-Step Algorithm

### Step 1: Spawn Suspended Process
```cpp
CreateProcess(
    "C:\\Windows\\System32\\cmd.exe",
    ...,
    CREATE_SUSPENDED,     // ← key: suspended = ntdll loaded but no code runs
    &pi
);
```
Child process loads a clean ntdll.dll from disk — no EDR hooks applied yet.

### Step 2: Read Clean ntdll
```cpp
// Find ntdll base address in child process
HMODULE hNtdll = GetModuleHandle("ntdll.dll");
MODULEINFO mi;
GetModuleInformation(GetCurrentProcess(), hNtdll, &mi, sizeof(mi));

// Read full ntdll image from child
BYTE* cleanBuffer = malloc(mi.SizeOfImage);
ReadProcessMemory(hChildProcess, childNtdllBase, cleanBuffer, mi.SizeOfImage, NULL);
```

### Step 3: Parse Export Tables
Both the clean image and current process's ntdll are parsed for their export directories. Only functions starting with "Nt" are candidates.

### Step 4: Identify Syscall Stubs
The 23-byte syscall prologue pattern:
```asm
mov r10, rcx          ; 4C 8B D1
mov eax, <SSN>        ; B8 XX XX XX XX
syscall                ; 0F 05
ret                    ; C3
```
Total: 4 + 5 + 2 + 1 = 12 bytes minimum, but the full stub with alignment padding is 23 bytes.

### Step 5: Selective Overwrite
```cpp
// For each Nt* function in both clean and current:
for each export in both images:
    if is_Nt_function and needs_restore:
        // Enable write access
        VirtualProtect(current_addr, 23, PAGE_EXECUTE_READWRITE, &old);
        // Copy clean stub over hooked stub
        memcpy(current_addr, clean_addr, 23);
        // Restore protection
        VirtualProtect(current_addr, 23, PAGE_EXECUTE_READ, &old);
```

**Two modes:**
1. `UnhookDetectedHooks` — scan current stubs, detect hooks by comparing to clean stubs byte-by-byte, only restore mismatched ones
2. `UnhookDesiredHooks` — always restore specific functions regardless of hook state

### Step 6: Cleanup
```cpp
TerminateProcess(hChildProcess, 0);
CloseHandle(hChildProcess);
```

## Comparison — Why This Approach

| Technique | How It Gets Clean ntdll | Detection Risk |
|-----------|------------------------|----------------|
| Load clean DLL from disk | ReadFile from known-dlls directory | HIGH — file I/O monitoring |
| Hell's Gate | Assume ntdll stubs are intact | MEDIUM — broken on hooked systems |
| Perun's Fart | Suspended process + read memory | LOW — requires child process |
| **NtUnhook** | Suspended process + selective restore | VERY LOW — minimal changes |

## Pitfalls

- Child process must be same architecture (x64 child for x64 parent)
- NtCreateUserProcess without proper PS_ATTRIBUTE_LIST setup will crash
- Only restores ntdll — EDR also hooks other DLLs (amsi.dll, kernel32.dll, etc.)
- Windows 10 22H2 tested, may need adjustment for Win11 24H2+ (different ntdll layout)