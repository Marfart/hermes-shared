---
name: bliiot-crm-tool
description: BLIIOT CRM 跟进记录工具 — 本地SQLite存储 + 双向同步到富通CRM + Excel报表生成。发邮件/WhatsApp/报价时可一键记录跟进。
---

# BLIIOT CRM 跟进记录工具

## 概述

本地SQLite数据库存储客户跟进记录，通过CDP浏览器实时同步到富通CRM (trade.joinf.com)。支持一键添加跟进、查客户历史、生成专业Excel报表。

## 文件结构

```
%LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM/
├── bliiot_crm.py              ← 核心CRM引擎（CLI + Excel生成 + 数据库）
├── crm_quick.py               ← 一键跟进快捷工具
├── sync_all_pending.mjs       ← 批量同步到富通CDP（需要浏览器登录态）
├── all_customers_raw.json     ← 1955条客户原始数据
├── crm_followups.db           ← SQLite跟进记录数据库
└── pending_sync.json          ← 待同步队列
```

## 数据库结构

```sql
-- 跟进记录表
CREATE TABLE followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,           -- 富通CRM客户ID
    customer_name TEXT,                      -- 客户名称（冗余缓存）
    contact_name TEXT,                       -- 联系人姓名
    type TEXT DEFAULT '跟进',                 -- 跟进类型
    content TEXT NOT NULL,                   -- 跟进内容
    operator TEXT DEFAULT 'Kali Marfa',
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    synced INTEGER DEFAULT 0,               -- 0=未同步 1=已同步
    joinf_follow_id TEXT,                   -- 富通CRM返回的跟进ID
    source TEXT DEFAULT 'manual'            -- manual/email/whatsapp/system
);

-- 客户缓存表
CREATE TABLE customer_cache (
    customer_id INTEGER PRIMARY KEY,
    customer_name, contact_name, contact_email,
    contact_mobile, source, grade, region
);
```

## 常用命令

### 从Hermes会话中使用

```python
# 添加跟进记录（本地 + 可选同步到富通）
python bliiot_crm.py add <客户ID> "跟进内容" --type 邮件 --sync

# 按客户名称搜索并查看跟进记录
python crm_quick.py customer "客户名"
python crm_quick.py add-by-name "客户名" "内容" --type WhatsApp --sync

# 查看统计
python crm_quick.py stats

# 刷新Excel报表
python crm_quick.py excel

# 搜索跟进记录
python crm_quick.py search "关键词"
```

### 跟进类型

`跟进` `邮件` `WhatsApp` `电话` `报价` `订单` `会议` `备注` `系统`

## 同步到富通CRM

```bash
cd %LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM
node sync_all_pending.mjs
```

前提：Chrome CDP端口9226已启动+已登录trade.joinf.com

## 同步Payload结构（关键！）

富通CRM的跟进API要求完整字段，Payload结构如下：

```json
{
  "id": "",
  "attachmentList": [],
  "businessStep": 0,
  "customerStep": 0,
  "completeNoRemind": 0,
  "cycleEndDay": "",
  "cycleStartDay": "",
  "cycleId": "",
  "dataType": 0,
  "currentDoneFlag": 0,
  "models": [
    { "columnDisplayName": "Customer Name", "columnName": "dataName", "dict": false,
      "displayOriginalValue": <客户ID>,
      "displayValue": "<客户名称>",         // ← 必须填写！
      "originalValue": "",
      "value": <客户ID>
    },
    { "columnDisplayName": "Contact Name", "columnName": "dataContactName", "dict": false,
      "displayOriginalValue": "", "displayValue": "", "originalValue": "", "value": null
    },
    { "columnDisplayName": "Content", "columnName": "contactContent", "dict": false,
      "displayOriginalValue": "", "displayValue": "", "originalValue": "",
      "value": "[类型] 跟进内容..."
    },
    { "columnDisplayName": "Color", "columnName": "bgColor", "dict": false,
      "displayOriginalValue": "", "displayValue": "", "originalValue": "",
      "value": "2B579A"
    },
    { "columnDisplayName": "Follow Method", "columnName": "method", "dict": true,
      "displayOriginalValue": "", "displayValue": "", "originalValue": "",
      "value": "邮件"
    },
    { "columnDisplayName": "Planning Time", "columnName": "planningTime", "dict": false,
      "displayOriginalValue": "", "displayValue": "", "originalValue": "",
      "value": "2026-06-18 14:37:52"
    },
    { "columnDisplayName": "Feedback Operator", "columnName": "feedbackOperator", "dict": false,
      "displayOriginalValue": "", "displayValue": "", "originalValue": "",
      "value": "183006"
    }
  ],
  "relevantList": [{ "relevantId": "", "relevant": "" }],
  "flowStep": "",
  "forceRefresh": true,
  "followType": "",
  "followObject": ""
}
```

## Excel报表

4个Sheet：客户总览、全部客户数据（含跟进统计列）、业务员统计、国家地区统计、跟进记录明细

生成方式：
```bash
python bliiot_crm.py generate-excel
```
输出到 `Desktop/Working/BLIIOT_富通CRM_客户数据全量报表.xlsx`

## 已知问题

1. CDP浏览器会话可能断连，需要重新启动Chrome并登录
2. 同步需要富通CRM页面在活动标签页（Vue SPA需要）
3. 客户名称中文显示问题：displayValue必须填客户名称，不能只填ID