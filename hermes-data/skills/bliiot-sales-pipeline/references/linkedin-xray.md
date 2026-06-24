# LinkedIn X-Ray 客户挖掘

不登录LinkedIn，通过搜索引擎批量获取客户公开资料。

## 工作路径
`site:linkedin.com/in/` + keywords on DuckDuckGo

## BLIIOT 目标客户查询模板

```
site:linkedin.com/in/ "system integrator" "South Africa"
site:linkedin.com/in/ "PLC" "SCADA" "South Africa"
site:linkedin.com/in/ "IIoT" Africa engineer
site:linkedin.com/in/ "industrial automation" Kenya Nigeria
site:linkedin.com/in/ "automation" "Africa" director
site:linkedin.com/in/ "RTU" "SCADA" Africa
site:linkedin.com/in/ "remote monitoring" Africa SCADA
site:linkedin.com/in/ "control systems" "Africa" engineer
```

## 产出
~60-80 unique profiles from 8 queries (~2.5 minutes)
~40% South Africa, ~10% Kenya, ~8% Nigeria

## 输出格式
Excel: Full Name, Job Title, Company, Country, Profile URL, Source Query, Description

## 标题解析规则
- `Name - Job Title - Company | LinkedIn` → 三分割
- `Name - Job Title at Company | LinkedIn` → split "at"
- `Name - Company | LinkedIn` → job empty
- `Name | LinkedIn` → only name

## 已知死路 (不要重复)
- ❌ Bing — Cloudflare Turnstile blocks
- ❌ Google — LinkedIn 2024 robots.txt removed /in/ pages
- ❌ Google Cache — returns captcha wall
- ❌ Brave Search API — low yield, needs API key
- ❌ 访问profile URL — authwall redirect

## 限制
- DuckDuckGo: ~1 query per 1.5s
- 结果每天变化
- 国家检测基于关键词启发式
