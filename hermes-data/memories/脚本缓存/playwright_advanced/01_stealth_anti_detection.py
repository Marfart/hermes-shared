#!/usr/bin/env python3
"""
Playwright 反检测技术脚本
核心功能：通过 stealth 插件 + 手动补丁绕过 bot 检测

学习要点：
1. playwright-stealth 自动补丁（webdriver/plugins/chrome等）
2. 手动设置 user-agent / viewport / locale / timezone
3. 自定义 navigator.webdriver 覆盖
4. 通过 https://bot.sannysoft.com/ 验证隐身效果

用法：python 01_stealth_anti_detection.py [url]
"""

import sys
import asyncio
from playwright.async_api import async_playwright


async def test_stealth(url: str = "https://bot.sannysoft.com"):
    async with async_playwright() as p:
        # 1. 启动带参数的浏览器（用已有 chromium-1223）
        # Playwright 1.59 需要 chromium-1217，但 CDN 下载太慢
        # 直接用已有的 1223 版本通过 executable_path
        chrome_path = (
            r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
            r"\chrome-win64\chrome.exe"
        )
        launch_kwargs = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",  # 关键：关闭自动化标记
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            "executable_path": chrome_path,
        }
        browser = await p.chromium.launch(**launch_kwargs)

        # 2. 创建上下文时手动设置指纹参数
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},  # 纽约坐标
            permissions=["geolocation"],
            color_scheme="light",
        )

        # 3. 注入 stealth 脚本（关键反检测步骤）
        # 在导航前注入 stealth JS 补丁
        await context.add_init_script(
            """
            // 覆盖 navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // 覆盖 chrome 属性
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };

            // 模拟插件数组
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // 模拟语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            """
        )

        page = await context.new_page()
        print(f"[*] 正在访问: {url}")
        await page.goto(url, wait_until="networkidle")

        # 4. 验证结果
        title = await page.title()
        print(f"[+] 页面标题: {title}")

        # 检查关键检测指标
        checks = await page.evaluate(
            """
            () => ({
                webdriver: navigator.webdriver,
                plugins: navigator.plugins.length,
                languages: navigator.languages[0],
                userAgent: navigator.userAgent.substring(0, 50),
            })
        """
        )
        print(f"[+] 检测结果:")
        for k, v in checks.items():
            print(f"    {k}: {v}")

        # 5. 截图保存
        screenshot_path = (
            "C:\\Users\\Admin\\AppData\\Local\\hermes\\memories\\"
            "脚本缓存\\playwright_advanced\\stealth_test.png"
        )
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"[+] 截图已保存: {screenshot_path}")

        await browser.close()
        print("[✓] 浏览器已关闭")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://bot.sannysoft.com"
    asyncio.run(test_stealth(url))