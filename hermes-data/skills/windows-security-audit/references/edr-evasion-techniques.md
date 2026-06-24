# EDR/AV 绕过技术 (源码级)

## 1. VEH + 硬件断点系统调用拦截
**来源**: WKL-Sec/LayeredSyscall

工作原理:
```
正常: UserCode → ntdll!Nt* → syscall → Kernel
EDR:  UserCode → ntdll!Nt* → EDR hook → syscall
拦截:  VEH在syscall边界拦截, 伪造调用栈
```

关键实现:
1. GetProcAddress获取真实Nt*函数
2. 遍历.text字节找0x0F 0x05 (syscall) 和ret操作码
3. Dr0=syscall地址, Dr1=ret地址 (硬件断点)
4. EXCEPTION_SINGLE_STEP触发时:
   - 保存寄存器上下文
   - 改变RIP到合法API(如MessageBoxA)
   - 设置TraceFlag单步执行ntdll
5. 在ntdll内找到合法调用帧
6. 恢复上下文 → Rax=真实SSN → 跳转到syscall操作码

SSN解析: 遍历ntdll异常目录(RUNTIME_FUNCTION), 对每个Zw开头的函数计数。

## 2. 选择性ntdll解钩(无文件)
**来源**: S12cybersecurity/NtUnhook

6步流程:
1. CreateProcess(CREATE_SUSPENDED) → 子进程加载干净ntdll
2. ReadProcessMemory(子进程, ntdll_base)
3. 解析导出表: 获取所有Nt*名称+RVA
4. 找23字节syscall stub模式
5. 按RVA匹配 → VirtualProtect(PAGE_RWX) → memcpy干净stub
6. 终止子进程

## 3. 间接syscalls (Havoc Demon)
```
代替: mov r10,rcx; mov eax,SSN; syscall; ret  ← 自己的代码
执行: mov r10,rcx; mov eax,SSN; jmp [ntdll_addr+offset]  ← RIP在ntdll
```

## 4. BOAZ多层规避
**来源**: thomasxm/BOAZ_beta (BlackHat USA 2024)

三层架构:
| 层 | 绕过什么 | 技术 |
|----|---------|------|
| 签名 | 静态AV | 10种编码+LLVM IR混淆 |
| 启发式 | 沙箱 | 反仿真检查+API解钩+睡眠掩码 |
| 行为 | EDR监控 | 50+加载器+ETW绕过+PPID欺骗 |

ETW绕过3种方法:
1. 热补丁 (写XOR RAX,RAX; RET覆盖NtTraceEvent)
2. VEH硬件断点(无补丁)
3. Page guard → VEH → VCH隐身守卫

## 5. AMSI绕过(跨进程Python)
Python进程不受AMSI扫描。独立Python脚本:
```python
import ctypes
# OpenProcess → VirtualProtect → WriteProcessMemory
# Patch amsi.dll!AmsiScanBuffer前3字节: mov eax,1; ret
```

## 6. ntdll系统调用发现(Python)
读取ntdll导出表, 枚举所有Nt*函数按VA排序 → SSN是索引。

## 常见陷阱
- 当前机器ntdll已干净
- 需要C++编译器(mingw-w64)编译大部分技术
- Python EDR工具只因为Python本身不被扫描
- TraceFlag单步很慢 — 只用于syscall调用
- VEH处理程序必须作为第一个(不是最后一个)添加
