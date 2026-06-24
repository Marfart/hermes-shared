# 富通CRM API (JoinF)

## 认证
- appKey + appSecret
- 详见 joinf-crm-api skill

## 核心操作
- 新增客户
- 修改客户资料
- 添加跟进记录

## 跟进记录API
- URL: `/rapi/m/follow/add`
- Method: POST
- Content-Type: application/json

### 字段要求
- displayValue: 客户名称 (必须非空!)
- bgColor: 如 "2B579A" (不要加引号)
- method: "邮件" / "WhatsApp" / "电话"
- planningTime: "2026-06-18 19:22:42"
- feedbackOperator: 用户ID

## 同步方式
1. Hermes Browser (推荐) — 直接用已登录的浏览器
2. CDP WebSocket — 独立Chrome实例

## 验证陷阱
- 不要只相信API success:true
- 验证displayLastFollowTime是否更新
- 检查window.location.href确认已登录
