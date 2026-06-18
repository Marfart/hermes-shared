# 跟进记录 API Payload 详情与调试记录

来源：2026-06-18 会话 — 8条跟进记录同步到富通CRM后「时间轴有显示但点进去空白」的排查与修复。

## 根本原因

富通CRM跟进详情页为 Vue SPA 组件渲染。时间轴列表页只用到 `value` 字段，但 **详情页的客户名称和记录内容依赖 `displayValue` 字段渲染**。当 `displayValue` 为空字符串时，详情页渲染失败，显示为空白。

## 必有字段

以下字段是 `POST /rapi/m/follow/add` 的 **最小有效模型集**（实测2026-06-18验证）：

```javascript
const models = [
  // [必填] 客户名称 — displayValue 不能为空!
  { columnName: "dataName", value: 235327923,
    displayValue: "hsinsight",             // ← 这是关键！
    displayOriginalValue: 235327923 },
  
  // [必填] 跟进内容
  { columnName: "contactContent", value: "[WhatsApp] 客户问...",
    displayValue: "", displayOriginalValue: "" },
  
  // [选填] 颜色标记（用于时间轴图标颜色）
  { columnName: "bgColor", value: "27AE60",
    displayValue: "", displayOriginalValue: "" },
  
  // [选填] 跟进方式
  { columnName: "method", dict: true, value: "WhatsApp",
    displayValue: "", displayOriginalValue: "" },
  
  // [选填] 计划/记录时间
  { columnName: "planningTime", value: "2026-06-18 15:08:06",
    displayValue: "", displayOriginalValue: "" },
  
  // [必填] 操作员ID
  { columnName: "feedbackOperator", value: "183006",
    displayValue: "", displayOriginalValue: "" },
];
```

**注意**：`method` 字段的 `dict: true` 会影响渲染方式，但不影响内容是否存在。

## 颜色映射

| 跟进类型 | bgColor 值 | 颜色 |
|---------|-----------|------|
| 邮件 | 2B579A | 蓝 |
| WhatsApp | 27AE60 | 绿 |
| 报价 | E67E22 | 橙 |
| 电话 | E74C3C | 红 |
| 跟进/其他 | fe4145 | 默认红 |

## 时间格式

必须用 `YYYY-MM-DD HH:mm:ss` 本地时间字符串。不要用 ISO 8601 格式。

```
✅ "2026-06-18 15:08:06"
❌ "2026-06-18T07:08:06.000Z"
```

## 调试记录

### 现象
8条同步记录全部返回 `{success: true}`，在时间轴能看到记录，但点进去详情页内容是空的。

### 排查路径
1. 对比 #1、#2（14:37，14:47，手动单条同步，显示正常）和 #5-#14（15:08:06，批量同步，点进去空白）
2. 发现手动同步的脚本（旧版 `sync_to_joinf.cjs`）传了 `displayValue`，但批量同步脚本（`sync_all_pending.mjs`）的 `dataName.displayValue` 为 `""`
3. 确认：Vue 组件用 `displayValue` 渲染详情页客户名称，空字符串导致渲染失败

### 修复范围
6个同步文件全部修了同一个位置：

| 文件 | 修改变量 |
|------|---------|
| `sync_all_pending.mjs` | `displayValue: customerName` |
| `sync_to_joinf.mjs` | `displayValue: rec.customer_name` |
| `sync_to_joinf.cjs` | `displayValue: record.customer_name` |
| `sync_to_joinf.py` | `displayValue: json.dumps(r.get('customer_name', ''))` |
| `bliiot_crm_sync.cjs` | `displayValue: record.customer_name` |
| `bliiot_crm_sync.mjs` | `displayValue: followup.customer_name` |

### 附加修复
`sync_all_pending.mjs` 原来只把成功状态写回 `pending_sync.json`，没有更新 SQLite。加了 `markSyncedInDB()` 函数同步成功后写 `UPDATE followups SET synced=1`。