# WhatsApp Automation Notes

Date: `2026-06-01`

## Important finding

`https://trade.joinf.com/tms/whatsapp` is not a direct message composer.
It currently shows a sync/helper page:

- `聊天同步，需同时登录 WhatsApp`
- `下载富通助手2.0`

That means the practical send path should use `WhatsApp Web`, not the Joinf sync page itself.

## Files

- Queue builder:
  `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\build_whatsapp_queue.mjs`
- Message renderer:
  `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\render_whatsapp_messages.mjs`
- Browser send module:
  `C:\Users\Admin\AppData\Local\hermes\scripts\buyer-development\whatsapp_web_sender.js`

Generated data:

- Queue JSON:
  `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_priority_queue_2026-06-01.json`
- Queue CSV:
  `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_priority_queue_2026-06-01.csv`
- Rendered messages:
  `C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_messages_2026-06-01.json`

## Current queue

Current WhatsApp-priority lead count: `3`

1. `Iris Automation Pvt. Ltd.`
2. `serendibtechnologies`
3. `1.618 S.R.L.`

## Send strategy

1. Log in to `https://web.whatsapp.com/`
2. Load the queue JSON with pre-rendered messages
3. For each lead, open:
   `https://web.whatsapp.com/send?phone=<number>&text=<encoded_message>`
4. Wait for chat composer to load
5. In dry-run mode, only prepare chats
6. In live mode, click send

## Safety

- Use dry-run first
- Confirm before live sending to real contacts
- Best for small batches first, then scale up
