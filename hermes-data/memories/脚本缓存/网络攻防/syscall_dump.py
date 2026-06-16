#!/usr/bin/env python3
"""
syscall_dump.py — 直接从内存读取ntdll的NT API syscall号
用ctypes.GetProcAddress获取函数地址 → 读前16字节 → 解析syscall号

原理: 每个ntdll的NT函数开头都是:
  mov r10, rcx        ; 4C 8B D1
  mov eax, SS#       ; B8 XX XX XX XX  ← 这里就是syscall号
  syscall              ; 0F 05
  ret                  ; C3
"""
import ctypes
from ctypes import wintypes
import struct

def get_syscall_number(func_addr):
    """从NT函数地址解析syscall号"""
    # 读取前16字节
    buf = (ctypes.c_ubyte * 16)()
    ctypes.memmove(buf, func_addr, 16)
    stub = bytes(buf)
    
    # x64标准模式: 4C 8B D1 (mov r10, rcx) + B8 XX XX XX XX (mov eax, imm32)
    if stub[0:3] == b"\x4C\x8B\xD1" and stub[3] == 0xB8:
        syscall_num = struct.unpack("<I", stub[4:8])[0]
        return syscall_num, stub[:13]  # mov r10,rcx + mov eax,SS + syscall + ret
    
    return None, stub

def main():
    ntdll = ctypes.windll.ntdll
    kernel32 = ctypes.windll.kernel32
    
    key_funcs = [
        "NtAllocateVirtualMemory", "NtProtectVirtualMemory", "NtWriteVirtualMemory",
        "NtCreateThreadEx", "NtOpenProcess", "NtCreateFile",
        "NtOpenFile", "NtReadFile", "NtWriteFile",
        "NtCreateUserProcess", "NtSuspendProcess", "NtResumeProcess",
        "NtQuerySystemInformation", "NtQueryInformationProcess",
        "NtSetInformationProcess", "NtClose",
        "NtCreateSection", "NtMapViewOfSection", "NtUnmapViewOfSection",
        "NtCreateKey", "NtOpenKey", "NtQueryValueKey",
        "NtCreateToken", "NtOpenProcessToken",
        "NtWaitForSingleObject", "NtDelayExecution",
        "NtRaiseHardError", "NtShutdownSystem",
        "NtCreateThread", "NtOpenThread",
    ]
    
    print("=" * 72)
    print(f"{'NT API':40s} {'Syscall#':>8s}  {'Signature'}")
    print("=" * 72)
    
    for name in key_funcs:
        try:
            func = getattr(ntdll, name)
            addr = ctypes.cast(func, ctypes.c_void_p).value
            if not addr:
                continue
            
            syscall_num, stub = get_syscall_number(addr)
            
            if syscall_num is not None:
                sig = " ".join(f"{b:02X}" for b in stub[:6])
                print(f"  {name:38s}  {syscall_num:3d}    {sig}")
            else:
                # 可能被hook了，显示前几个字节
                sig = " ".join(f"{b:02X}" for b in stub[:8])
                print(f"  {name:38s}  HOOKED  {sig}")
                
        except AttributeError:
            pass

if __name__ == "__main__":
    main()