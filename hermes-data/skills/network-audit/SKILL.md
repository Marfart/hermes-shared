---
name: network-audit
description: "网络审计工具集 — 端口扫描、SNMP扫描、暴力破解测试、摄像头发现。覆盖网络安全评估的常见扫描和审计工具链。"
version: 1.0.0
author: Hermes Agent (Kali)
tags: [network, security, audit, scanning, snmp, portscan, brute-force, camera]
triggers:
  - "端口扫描"
  - "SNMP扫描"
  - "暴力破解"
  - "摄像头发现"
  - "网络审计"
  - "port scan"
  - "network scan"
---

# 网络审计工具集

> 端口扫描、协议扫描、弱口令测试、设备发现的完整工具链。

## 工具清单

| 工具 | 功能 | 位置 |
|------|------|------|
| **PortWatch** | 多线程端口扫描+变化检测+HTTP监控 | `memories/脚本缓存/网络攻防/portwatch.py` |
| **SNMP** | SNMP协议扫描/walk/安全审计 | Python脚本 + pysnmp |
| **PyHydra** | HTTP/SSH暴力破解引擎 | `memories/脚本缓存/网络攻防/pyhydra.py` |
| **Camera Recon** | 三层摄像头发现(本机+局域网+公网) | 见 red-teaming/camera-reconnaissance |

## PortWatch — 端口扫描

### 功能
- 多线程TCP端口扫描（默认200并发）
- 端口变化检测
- HTTP服务可用性监控
- 高风险端口标注
- 状态持久化

### 用法
```bash
python portwatch.py scan 目标IP 1-1024
python portwatch.py watch 目标IP 22,80,443,3389 --interval 60
python portwatch.py status
```

## SNMP — 协议扫描

### 功能
- SNMPv1/v2c/v3协议操作
- BER编码/解码
- pysnmp实现
- Walk算法
- 安全审计

### 版本分布
- v2c: ~90% (明文community)
- v3: ~5% (USM加密)

### 安全审计要点
- `snmpwalk -c public` 可泄漏: 系统信息/接口/IP/进程/用户
- `private` community = 写权限 = 可修改配置

## PyHydra — 暴力破解

### 功能
- HTTP POST/GET表单爆破
- SSH端口扫描
- 多线程（4-200线程）
- 进度条+速率显示
- 内建字典

### 用法
```bash
python pyhydra.py http-form://目标/ -F "错误" -S "成功"
python pyhydra.py ssh://10.0.0.1 -U users.txt -P passwords.txt
```

### 实测性能
- 120组合 → 0.3秒 (347次/秒)

## Camera Recon — 摄像头发现

详见 `red-teaming/camera-reconnaissance` 技能。

三层扫描:
1. 本机设备枚举 (PnP Camera)
2. 局域网IP摄像头 (RTSP/ONVIF/HTTP)
3. 公网OSINT (Shodan/Insecam/Google Dorks)

## 使用原则

- **安全/黑客研究与BLIIOT业务绝对隔离**
- 只在授权网络上测试
- 靶场测试优先
- 工厂设备默认密码审计需要客户授权

## 关联技能

- `windows-security-audit` — Windows系统安全审计
- `portwatch-scanner` → 见PortWatch部分
- `snmp` → 见SNMP部分
- `pyhydra-brute-force` → 见PyHydra部分
