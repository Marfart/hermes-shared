import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright-core");

export const CHROME_PATH = "C:/Program Files/Google/Chrome/Application/chrome.exe";

export function buildProfileDir(profileName) {
  return path.join(
    os.homedir(),
    "AppData",
    "Local",
    "hermes",
    "chrome-profiles",
    profileName
  );
}

export function parsePort(input, fallbackPort) {
  if (!input) return fallbackPort;
  if (/^\d+$/.test(String(input))) return Number(input);
  try {
    const url = new URL(String(input));
    return Number(url.port || fallbackPort);
  } catch {
    return fallbackPort;
  }
}

export function buildDebugUrl(input, fallbackPort) {
  const port = parsePort(input, fallbackPort);
  return `http://127.0.0.1:${port}`;
}

export async function ensureChromePath() {
  await fs.access(CHROME_PATH);
  return CHROME_PATH;
}

export async function spawnChromeWithProfile({
  debugPort,
  profileName,
  startUrls = [],
  extraArgs = [],
}) {
  const chromeExe = await ensureChromePath();
  const userDataDir = buildProfileDir(profileName);
  await fs.mkdir(userDataDir, { recursive: true });
  const args = [
    `--remote-debugging-port=${debugPort}`,
    `--user-data-dir=${userDataDir}`,
    "--no-first-run",
    "--no-default-browser-check",
    ...extraArgs,
    ...(startUrls.length ? startUrls : ["about:blank"]),
  ];
  const child = spawn(chromeExe, args, {
    detached: true,
    stdio: "ignore",
  });
  child.unref();
  return {
    pid: child.pid,
    chromeExe,
    userDataDir,
    debugPort,
  };
}

export async function connectOrLaunchChrome({
  debugPort,
  profileName,
  startUrls = [],
  attempts = 25,
  delayMs = 1000,
}) {
  const debugUrl = `http://127.0.0.1:${debugPort}`;
  try {
    const browser = await chromium.connectOverCDP(debugUrl);
    return {
      browser,
      debugUrl,
      launched: false,
      userDataDir: buildProfileDir(profileName),
    };
  } catch {
    await spawnChromeWithProfile({ debugPort, profileName, startUrls });
  }

  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const browser = await chromium.connectOverCDP(debugUrl);
      return {
        browser,
        debugUrl,
        launched: true,
        userDataDir: buildProfileDir(profileName),
      };
    } catch {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }

  throw new Error(`Unable to connect to Chrome over CDP at ${debugUrl}`);
}
