# 富通CRM API探索日志

## 任务目标
找出富通/金蝶后台真实API，优先解决：添加备注、添加跟进记录、修改客户资料、保存邮件草稿、新增客户

## 环境信息
- 浏览器：Chrome 149.0.7827.103，CDP端口9223
- 测试客户ID: 238855365 (Вадим 2)
- 登录账号: blliot03 / Kali1314520!
- 当前页面: https://trade.joinf.com/tms/customer/customers?type=edit&id=238855365&tab=0

## 已知API（读）
- GET /rapi/d/customers?num={page}&paging=true&size=50 — 读取客户列表
- GET /rapi/d/customer/check?type=0&key={name}&customerTypeId={id}&customerId={id} — 检查名称重复

## 已知问题
- CDP websocket连接超时（send成功但recv超时）
- POST/PUT /rapi/d/customers 返回"系统繁忙"
- /rapi/d/customer/save 返回404

## 探索进度

### 阶段1：CDP Network监听（进行中）
- 时间：2026-06-17 约19:45开始
- 问题：CDP websocket超时，尝试多种方式连接
- 下一步：尝试用Chrome HTTP接口或pagesok替代

### 阶段2：HAR导出分析（待执行）
### 阶段3：JS bundle反查（待执行）
### 阶段4：Storage/Token解析（待执行）
### 阶段5：GraphQL/Gateway/RPC检查（待执行）
### 阶段6：WebSocket frame检查（待执行）
### 阶段7：页面内部request函数（待执行）
### 阶段8：备选方案（待执行）
### [03:59:44] ============================================================
### [03:59:44] 阶段1开始: Network监听 + 添加备注测试
### [03:59:44] ============================================================
### [03:59:44] 页面: 1716057F6682601E5C7250B087727896
### [03:59:44] WebSocket连接成功 ✓
### [03:59:44] Network.enable: OK
### [03:59:44] 页面: complete | https://trade.joinf.com/tms/customer/customers?type=edit&id=238855365&tab=0
### [03:59:44] 原始备注: No introduce. Textareas: 0
### [03:59:44] 测试字符串: HERMES_API_TEST_035944
### [03:59:44] 设置备注: NO_ELEMENT
### [03:59:44] 保存按钮: CLICKED: 保存
### [03:59:44] 监听 Network 请求 (10秒)...
### [03:59:54] 收集到 2 个 POST/PUT/PATCH 请求
### [03:59:54] 目标请求: 2
### [03:59:54] 
--- 请求 1  ---
### [03:59:54]   URL: https://tracking.joinf.com/record/log
### [03:59:54]   Method: POST
### [03:59:54]   Payload: data_list=W3siZGlzdGluY3RfaWQiOiI3ODY3MTgiLCJsaWIiOnsiJGxpYiI6ImpzIiwiJGxpYl9tZXRob2QiOiJjb2RlIiwiJGxpYl92ZXJzaW9uIjoiMS4xNC4xNSJ9LCJwcm9wZXJ0aWVzIjp7
### [03:59:54] 
--- 请求 2  ---
### [03:59:54]   URL: https://rumt-zh.com/speed?from=https%3A%2F%2Ftrade.joinf.com%2Ftms%2Fcustomer%2Fcustomers%3Ftype%3Dedit%26id%3D238855365%26tab%3D0&sampled=1&id=dWJXZT
### [03:59:54]   Method: POST
### [03:59:54]   Payload: {"payload":"{\"duration\":{\"fetch\":[{\"url\":\"https://tracking.joinf.com/record/log\",\"isHttps\":true,\"method\":\"POST\",\"type\":\"fetch\",\"sta
### [03:59:54] 
Cookies (10): JOINF_SESSION=Mjc5YTk1ZmUtZGFjNi00ZTgwLWE3ZWQtZjNlY2ExMTZlNDFh; language=zh; tgw_l7_route=d141dcb5fe4c19de0f74b0c71546b82b; userLoginInfoSaas=%7B%22userName%22%3A%22bliiot03%22%7D; releaseCenterLoginI
### [03:59:54] 当前备注: NO_ELEMENT
