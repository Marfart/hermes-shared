"""Create SNMP lesson note in Obsidian"""
import subprocess, sys

script = r'C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py'
category = 'Hermes技能'  # SNMP is a protocol/hacking topic
title = 'SNMP協議完全入門'
content = """# SNMP 協議完全入門

> 📅 2026-06-08 | #SNMP #協議 #網絡安全 #滲透測試

---

## 📌 目錄

1. [SNMP 是什麼](#1-snmp-是什麼)
2. [為什麼要學 SNMP](#2-為什麼要學-snmp)
3. [SNMP 架構：Manager + Agent + MIB](#3-snmp-架構)
4. [版本演進：v1 → v2c → v3](#4-版本演進)
5. [MIB & OID：SNMP 的檔案系統](#5-mib--oid)
6. [協議操作：5 種 PDU](#6-協議操作)
7. [BER 編碼：線上有什麼](#7-ber-編碼)
8. [安全視角：為什麼 SNMP 是滲透金礦](#8-安全視角)
9. [實戰：安裝 net-snmp + 掃內網](#9-實戰)
10. [參考資料](#10-參考資料)

---

## 1. SNMP 是什麼

**Simple Network Management Protocol** — 1988 年發明的網路管理協議。

核心思想：**用一個統一的協議管理所有網路設備**。
不管你是 Cisco 路由器、華為交換機、HP 打印機、還是 BLIIOT 工業網關，都透過 SNMP 同一個接口查狀態。

## 2. 為什麼要學 SNMP

| 場景 | 意義 |
|:----|:-----|
| 網路監控 | Zabbix / Prometheus 用 SNMP 收集所有設備指標 |
| 設備發現 | 掃網段就知道有哪些設備、什麼型號、跑什麼系統 |
| 滲透測試 | v2c 明文傳 community string，設備量巨大 |
| 工業物聯網 | BLIIOT 網關支援 SNMP，現場大量部署 |
| 故障排查 | 一秒查出設備 uptime、CPU 負載、介面流量 |

## 3. SNMP 架構

```
Manager ──── GET/WALK ──────→ Agent（UDP 161）
         ←── RESPONSE ──────
         ──── SET ──────────→ （修改設備配置）
         ←── TRAP ────────── （非同步警報，UDP 162）
```

**Manager**（管理者）：輪詢端，如 Zabbix、Cacti、你自己的腳本
**Agent**（代理）：運行在受管設備上的守護進程
**MIB**（Management Information Base）：OID 樹的定義檔

## 4. 版本演進

| 版本 | 認證 | 加密 | 實際佔比 | 說明 |
|:----|:-----|:-----|:---------|:-----|
| v1 (1988) | 明文字串 | ❌ | 極少 | 已淘汰 |
| **v2c** (1993) | 明文字串 | ❌ | **~90%** | 加了 GetBulkRequest |
| v3 (2002) | USM 用戶名+密碼 | AES/DES | ~5% | 配置複雜，支援設備少 |

**殘酷現實**：95% 的 SNMP 跑 v2c，預設 community 是 `public`（唯讀）/ `private`（讀寫）。

## 5. MIB & OID

**OID**（Object Identifier） = SNMP 的檔案路徑：

```
1.3.6.1.2.1.1.5.0  = sysName.0（設備主機名）
1.3.6.1.2.1.1.1.0  = sysDescr.0（設備描述）
1.3.6.1.2.1.2.2.1.2 = ifDescr（介面名稱列表）
```

**MIB** = 把 OID 數字翻譯成人類可讀名稱的字典。

OID 樹狀結構：
```
ISO(1)
└── ORG(3)
    └── DOD(6)
        └── INTERNET(1)
            ├── mgmt(2)
            │   └── mib-2(1)  ← 標準MIB（所有設備都支援）
            ├── private(4)
            │   └── enterprises(1)  ← 廠商自定義
            │       ├── cisco(9)
            │       ├── huawei(2011)
            │       └── ...
```

**mib-2**（1.3.6.1.2.1）下有 10+ 個必實現的組：
- system (1) — 設備名稱、描述、位置、Uptime
- interfaces (2) — 所有網路介面、IP、MAC
- ip (4) — IP 層統計
- icmp (5) — ICMP 統計
- tcp (6) — TCP 連接
- udp (7) — UDP 統計

## 6. 協議操作

| PDU 類型 | 操作 | 用途 |
|:---------|:-----|:------|
| GetRequest (0xA0) | 取單個 OID | 查特定值 |
| GetNextRequest (0xA1) | 取下一個 OID | WALK 的核心原語 |
| GetResponse (0xA2) | 回覆 | Agent 對所有請求的回應 |
| SetRequest (0xA3) | 寫入 OID | 修改設備配置 |
| GetBulkRequest (0xA5) | 批量取 N 行 | v2c 新增，加速 WALK |

**WALK 演算法**（一步步遍歷整棵樹）：
```
1. 發 GetNextRequest(起始OID)
2. 收到下一個OID的值
3. 用收到的OID作為新起點，重複
4. 直到OID不在目標子樹內 → 結束
```

## 7. BER 編碼（底層）

SNMP 在 UDP 上的資料格式是 **BER**（Basic Encoding Rules）。

每個欄位編碼為 TLV 三元組：**Tag + Length + Value**

Tag 類型：
- 0x02 = INTEGER
- 0x04 = OCTET STRING（字串）
- 0x05 = NULL
- 0x06 = OBJECT IDENTIFIER
- 0x30 = SEQUENCE（容器）
- **0xA0~0xA5** = SNMP 特定 PDU 類型

**關鍵坑**：SNMP PDU 必須用 context-specific tag（0xA0~0xA5），不能用通用的 0x30（Sequence）！
這也是初學者寫自定義 SNMP 程式最常犯的錯誤。

## 8. 安全視角

一次成功的 `snmpwalk -c public` 可以洩漏：

### 可以拿到的資料
- 完整系統描述（型號、韌體版本）
- 所有網路介面的 IP/MAC/路由表
- 運行中的進程和安裝的軟體
- 用戶帳號列表（部分設備）
- 廠商專有 MIB 數據

### 有 write 權限（private）可以做的事
- 修改主機名、位置（偽裝）
- 重啟介面（DoS）
- 部分設備可透過企業 MIB 執行命令

### 實際攻擊場景
1. 掃 UDP 161 開放端口
2. 暴力破解 community string（public/private/snmp/admin...）
3. snmpwalk 全樹 dump
4. 提取系統資訊、路由表、ARP 表
5. 橫向移動的跳板

## 9. 實戰工具

| 工具 | 用途 |
|:----|:-----|
| snmpwalk | 遍歷 OID 樹 |
| snmpget | 取單個 OID |
| snmpbulkwalk | 批量遍歷（更快） |
| snmpset | 寫入 OID |
| nmap -sU -p 161 | 掃描 SNMP 開放端口 |
| onesixtyone | 快速暴力 community string |
| pysnmp (Python) | 自己寫 SNMP 客戶端/代理 |

---

> 🐾 小馬陪學筆記 | 下一堂：實戰安裝 net-snmp + 掃內網看看有什麼設備
"""

subprocess.run([
    'python', script, 'create', category, title, content
], capture_output=True, text=True)
print("Note created successfully")
