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
  await page.waitForTimeout(3000);

  // Get full page text
  const bodyText = await page.locator("body").innerText({ timeout: 10000 }).catch(() => "");
  console.log("=== Page text ===");
  console.log(bodyText.substring(0, 1000));
  console.log("=== End ===");

  // Check for buttons
  const buttons = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button, div[role="button"]')).map(b => ({
      text: b.textContent.trim().substring(0, 50),
      tag: b.tagName,
      visible: b.offsetParent !== null
    }));
  });
  console.log("\nButtons:", JSON.stringify(buttons, null, 2));

  // Check for QR
  const hasQR = await page.evaluate(() => !!document.querySelector("canvas"));
  console.log("Has QR canvas:", hasQR);

  // Check for chat list
  const hasChatList = await page.evaluate(() => !!document.querySelector('[data-testid="chat-list"]'));
  console.log("Has chat-list:", hasChatList);

  // Check URL
  const url = page.url();
  console.log("URL:", url);

  await browser.close();
}

main().catch(console.error);
