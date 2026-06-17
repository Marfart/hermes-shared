import { connectOrLaunchChrome } from "./chrome_cdp_launcher.mjs";

const DEBUG_PORT = 9223;

async function main() {
  console.log("Connecting to Chrome via CDP...");
  const { browser } = await connectOrLaunchChrome({
    debugPort: DEBUG_PORT,
    profileName: "whatsapp-bulk",
    startUrls: ["https://web.whatsapp.com/"],
  });

  const context = browser.contexts()[0];
  let page = context.pages().find((p) => p.url().includes("web.whatsapp.com"));
  if (!page) {
    page = await context.newPage();
    await page.goto("https://web.whatsapp.com/");
  }
  await page.bringToFront();
  await page.waitForTimeout(5000);

  // Check if we need to click "Use this window"
  const bodyText = await page.locator("body").innerText({ timeout: 10000 }).catch(() => "");
  if (bodyText.includes("使用此窗口") || bodyText.includes("Use this window")) {
    console.log("Found 'Use this window' prompt, clicking...");
    try {
      const useBtn = page.locator('div[role="button"]:has-text("使用此窗口"), div[role="button"]:has-text("Use this window")');
      if (await useBtn.count() > 0) {
        await useBtn.click();
        console.log("Clicked!");
        await page.waitForTimeout(5000);
      }
    } catch (e) {
      console.log("Could not click:", e.message);
    }
  }

  // Check if logged in
  const text2 = await page.locator("body").innerText({ timeout: 10000 }).catch(() => "");
  const needsLogin = /链接设备|link with phone number|扫码|qr code|保持手机联网/i.test(text2);
  if (needsLogin) {
    console.log("WhatsApp needs login - QR code required");
    await browser.close();
    process.exit(1);
  }

  console.log("WhatsApp is logged in! Reading chat list...");
  await page.waitForTimeout(3000);

  // Get chat list - find chats that have recent messages (from June 16 = 前天)
  const chats = await page.evaluate(() => {
    const rows = document.querySelectorAll('[role="row"]');
    const results = [];
    for (let i = 0; i < Math.min(rows.length, 30); i++) {
      const row = rows[i];
      const spans = row.querySelectorAll('span[dir="auto"]');
      const name = spans.length > 0 ? spans[0].textContent.trim() : "";
      const lastMsg = spans.length > 1 ? spans[spans.length - 1].textContent.trim().substring(0, 150) : "";
      if (name) results.push({ name, lastMsg });
    }
    return results;
  });

  console.log(`\nChat list (${chats.length}):`);
  for (const c of chats) {
    console.log(`  ${c.name}: ${c.lastMsg.substring(0, 100)}`);
  }

  await browser.close();
}

main().catch(console.error);
