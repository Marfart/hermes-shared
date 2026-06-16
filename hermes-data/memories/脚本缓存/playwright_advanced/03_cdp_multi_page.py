#!/usr/bin/env python3
"""
Playwright CDP 连接 + 多页面并发

学习要点：
1. 连接到已有 Chrome 实例（CDP 9223/9226 端口）
2. 多页面并行抓取
3. 页面池复用
4. CDP 浏览器 vs 新启动浏览器的差异

用法：
  # 连接到已打开的 Chrome CDP
  python 03_cdp_multi_page.py cdp

  # 启动新浏览器并并行抓取
  python 03_cdp_multi_page.py parallel
"""

import sys
import asyncio
from playwright.async_api import async_playwright


async def connect_cdp(port: int = 9223):
    """
    连接到已运行的 Chrome CDP 实例
    适合场景：利用已有的登录态、cookie、session
    """
    endpoint_url = f"http://127.0.0.1:{port}"

    async with async_playwright() as p:
        print(f"[*] 正在连接 CDP: {endpoint_url}")
        try:
            browser = await p.chromium.connect_over_cdp(endpoint_url)
        except Exception as e:
            print(f"[✗] CDP 连接失败: {e}")
            print("[!] 请确保 Chrome 已用 --remote-debugging-port=9223 启动")
            return

        print(f"[+] 已连接! 浏览器版本: {browser.version}")

        # 获取所有已有标签页
        contexts = browser.contexts
        pages = browser.contexts[0].pages if contexts else []
        print(f"[*] 已有标签页: {len(pages)}")

        # 创建新标签页（不干扰已有的）
        context = contexts[0] if contexts else await browser.new_context()
        page = await context.new_page()

        await page.goto("https://httpbin.org/ip", wait_until="networkidle")
        content = await page.text_content("body")
        print(f"[+] CDP 浏览器 IP 信息: {content}")

        print("[*] 提示: CDP 浏览器可以看到你的真实登录态 Cookie")
        print("[*] 适合用来访问需要登录的网站")

        # 不要关闭 CDP 浏览器 - 它还可能被用户使用
        # await browser.close()


async def parallel_scrape(urls: list[str]):
    """
    多页面并行抓取
    优势：同时打开多个页面，比串行快 N 倍
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        async def fetch_one(url: str, idx: int) -> dict:
            """单个页面抓取逻辑"""
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                title = await page.title()
                return {"idx": idx, "url": url, "title": title, "status": "ok"}
            except Exception as e:
                return {"idx": idx, "url": url, "title": str(e), "status": "error"}
            finally:
                await page.close()

        # 并行发射所有请求
        tasks = [fetch_one(url, i) for i, url in enumerate(urls)]
        results = await asyncio.gather(*tasks)

        print(f"[+] 并行抓取 {len(urls)} 个页面完成:")
        for r in results:
            icon = "[✓]" if r["status"] == "ok" else "[✗]"
            print(f"  {icon} #{r['idx']} {r['title'][:60]}")

        await browser.close()


async def page_pool_demo():
    """
    页面池模式 - 复用浏览器上下文
    优势：共享 Cookie/登录态，减少创建开销
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 ..."
            )
        )

        # 创建一个页面池（3个页面）
        pool = []
        for i in range(3):
            page = await context.new_page()
            pool.append(page)

        print(f"[+] 页面池已创建：{len(pool)} 个页面")
        print("[*] 所有页面共享同一个 cookie jar 和上下文")

        urls = [
            "https://httpbin.org/cookies/set/session_id/abc123",
            "https://httpbin.org/cookies",
            "https://httpbin.org/user-agent",
        ]

        for i, (page, url) in enumerate(zip(pool, urls)):
            await page.goto(url, wait_until="domcontentloaded")
            body = await page.text_content("body")
            print(f"\n[页面 {i}] {url}")
            print(f"  -> {body[:120]}")

        # 全部关闭
        for page in pool:
            await page.close()
        await browser.close()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "help"

    if mode == "cdp":
        asyncio.run(connect_cdp(port=9223))
    elif mode == "parallel":
        test_urls = [
            "https://httpbin.org/anything?q=1",
            "https://httpbin.org/anything?q=2",
            "https://httpbin.org/anything?q=3",
            "https://httpbin.org/anything?q=4",
            "https://httpbin.org/anything?q=5",
        ]
        asyncio.run(parallel_scrape(test_urls))
    elif mode == "pool":
        asyncio.run(page_pool_demo())
    else:
        print(__doc__)
        print("\n用法: python 03_cdp_multi_page.py [cdp|parallel|pool]")