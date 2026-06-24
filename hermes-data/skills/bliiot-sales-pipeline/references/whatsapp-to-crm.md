# WhatsApp -> 富通CRM 管道

## 工作流
1. WhatsApp Web 读取客户消息
2. 提取联系人信息
3. 三字段匹配 (contactName / linkman / company)
4. 匹配 → 添加跟进记录
5. 不匹配 → 新增客户

## 三字段匹配规则
- contactName 匹配 → 防止重复创建
- linkman 匹配 → 同一公司不同联系人
- company 匹配 → 已知公司

## 技术实现
- 读取: Playwright MCP 浏览器
- 写入: 富通API (joinf-crm-api)
- 本地缓存: SQLite (crm_followups.db)
