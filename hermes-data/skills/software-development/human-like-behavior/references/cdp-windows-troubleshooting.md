# Windows CDP 连接排错指南

## 场景
需要通过CDP连接本机已登录Chrome（如WhatsApp Web）时，端口未开的排查和解决。

## ⚠️ 最重要的区别

**Hermes `browser_navigate` 用的 Browserbase 云服务器 — 页面不会出现在用户屏幕上！**

需要用户看到QR码/视觉验证 → 必须用本机Chrome CDP。
后台脚本/爬虫/无需用户看 → 可以用Hermes Browserbase。

## 完整启动流程（agent自动执行）

### Step 1: 杀掉Chrome
```bash
taskkill //F //IM chrome.exe
sleep 3
```

### Step 2: 删除Singleton锁（必须！否则Chrome忽略--remote-debugging-port）
```bash
rm -f "/c/Users/Admin/AppData/Local/Google/Chrome/User Data/SingletonLock"
rm -f "/c/Users/Admin/AppData/Local/Google/Chrome/User Data/SingletonSocket"
rm -f "/c/Users/Admin/AppData/Local/Google/Chrome/User Data/SingletonCookie"
```

### Step 3: 用PowerShell启动
```bash
powershell.exe -Command 'Start-Process "C:\Program Files\Google\Chrome\Application\chrome.exe" -ArgumentList "--remote-debugging-port=9223","--user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data","https://web.whatsapp.com"'
```

### Step 4: 验证
```bash
sleep 6
netstat -ano | grep 9223
curl -s http://127.0.0.1:9223/json/version
```

## 启动失败排查表

| 症状 | 根因 | 解决 |
|------|------|------|
| `cmd.exe start "chrome.exe" --remote-debugging-port=9223` 参数不传递 | cmd.exe的start命令不能正确传带等号的参数 | 改用PowerShell Start-Process |
| terminal `&` 后台启动 | Hermes拦截前台shell的background | 用taskkill + powershell Start-Process |
| Chrome起来了但端口没监听 | SingletonLock未删，profile被占，Chrome用已有实例 | 删除Singleton锁文件后重试 |
| `curl http://127.0.0.1:9223/json/version` exit 7 | Chrome启动中还没绑定端口 | sleep 5-8秒再试 |

## 验证CDP可用后

用Hermes浏览器工具连本机WhatsApp：
```
browser_navigate("https://web.whatsapp.com")  # 此时走的是本机CDP 9223端口
```
如果本机Chrome已登录WhatsApp，直接跳转聊天列表不会显示QR码。

## WhatsApp Web 电话号码登录（QR码不可用时的fallback）

### 触发条件
- 用户说"扫不了/登不了了/用电话号码"
- Hermes浏览器截图无法显示二维码（cloud server渲染问题）

### 操作流程（Playwright MCP）

```javascript
// 1. 导航到WhatsApp Web
await page.goto('https://web.whatsapp.com')

// 2. 等页面加载
await page.waitForTimeout(8000)

// 3. 点击"使用电话号码登录"
await page.getByText('使用电话号码登录').click()

// 4. 等表单加载
await page.waitForTimeout(3000)

// 5. 此时页面显示：国家旗帜下拉 + 号码输入框 + "下一步"按钮
// 用户手动操作：选国家 → 输入号码 → 点下一步

// 6. WhatsApp发验证码到手机App
// 用户查看App通知 → 输入6位码 → 完成登录
```

### 2026-06-29 实例
- Kali说"登不了了，用手机号码登录吧"
- Playwright页面click "使用电话号码登录"成功，切换到号码表单
- 需要Kali手动在国家下拉选+输入号码+点下一步
- **后续需要确认Kali的WhatsApp号码国家（+86? +27? 其他?）**

## 铁律
- WhatsApp操作必须用CDP连本机Chrome，不能用Playwright MCP
- Hermes浏览器工具走Vortex代理，访问WhatsApp会超时
- 用户需要"看到"任何页面内容时（扫码等）→ 必须本机Chrome，不能Browserbase
- 永远自动执行开CDP流程，不要等用户手动操作
- 不要浪费时间在失败的方案上
