import { buildDebugUrl, buildProfileDir, connectOrLaunchChrome } from "./chrome_cdp_launcher.mjs";

const DEBUG_PORT = 9223;

const { browser, launched, userDataDir } = await connectOrLaunchChrome({
  debugPort: DEBUG_PORT,
  profileName: "whatsapp-bulk",
  startUrls: ["https://web.whatsapp.com/"],
});

await browser.close().catch(() => {});

console.log(
  JSON.stringify(
    {
      status: "ready",
      launched,
      debugUrl: buildDebugUrl(DEBUG_PORT, DEBUG_PORT),
      profileDir: userDataDir || buildProfileDir("whatsapp-bulk"),
      note: "If WhatsApp is not logged in, scan once in this dedicated browser profile.",
    },
    null,
    2
  )
);
