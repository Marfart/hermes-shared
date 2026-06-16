---
name: portwatch-scanner
description: 👁️ PortWatch — 远程端口监控器。多线程端口扫描、变化检测、HTTP可用性监控、持续监控模式
---

# 👁️ PortWatch — 远程端口监控器

## 文件位置
- 脚本：`%LOCALAPPDATA%\hermes\memories\脚本缓存\网络攻防\portwatch.py`
- 状态文件：`%LOCALAPPDATA%\hermes\memories\scripts_cache\portwatch_state.json`

## 功能
- 多线程TCP端口扫描（默认200并发）
- 端口变化检测（对比历史状态，发现新增/关闭端口）
- HTTP服务可用性监控
- 持续监控模式（循环扫描+变化告警）
- 高风险端口自动标注（135/139/445/3389/5900/5985/5986）
- 常见服务识别（22=SSH, 80=HTTP, 443=HTTPS, 3306=MySQL等30+种）
- 状态持久化到JSON文件，跨会话可查历史

## 用法

### 扫描端口范围
```bash
python portwatch.py scan 目标IP 1-1024
```

### 持续监控关键端口
```bash
python portwatch.py watch 目标IP 22,80,443,3389 --interval 60
```

### 单次扫描（不持续）
```bash
python portwatch.py watch 目标IP 1-100 --once
```

### HTTP服务监控
```bash
python portwatch.py http://example.com
python portwatch.py http://example.com --interval 10
python portwatch.py http://example.com --once
```

### 查看历史状态
```bash
python portwatch.py status
```

## 关键参数
| 参数 | 说明 |
|------|------|
| `scan` | 单次扫描命令 |
| `watch` | 持续监控命令 |
| `status` | 查看历史状态 |
| `--interval/-i` | 监控间隔秒数（默认60） |
| `--threads/-t` | 并发线程数（默认200） |
| `--timeout` | 单端口超时秒数（默认2） |
| `--once` | 仅扫描一次 |

## 端口范围语法
- `1-1000` — 范围
- `22,80,443` — 列表
- `1-1024,3389,8080-8090` — 混合

## 实测性能
- 1000端口扫描 → ~6秒完成
- 4端口扫描 → 秒级
- 本地发现：RPC(135)⚠️ + SMB(445)⚠️ + Flask(5000/5001)

## 延伸用途
- BLIIOT设备出厂端口安全审计（扫描哪些端口不该开）
- 客户网络设备暴露面评估
- 内网资产自动发现
- 网关漏洞攻击面缩小（关掉不必要的服务）