---
name: bliiot-crm-followup
description: BLIIOT 富通CRM 跟进记录工具 — 本地SQLite+富通API双向同步，支持一键添加跟进、查客户、生成Excel报表
---

# BLIIOT CRM 跟进记录工具

## 概述

本地 SQLite 数据库 + 富通CRM API 双向同步工具。发邮件/WhatsApp/报价时自动记录跟进，一键同步到富通CRM，随时生成完整Excel报表。

## 文件清单

```
%LOCALAPPDATA%/hermes/memories/脚本缓存/富通CRM/
├── bliiot_crm.py             ← 主程序（DB管理+Excel生成+CLI）
├── crm_quick.py              ← 快捷工具（按名字查客户+加跟进）
├── sync_all_pending.mjs      ← CDP批量同步（主入口，建议只用这个）
├── sync_to_joinf.cjs         ← 单条同步（被bliiot_crm.py调用）
├── sync_to_joinf.mjs         ← 单条同步（旧版）
├── sync_to_joinf.py          ← 单条同步（Python版）
├── bliiot_crm_sync.cjs       ← Node.js完全同步工具
├── bliiot_crm_sync.mjs       ← ES module版同步工具
├── crm_followups.db          ← SQLite数据库
├── all_customers_raw.json    ← 富通原始客户数据（1955条）
├── pending_sync.json         ← 待同步队列
├── generate_excel.py         ← Excel报表生成器
├── fetch_all_customers.mjs   ← 从富通CDP拉取客户数据
└── all_customers_raw.json    ← 客户数据缓存
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
富通CRM 成功 → UPDATE followups SET synced=1 WHERE id=? (写SQLite)
                    ↓
               pending_sync.json (同步写)
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

## 跟进记录Payload（富通API）

```json
POST /rapi/m/follow/add
{
  "models": [
    { "columnName": "dataName", "value": 235327923,
      "displayValue": "客户名称",        // ← 必填！空了点进去看不到
      "displayOriginalValue": 235327923 },
    { "columnName": "contactContent", "value": "[邮件] 发了BL460报价..." },
    { "columnName": "bgColor", "value": "2B579A" },
    { "columnName": "method", "dict": true, "value": "邮件" },
    { "columnName": "feedbackOperator", "value": "183006" },
    { "columnName": "planningTime", "value": "2026-06-18 15:08:06" }
  ],
  "forceRefresh": true
}
```

### GitHub 共享仓库同步注意事项

CRM 工具数据同步到 `Marfart/hermes-shared` 仓库时注意两个防线：

1. **`.gitignore`** 默认禁止 `*.db` — CRM 数据库 `crm_followups.db` 会被排除。已在 `.gitignore` 末尾加 `!*.db` 覆盖。
2. **`github_shared_sync.py` 的 `EXCLUDE_EXT`** 默认包含 `.db` — 已在 `github_shared_sync.py` 第38行移除。
3. **`all_customers_raw.json`（6.4MB）** 需要 `git add -f` 强制追踪。
4. 检查缺失文件：运行 `diff -r` 或 `find` 对比本地和共享仓库的文件计数，确保所有 `.py` `.mjs` `.cjs` 都在。

## Excel 报表结构（5个Sheet）

| Sheet | 内容 |
|-------|------|
| 客户总览 | KPI卡片+等级分布+来源Top15+国家Top20 |
| 全部客户数据 | 1955行×36列（含本地跟进次数/时间/摘要） |
| 业务员统计 | 每人客户数/跟进率/邮箱率/手机率 |
| 国家地区统计 | 147个国家覆盖+跟进深度 |
| 跟进记录明细 | 全部跟进记录（类型/内容/同步状态） |

## 自动跟进记录（无需CDP的插入模式）

某些场景不需要通过富通API同步，而是**直接写入本地SQLite**：

- **邮件发送**（`send_selected5.py`）— 发完一封直接 `INSERT INTO followups (..., source='email', synced=1)`
- **WhatsApp发送** — 同样可以直接写本地DB，标记 `synced=0` 等CDP就绪后批量同步
- **内部备注** — 不需要进富通时间轴的记录

这种模式的优点是**不需要CDP连接**（Python直连SQLite），缺点是记录不会实时出现在富通。需要时跑 `node sync_all_pending.mjs` 批量推送。

```python
# 示例：直接写跟进记录（无需CDP）
import sqlite3, json
from pathlib import Path

