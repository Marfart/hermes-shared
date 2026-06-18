# CRM Email Recall — 实战参考

## 2026-06-18 实战记录

首次CRM老客户召回邮件发送成功：

| # | 客户 | 邮箱 | 国家 | 状态 |
|---|------|------|------|------|
| 1 | Juan Carlos Martinez | juancarlosmartinezq@hotmail.com | 🇨🇴 Colombia | ✅ sent |
| 2 | Stephen Hudson | Stephen@Home.co.nz | 🇳🇿 New Zealand | ✅ sent |
| 3 | Richard Twite | richard@twite.com.au | 🇦🇺 Australia | ✅ sent |
| 4 | Basem Mohamed Ibrahim | basemnani71077@gmail.com | 🇪🇬 Egypt | ✅ sent |
| 5 | Alex Elliot | alex@the-elliots.us | 🇺🇸 USA | ✅ sent |

## 关键参数

- **SMTP**: smtp.qq.com:465, kali_foever@qq.com
- **授权码**: reoefbstemklbdcd
- **发送模式**: 拟人，每封间隔60-150秒
- **跟进记录**: 自动写入CRM SQLite，source='email'

## 客户筛选条件

- 创建时间 < 2024-01-01
- 有有效的contactEmail
- 共1600+符合条件

## 已发送列表（避免重复）

已发送的5封未用去重文件记录（send_selected5.py无`.sent_log.json`）。下次发之前可先排除这5个邮箱：juancarlosmartinezq@hotmail.com, Stephen@Home.co.nz, richard@twite.com.au, basemnani71077@gmail.com, alex@the-elliots.us