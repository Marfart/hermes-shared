---
name: bliiot-crm-followup
description: BLIIOT 富通CRM 跟进记录工具 — 本地SQLite+富通API双向同步，支持一键添加跟进、查客户、生成Excel报表
---

# BLIIOT CRM 跟进记录工具

## 概述

本地 SQLite 数据库 + 富通CRM API 双向同步工具。发邮件/WhatsApp/报价时自动记录跟进，一键同步到富通CRM，随时生成完整Excel报表。

## 文件位置

```
%LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM/
├── bliiot_crm.py           ← 主程序（数据库+Excel生成+CLI）
├── crm_quick.py            ← 快捷工具（按名字查客户+加跟进）
├── sync_all_pending.mjs    ← CDP同步脚本（批量跑跟进到富通）
├── sync_to_joinf.cjs       ← 单条CDP同步脚本
├── crm_followups.db        ← SQLite数据库
├── all_customers_raw.json  ← 原始客户数据（1955条）
└── pending_sync.json       ← 待同步队列
```

## 使用方法

### 添加跟进记录

```bash
# 用客户ID
python bliiot_crm.py add 235327923 "发了BL460报价，客户说下周回复" --type 邮件 --sync

# 用客户名称（模糊匹配）
python crm_quick.py add-by-name "hsinsight" "WhatsApp联系，已读产品资料" --type WhatsApp --sync
```

### 查询客户+跟进历史

```bash
python crm_quick.py customer "hsinsight"
# 输出：客户信息+所有跟进记录（ID/时间/类型/内容/同步状态）
```

### 统计与Excel

```bash
python bliiot_crm.py stats           # 跟进统计
python bliiot_crm.py generate-excel  # 生成完整Excel（5个Sheet）
python crm_quick.py search "关键词"   # 搜索跟进记录
```

### 同步待处理记录到富通

```bash
# 先确保Chrome CDP 9226端口运行中，已登录trade.joinf.com
cd %LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM
node sync_all_pending.mjs
```

## 跟进类型

`跟进`, `邮件`, `WhatsApp`, `电话`, `报价`, `订单`, `会议`, `备注`, `系统`

## 双向同步机制

```
本地 add() → SQLite(synced=0)
  ↓
sync_all_pending.mjs → CDP POST /rapi/m/follow/add
  ↓
富通CRM 成功 → UPDATE synced=1
  ↓
富通CRM 失败 → 保留 synced=0 待重试
```

## API 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| companyId | 71376 | 公司ID |
| operatorId | 183006 | 操作员ID (bliiot03) |
| xCid | 71376 | Header X-Cid |
| xUser | 183006 | Header X-User |
| baseUrl | https://trade.joinf.com | API 基础 URL |

## 跟进记录格式（富通API）

```json
POST /rapi/m/follow/add
{
  "models": [
    { "columnName": "dataName", "value": 235327923 },
    { "columnName": "contactContent", "value": "[邮件] 发了BL460报价..." },
    { "columnName": "bgColor", "value": "2B579A" },
    { "columnName": "method", "value": "邮件" },
    { "columnName": "feedbackOperator", "value": "183006" },
    { "columnName": "planningTime", "value": "2026-06-18 15:08" }
  ],
  "forceRefresh": true
}
```

## Excel 报表结构（5个Sheet）

| Sheet | 内容 |
|-------|------|
| 客户总览 | KPI卡片+等级分布+来源Top15+国家Top20 |
| 全部客户数据 | 1955行×36列（含本地跟进次数/时间/摘要） |
| 业务员统计 | 每人客户数/跟进率/邮箱率/手机率 |
| 国家地区统计 | 147个国家覆盖+跟进深度 |
| 跟进记录明细 | 全部跟进记录（类型/内容/同步状态） |

## 关键铁则

1. **先查后增** — 加跟进前用 `crm_quick.py customer` 确认客户存在
2. **同步前需开CDP** — Chrome `--remote-debugging-port=9226 --profile-directory=Profile 2`，已登录trade.joinf.com
3. **双写确认** — 本地SQLite先写 + `--sync` 参数同步到富通API
4. **displayValue必填客户名称** — 富通Vue组件依赖`dataName.displayValue`渲染跟进详情，空字符串会导致记录显示在时间轴但点进去内容为空。`displayValue`必须传客户名称（对应`customer_name`字段）
5. **黑白颜色映射** — 邮件=2B579A(蓝), WhatsApp=27AE60(绿), 报价=E67E22(橙), 电话=E74C3C(红), 默认=fe4145
6. **planningTime格式** — 必须用本地时间字符串 `YYYY-MM-DD HH:mm:ss`，不要用ISO格式
7. **永久存储** — SQLite + JSON双重保险
8. **Excel刷新** — 每次新加跟进后运行 `generate-excel` 或 `crm_quick.py excel` 刷新报表

## 常见Bug排查

| 现象 | 原因 | 修复 |
|------|------|------|
| 时间轴有记录但点进去空白 | `dataName.displayValue` 为空 | 传`customer_name`给`displayValue` |
| 多条记录时间戳相同 | `planningTime` 用默认值 | 同步前从DB读出`created_at` |
| 返回"系统繁忙" | Cookie过期或未登录 | 重新登录富通 + 刷新页面 |
| 跟进类型不显示 | `method.dict=true` 但值不对 | 确保值匹配富通字典表 |

## 调试参考

完整的 payload 调试记录和 #5-#14 修复详情见：
`references/joinf-followup-payload.md`