export function encodeMessage(message) {
  return encodeURIComponent(message || "");
}

export function buildSendUrl(phone, message) {
  const normalizedPhone = String(phone || "").replace(/[^\d]/g, "");
  if (!normalizedPhone) {
    throw new Error("Missing phone number");
  }
  return `https://web.whatsapp.com/send?phone=${normalizedPhone}&text=${encodeMessage(message)}`;
}

export async function openChat(tab, phone, message) {
  await tab.goto(buildSendUrl(phone, message));
  await tab.playwright.waitForLoadState({ state: "domcontentloaded", timeoutMs: 15000 });
}

export async function waitForComposer(tab) {
  const bodyText = await tab.playwright.evaluate(() => document.body.innerText);
  if (/链接设备|Link with phone number|Use WhatsApp on your computer|Keep your phone connected/i.test(bodyText)) {
    throw new Error("WhatsApp Web is not logged in");
  }
  const composer = tab.playwright.locator('[contenteditable="true"]').filter({ hasText: "" });
  const count = await composer.count();
  return { composer, count, bodyText };
}

export async function sendCurrentPreparedMessage(tab) {
  const sendBtn = tab.playwright.locator('button').filter({ hasText: "" });
  const bodyText = await tab.playwright.evaluate(() => document.body.innerText);
  const hasPending = /send|发送/i.test(bodyText);
  if (!hasPending) {
    return { sent: false, reason: "No visible send cue detected" };
  }
  const dom = await tab.dom_cua.get_visible_dom();
  const json = JSON.stringify(dom);
  const sendNodeIdMatch = json.match(/"role":"button"[^}]*"ariaLabel":"发送"[^}]*"id":"([^"]+)"/);
  if (sendNodeIdMatch) {
    await tab.dom_cua.click({ node_id: sendNodeIdMatch[1] });
    return { sent: true, via: "dom_cua:发送" };
  }
  return { sent: false, reason: "Send button node not found in visible DOM" };
}

export async function sendQueue(tab, queue, options = {}) {
  const dryRun = options.dryRun ?? true;
  const delayMs = options.delayMs ?? 3000;
  const results = [];
  for (const lead of queue) {
    const result = {
      name: lead.name,
      whatsapp_number: lead.whatsapp_number,
      status: "pending",
    };
    try {
      await openChat(tab, lead.whatsapp_number, lead.message);
      await tab.playwright.waitForTimeout(3000);
      await waitForComposer(tab);
      if (dryRun) {
        result.status = "prepared";
      } else {
        const sent = await sendCurrentPreparedMessage(tab);
        result.status = sent.sent ? "sent" : "not_sent";
        result.send_result = sent;
      }
    } catch (error) {
      result.status = "error";
      result.error = error instanceof Error ? error.message : String(error);
    }
    results.push(result);
    await tab.playwright.waitForTimeout(delayMs);
  }
  return results;
}