db = Path.home() / 'AppData/Local/hermes/memories/脚本缓存/富通CRM/crm_followups.db'
conn = sqlite3.connect(str(db))
conn.execute("""INSERT INTO followups
    (customer_id, customer_name, type, content, operator, source, synced)
    VALUES (?, ?, ?, ?, 'Kali Marfa', 'email', 1)""",
    (customer_id, customer_name, type_, content))
conn.commit()
conn.close()
```

关联技能：`bliiot-email-marketing` — CRM 老客户召回脚本 `send_crm_recall.py` 使用此模式。

## 关键铁则

1. **先查后增** — 加跟进前用 `crm_quick.py customer` 确认客户存在
2. **同步前需开CDP** — Chrome `--remote-debugging-port=9226 --profile-directory=Profile 2`，已登录trade.joinf.com
3. **双写确认** — 同步成功后 **必须同时**更新SQLite(`SYNCED=1`)和JSON(`pending_sync.json`)。只写JSON是半个同步 — sync_all_pending.mjs有SQLite写回逻辑，其他脚本不一定有
4. **displayValue必填客户名称** — 富通Vue组件依赖`dataName.displayValue`渲染跟进详情。空字符串→记录在时间轴但点进去空白。**6个同步文件(cjs/mjs/py)全部要传`customer_name`**，缺一不可
5. **planningTime格式** — 必须用本地时间字符串 `YYYY-MM-DD HH:mm:ss`，不要用ISO格式。多条记录同时间戳说明用了默认值
6. **颜色映射** — 邮件=2B579A(蓝), WhatsApp=27AE60(绿), 报价=E67E22(橙), 电话=E74C3C(红), 默认=fe4145
7. **永久存储** — SQLite + JSON双重保险
8. **Excel刷新** — 每次新加跟进后运行 `generate-excel` 或 `crm_quick.py excel`

## 已知Bug与修复

| 现象 | 原因 | 修复 |
|------|------|------|
| 时间轴有记录但点进去空白 | `dataName.displayValue` 为空 | 传`customer_name`给`displayValue` (6个文件都要改) |
| 多条记录时间戳完全相同 | `planningTime` 用了JS `new Date()` 默认值 | 从DB读出 `created_at` 传到payload |
| 返回"系统繁忙" | Cookie过期或未登录 | 重新登录富通 + 刷新页面 |
| 跟进类型不显示 | `method.dict=true` 但值不对 | 确保值匹配富通字典表 |
| 同步显示成功但SQLite没更新 | 脚本只写了JSON没写SQLite | 加 `UPDATE followups SET synced=1` 到DB |

### 跨文件修复模式（displayValue）

当修复displayValue问题时，必须检查以下6个文件全部改了，否则下次不同入口同步仍会出现空白记录：

```
sync_all_pending.mjs   → displayValue: customerName        ✅
sync_to_joinf.cjs      → displayValue: record.customer_name ✅
sync_to_joinf.mjs      → displayValue: rec.customer_name    ✅
sync_to_joinf.py       → displayValue: r.get('customer_name') ✅
bliiot_crm_sync.cjs    → displayValue: record.customer_name ✅
bliiot_crm_sync.mjs    → displayValue: followup.customer_name ✅
```

### 旧记录恢复

已同步到富通但`displayValue=""`的记录无法通过API删除或修改。只能：
1. 在富通UI手动删除空白记录
2. 重新同步（本地标记synced=0 → 重新推送）
3. 以后新记录保证走修复版代码