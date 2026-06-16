# Joinf 客户 + 公海手机号导出

日期：2026-06-02

## 目标

从富通 `我的客户 + 公海` 中，导出 `2025-01-01` 到当前为止，所有 `联系人手机号非空` 的客户记录。

## 方法

- 不依赖内置浏览器登录态。
- 使用专用 Chrome 调试会话：`http://127.0.0.1:9226`
- 直接调用富通列表接口，再本地过滤：
  - `displayCreateTime >= 2025-01-01`
  - `contactMobile` 非空

## 接口

- 我的客户：
  - `GET /rapi/d/customers?num={page}&paging=true&size=1000&sortColumn=&sortType=&isAsterisk=0`
- 公海：
  - `GET /rapi/d/customers/public?num={page}&paging=true&size=1000&sortColumn=lastTransferTime&sortType=desc&source=&mainProduct=`

## 脚本

- `C:\Users\Admin\AppData\Local\hermes\scripts\joinf-crm-edm\export_customer_and_public_mobile_since.mjs`

## 本次产物

- JSON：
  - `C:\Users\Admin\AppData\Local\hermes\memories\joinf-crm-edm\joinf_customer_public_mobile_since_2025-01-01_2026-06-02.json`
- CSV：
  - `C:\Users\Admin\AppData\Local\hermes\memories\joinf-crm-edm\joinf_customer_public_mobile_since_2025-01-01_2026-06-02.csv`
- 汇总：
  - `C:\Users\Admin\AppData\Local\hermes\memories\joinf-crm-edm\joinf_customer_public_mobile_since_2025-01-01_2026-06-02_summary.json`

## 结果

- 总条数：`94`
- 我的客户：`56`
- 公海：`38`
