import { buildDebugUrl, buildProfileDir, connectOrLaunchChrome } from "./chrome_cdp_launcher.mjs";

const DEBUG_PORT = 9226;

const { browser, launched, userDataDir } = await connectOrLaunchChrome({
  debugPort: DEBUG_PORT,
  profileName: "joinf-maps-live",
  startUrls: [
    "https://data.joinf.com/searchResult?open=firstPage",
    "https://www.google.com/maps?hl=en",
  ],
});

await browser.close().catch(() => {});

console.log(
  JSON.stringify(
    {
      status: "ready",
      launched,
      debugUrl: buildDebugUrl(DEBUG_PORT, DEBUG_PORT),
      profileDir: userDataDir || buildProfileDir("joinf-maps-live"),
      note: "If Joinf login is missing, log in once in this dedicated browser profile.",
    },
    null,
    2
  )
);
