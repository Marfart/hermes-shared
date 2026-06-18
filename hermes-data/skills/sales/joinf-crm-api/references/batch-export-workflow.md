# 富通CRM 批量导出工作流

## 前置条件

1. Chrome 浏览器已登录 `trade.joinf.com`（账号 bliiot03）
2. Chrome 需启动远程调试端口（通常 9223 或 9226）

## 第一步：启动带 CDP 的 Chrome（如果尚未启动）

```powershell
Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9226','--profile-directory=Profile 2','--user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data'
```

## 第二步：登录（绕过拼图验证码）

通过 CDP WebSocket：
1. Navigate to `https://cloud.joinf.com/login`
2. Fill username: `bliiot03`, password: `Kali1314520!`
3. Click `loginBtn` — 拼图验证码被绕过，直接跳转到 CRM

## 第三步：提取认证信息

- `Network.getCookies` → Cookie header
- `localStorage.getItem('joinf-compnayId')` → xCid = "71376"
- `localStorage.getItem('joinf-XUser')` → xUser = "183006"

## 第四步：翻页拉取全部客户

size=200 可用。1955 条客户约 10 页。

完整脚本见 `../scripts/fetch_all_customers.mjs`

## 第五步：生成 Excel 报表

必须清洗非打印字符（openpyxl IllegalCharacterError 陷阱）。

完整脚本见 `../scripts/generate_excel.py`

建议 4 个 Sheet：
- 客户总览（Dashboard）
- 全部客户数据（49 列，自动筛选+冻结）
- 业务员统计
- 国家地区统计

## 几组常用分析

### 有邮箱的客户
```python
has_email = sum(1 for c in customers if c.get('contactEmail'))
```

### 即将转入公海的客户（剩余 < 7 天）
```python
import re
def days_remaining(r):
    m = re.search(r'(\d+)天', str(r))
    return int(m.group(1)) if m else 999
nearly_expired = [c for c in customers if days_remaining(c.get('remainingTime','')) < 7]
```

### 按来源筛选客户
```python
linkedin = [c for c in customers if c.get('source') == '领英开发']
website = [c for c in customers if c.get('source') == '官网询价']
```

### 102 个原始字段说明
详见 SKILL.md 中的关键字段速查表。