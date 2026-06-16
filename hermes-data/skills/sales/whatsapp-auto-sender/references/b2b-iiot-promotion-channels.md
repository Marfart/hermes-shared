# B2B IIoT 推广渠道参考 (2026-06-03 更新)

BLIIoT 产品（工业网关、ARM边缘控制器、PLC上云方案）全球推广渠道调研结果。

## ⛔ 被封禁的渠道（Kali 2026-06-03 明确禁止）

| 渠道 | 原因 | 替代方案 |
|:----|:-----|:---------|
| ❌ **Reddit** (r/PLC, r/IOT) | 易因产品推广被封号 | 国内B2B平台或知乎 |
| ❌ **LinkedIn** | 易被封号 | 国内B2B平台或知乎 |
| ❌ **Telegram 工业群** | 易被封号 | WhatsApp 直发开发信 |
| ❌ **GitHub Issues/Discussions** | 关联 GitHub 账号风险 | 技术博客平台 |

## ✅ 批准的渠道（按优先级排序）

### 第一梯队：国内平台（无Cloudflare，不会封号）

| 平台 | 注册方式 | 受众 | 推广方式 |
|:----|:---------|:----|:---------|
| 🏆 **知乎** | `+86 17704014518` | 国内工控/自动化工程师 | 写技术文章+回答相关问题 |
| 🏆 **工控论坛** (gongkong.com) | `+86 17704014518` | 国内PLC/SCADA工程师 | 技术讨论帖 |
| 🏆 **中国制造网** (Made-in-China.com) | `+86 17704014518` | 全球B2B采购商 | 产品上架+店铺运营 |
| 🏆 **Alibaba.com** | `+86 17704014518` | 全球B2B采购商 | 产品上架（BLIIoT可能已有） |

### 第二梯队：技术内容平台（邮箱注册，无电话验证）

| 平台 | 注册方式 | 受众 | 推广方式 |
|:----|:---------|:----|:---------|
| ✍️ **Medium** | `bl42@bliiot.com` | 全球技术读者 | 《How to Connect Legacy PLCs to Cloud》技术文章 |
| 💻 **Dev.to** | `bl42@bliiot.com` | 开发者/IIoT工程师 | 技术教程+WhatsApp引流 |
| 📐 **Hackster.io** | 邮箱 | IoT硬件爱好者 | 项目帖子《Modbus to Cloud with BLIIoT Gateway》 |
| 🔧 **element14** | 邮箱 | 电子工程师 | 技术经验分享 |

### 第三梯队：行业媒体评论区

| 平台 | 方式 |
|:----|:-----|
| 📰 **控制工程网** (cechina.cn) | 在IIoT相关文章下留技术性评论 |
| 🔩 **iiot-world.com** | 评论区留有用信息+WhatsApp |

## 🎯 最新注册配置

```yaml
company_email: bl42@bliiot.com    # 公司邮箱 - 用于技术平台注册
company_phone: "+86 17704014518"  # 推广WhatsApp号 - 用于国内平台注册
registration_flow: |
  1. 小马打开注册页 + 填号
  2. 验证码发到Kali微信
  3. Kali 复制验证码给小马
  4. 小马完成注册
```

## 🚫 Cloudflare 封锁（已确认）

**当前浏览器（Browserbase）的代理IP已被多数国际平台标记为bot，表现为：**
- Cloudflare 验证页无限循环
- 部分站点直接 403 封 IP
- 中国站点（知乎、阿里巴巴等）不受影响

**解决方案：**
1. CDP 连接本机真实 Chrome（`--remote-debugging-port=9555 --user-data-dir=...`）
2. 直接在中国平台注册（无 Cloudflare）
3. 让 Kali 自己在浏览器注册后告诉小马验证码

## 📝 推广文案模板（标准格式）

```
[技术问题/分享经验] → [提到 BLIIoT 产品方案] → [WhatsApp: +86 17704014518]
```

所有文案已保存到 `memories/脚本缓存/BLIIoT推广/`：
- `battle_plan.md` — 作战方案
- `copywriting.md` — 完整文案（6套）
- `ready_to_post.md` — 可直接复制粘贴的版本

## 🚀 最有效的自动化推广路径（当前已验证）

1. **WhatsApp CDP 管道**（已有 `scripts/buyer-development/`）— 直接发开发信给目标客户，最直接有效
2. **国内B2B平台注册** — 知乎、Alibaba、工控论坛，用 `+86 17704014518` 注册
3. **技术博客** — Medium/Dev.to 写文章用 `bl42@bliiot.com` 注册（无电话验证）