# 网络攻防深度学习成果
## 2026-06-04

## 源码研读项目

### 1. fortra/impacket (15.8k⭐)
https://github.com/fortra/impacket

**学到什么：**
- SMB1/2/3 协议多版本透明切换模式
- NTLM 认证握手（compute_lmhash / compute_nthash）
- NetBIOS 名称解析 + SMB 直连（端口445 vs 139）双通道架构
- secretsdump 中的 DC 同步（DRSUAPI）远程提取哈希
- smbexec 中的服务控制管理器远程命令执行
- 异常体系：SessionError 统一封装底层网络错误

**核心设计模式：**
- 连接器模式（negotiateSession 自动协商最高协议）
- 回退机制（SMB1 → SMB2 → SMB3 逐级尝试）
- 异常链（低层 socket 错误 → SessionError 统一包装）

### 2. Gallopsled/pwntools (13.5k⭐)
https://github.com/Gallopsled/pwntools

**学到什么：**
- tube 基类 + sock/remote/listen/process 继承体系
- recv_raw 中的 errno 精准分类（EAGAIN=重试、ECONNRESET=断连、EINTR=中断重试）
- ROP 链构造器：Gadget 发现、地址自动对齐、badchars 过滤
- shellcraft 模块化 shellcode 生成
- context 全局配置系统

**核心设计模式：**
- 管道抽象（统一 recv/send/connect/close 接口）
- 延迟加载（__getattr__ 动态发现 gadget）
- self.closed 双工关闭状态（recv 和 send 独立跟踪）

### 3. 1N3/Sn1per (10k⭐)
https://github.com/1N3/Sn1per

**学到什么：**
- 模块化攻击面管理架构
- 90+ 第三方工具编排调度引擎
- recon → enum → exploit → post 流水线模式

### 4. MRxO11/RedOps
https://github.com/MRxO11/RedOps

**学到什么：**
- 终端 UI 框架 + Nmap/Metasploit/Nuclei 集成
- 多工具结果聚合管道

## 提取的精华模式

1. **errno 精准分类** — 替代 bare except
2. **双工关闭状态** — recv/send 独立跟踪
3. **连接器模式** — 自动协商最高协议版本
4. **EAFP 异常扫描** — 端口/IP 扫描不走 ping
5. **Retry 迭代器** — yt-dlp 风格的重试管理器
6. **延迟加载发现** — __getattr__ 动态注入属性

## 脚本清单

| 脚本 | 说明 | 来源 |
|:----|:-----|:-----|
| port_scanner.py | 异步 TCP 端口扫描器（非阻塞+超时+服务识别） | impacket + pwntools |
| network_recon.py | 局域网设备发现+端口扫描+服务指纹识别一体工具 | Sn1per + RedOps |
