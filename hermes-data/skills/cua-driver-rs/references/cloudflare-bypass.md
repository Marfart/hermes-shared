# Cloudflare 绕过方案 (Browser-based)

## 问题

Browserbase 的远程浏览器代理 IP 被多数国际平台（Medium、Hackster.io、DirectIndustry、Quora、PLCtalk 等）的 Cloudflare 安全服务标记为 bot，表现为：
- Cloudflare Challenge 验证页循环（Ray ID、JS Challenge）
- 部分站点直接 403（`ERR_CONNECTION_CLOSED`）
- 中国站点（知乎、阿里巴巴、工控论坛）不受影响

## 确认的绕过方案

### 方案 A：CDP 连接本机 Chrome（推荐）

**原理：** 用 `--remote-debugging-port` 启动用户本地已登录的 Chrome，然后用 `browser_navigate` 通过这个端口操控浏览器。本地 Chrome 用的是用户家宽的真实 IP，不会被 Cloudflare 标记。

```bash
# 启动带 CDP 端口的本机 Chrome（用 Kali 的真实 profile）
powershell.exe -NoProfile -Command "Start-Process -WindowStyle Hidden \
  'C:\Program Files\Google\Chrome\Application\chrome.exe' \
  -ArgumentList '--remote-debugging-port=9555 \
    --user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data'"

# 验证 CDP 是否连上
curl -s http://localhost:9555/json/version | python -c "
import sys, json
d = json.load(sys.stdin)
print('Browser:', d.get('Browser','?'))
"
```

**注意事项：**
- 端口号选择 9555（不冲突，WhatsApp CDP 用 9223）
- `--user-data-dir` 必须指向用户真实 profile（否则是个空 profile，无 cookie 无登录态）
- 启动后 `browser_navigate` 工具会自动用这个端口
- 启动窗口会被隐藏（`-WindowStyle Hidden`），但仍可能在任务栏出现

### 方案 B：Cua Driver 启动 Chrome（备选）

如果 CDP 启动不成功，用 Cua Driver 的 `launch_app`：

```python
import subprocess, json
proc = subprocess.Popen(['cua-driver', 'launch_app'], stdin=subprocess.PIPE, text=True)
proc.communicate(json.dumps({
    'path': 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'args': ['--new-window', 'https://example.com']
}))
```

**缺点：** cua-driver launch_app 走后台启动，不暴露 CDP 端口，所以 `browser_navigate` 无法用它。

### 方案 C：在中国平台注册（无需绕过）

知乎、阿里巴巴、Made-in-China、工控论坛等中国平台无 Cloudflare，可直接用 `browser_navigate` 访问：
- 用 `+86 17704014518` 注册（验证码发到 Kali 微信）
- 用 `bl42@bliiot.com` 作为公司邮箱

## 被 Cloudflare 封锁时的识别特征

```
页面标题包含：
  - "正在进行安全验证" / "Attention Required!"
  - "请稍候…"（无限转圈）
  - "You have been blocked"
  - "Just a moment..."

browser_navigate 返回：
  - bot_detection_warning = true
  - error = "ERR_CONNECTION_CLOSED"
  - error = "net::ERR_HTTP_RESPONSE_CODE_FAILURE"
  - snapshot 只有一个 "Cloudflare" 链接 + 验证框
```