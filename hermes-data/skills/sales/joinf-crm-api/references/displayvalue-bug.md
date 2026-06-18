# displayValue 空白记录 Bug 排查与修复 (2026-06-18)

## 现象

富通CRM跟进记录显示在时间轴（联系人时间线），但点击进去内容区域空白，看不到任何字段。

## 根因

富通CRM的Vue组件在渲染跟进详情页时，依赖 `dataName.displayValue` 字段来展示客户名称。当该字段为空字符串时，组件可能跳过整个渲染流程或导致其他字段不被显示。

原始代码中6个同步文件都传了 `displayValue: ""`。

## 修复

`dataName.displayValue` 必须传客户名称字符串:

```json
{ "columnName": "dataName", "value": 235327923,
  "displayValue": "hsinsight",           // ← 客户名称，不是ID
  "displayOriginalValue": 235327923 }
```

## 涉及的文件（全部修）

- `sync_all_pending.mjs` → `displayValue: customerName`
- `sync_to_joinf.cjs` → `displayValue: record.customer_name`
- `sync_to_joinf.mjs` → `displayValue: rec.customer_name`
- `sync_to_joinf.py` → `displayValue: json.dumps(r.get('customer_name', ''))`
- `bliiot_crm_sync.cjs` → `displayValue: record.customer_name`
- `bliiot_crm_sync.mjs` → `displayValue: followup.customer_name`

## 旧数据恢复

已同步的空白记录无法通过API删除或修改。方法：
1. 富通UI手动删除
2. 本地标记synced=0 → 重新推送（会创建新记录）
3. 以后的记录走修复代码保证正确

## 排查方法

1. 查本地SQLite：确认 `customer_name` 字段有值
2. 查富通时间轴：有记录但空白 → displayValue问题
3. 查同步日志：看API返回的 `success: true` 不代表内容正确
4. 对比#1 #2（手动同步，displayValue正确）vs #5-#14（批量同步，displayValue空）

## 预防

所有新写的同步脚本，在 `dataName` model 中必须包含非空 `displayValue`。代码审查时检查这一点。