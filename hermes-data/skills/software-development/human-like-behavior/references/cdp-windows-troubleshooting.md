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

## 铁律
- WhatsApp操作必须用CDP连本机Chrome，不能用Playwright MCP
- Hermes浏览器工具走Vortex代理，访问WhatsApp会超时
- 用户需要"看到"任何页面内容时（扫码等）→ 必须本机Chrome，不能Browserbase
- 永远自动执行开CDP流程，不要等用户手动操作
- 不要浪费时间在失败的方案上
