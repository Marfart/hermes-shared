# WhatsApp 自动发送开发信

## 两种管道

| 管道 A: Playwright CDP (新) | 管道 B: Selenium (旧) |
|---|---|
| CDP + Chrome | Selenium WebDriver |
| JSON管道 | Excel直接 |
| 4style x 9段结构 | 11种关键词模板 |

## 管道A数据链
```
Excel → build_enriched_0602.py → build_whatsapp_queue.mjs
  → render_whatsapp_messages.mjs → whatsapp_bulk_sender_cdp.mjs
```

## 消息结构 (9段)
1. greeting (5变体)
2. intro (5变体)
3. company_pitch (4种按领域)
4. observation (按style)
5. offer (产品匹配)
6. value (价值说明)
7. cta (行动号召)
8. link (官网)
9. close (收尾)

## 防封号
- 发送间隔: 2-5分钟随机
- 每会话上限: 30条
- 日建议: 20-30条
- 操作间加human_delay(2-8s)

## 断点续传
- progress.json 记录已发送
- sent_registry.json 查重

## 首次使用
1. 关本地Chrome
2. 运行脚本 → 自动打开Chrome
3. 首次扫QR码 → session保存
