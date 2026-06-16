# WhatsApp Web QR码提取方法 (2026-06验证)

## 新版WhatsApp Web UI变化

WhatsApp Web新版登录页面已不再使用`<canvas>`绘制QR码，改用**内嵌SVG**。QR码位于`[data-ref]`属性的div内。

## 提取方法（从简到繁）

### 方法1: Playwright MCP 元素截图（最简单推荐）

```javascript
// Playwright MCP — 直接截[data-ref]元素
await page.locator('[data-ref]').screenshot({ path: 'whatsapp_qr.png' });
```

一步搞定，截图自动保存到指定路径。最可靠。

### 方法2: SVG → Canvas → 高清PNG

当需要放大QR码（手机扫描需要足够分辨率）时：

```javascript
// 1. 提取SVG
const dataRefEl = document.querySelector('[data-ref]');
const svgEl = dataRefEl.querySelector('svg');
const svgData = new XMLSerializer().serializeToString(svgEl);
const svgBase64 = btoa(unescape(encodeURIComponent(svgData)));
const imgSrc = 'data:image/svg+xml;base64,' + svgBase64;

// 2. 渲染到Canvas（放大6x）
const img = new Image();
img.onload = () => {
    const canvas = document.createElement('canvas');
    const scale = 6;
    canvas.width = (img.width || 264) * scale;
    canvas.height = (img.height || 264) * scale;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = false;  // QR码要像素精确
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/png');
    // dataUrl 即为base64 PNG
};
img.src = imgSrc;
```

### 方法3: 整页截图 + 裁剪

```javascript
// 获取QR码区域坐标
const rect = document.querySelector('[data-ref]').getBoundingClientRect();
// { x: 623.5, y: 261, width: 228, height: 228 }
// 然后用Playwright clip截图
```

## 不工作的方法

| 方法 | 原因 |
|------|------|
| `document.querySelector('canvas')` | QR码首次渲染后canvas可能被回收（hasCanvas从true变false） |
| `img[alt*="QR"]` | 新版不再用`<img>`标签 |
| `document.querySelector('[data-testid="qr-code"]')` | 此testid不存在 |
| 直接`curl`下载页面 | WhatsApp Web是SPA，需要JS执行后才渲染QR码 |

## CDP连接方式

WhatsApp Web需要在已登录的Chrome profile中操作：

```bash
# 启动带CDP的Chrome（使用whatsapp-bulk profile）
node open_whatsapp_browser.mjs  # 启动在端口9223

# Playwright MCP连接
# mcp_playwright_browser_navigate → https://web.whatsapp.com/
# 然后用browser_snapshot或browser_take_screenshot查看
```

## 登录检测

```javascript
// 检查是否已登录
const chatList = document.querySelector('[data-testid="chat-list"]');
const hasQR = !!document.querySelector('[data-ref]');
const bodyText = document.body.innerText;

// 已登录: hasChatList = true
// 未登录: bodyText包含 "扫描登录" / "Scan this QR code"
```

## 发送QR码给用户

截图后复制到桌面，用户可直接扫码：
```bash
cp "image_cache_path/qr.png" "C:/Users/Admin/Desktop/whatsapp_qr_login.png"
```