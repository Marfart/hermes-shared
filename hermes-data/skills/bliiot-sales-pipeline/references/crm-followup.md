# CRM 跟进记录工具

## 架构
本地SQLite + 富通API双向同步

## 数据库
- `crm_followups.db` — 本地SQLite
- customers表 + followups表

## 功能
- 一键添加跟进
- 查客户
- 生成Excel报告
- 同步到富通CRM

## 双写模式
1. SQLite INSERT (本地)
2. pending_sync.json (待同步队列)
3. 同步到富通API
4. 标记 synced=1
