#!/usr/bin/env python3
"""
Playwright 网络拦截技术
核心功能：拦截/修改请求和响应

学习要点：
1. page.route() - 拦截所有请求
2. 修改请求头（添加 API key 等）
3. Mock API 响应（无需后端也能测试）
4. 拦截图片/CSS 减少带宽
5. 捕获网络请求日志（console 级别）

用法：python 02_network_intercept.py
"""

import asyncio
import json
from playwright.async_api import async_playwright


async def demo_intercept():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        context = await browser.new_context()

        # 拦截器日志
        intercepted = {"requests": [], "blocked": 0}

        async def handle_route(route, request):
            url = request.url
            rtype = request.resource_type

            # 1. 拦截并记录
            intercepted["requests"].append(
                {"url": url[:100], "method": request.method, "type": rtype}
            )

            # 2. 阻止图片和字体（节省带宽）
            if rtype in ("image", "font", "media"):
                intercepted["blocked"] += 1
                await route.abort("blockedbyclient")
                return

            # 3. 修改某些 API 请求头
            headers = dict(request.headers)
            if "api.example.com" in url:
                headers["X-Custom-Header"] = "hermes-stealth"
                headers["Authorization"] = "Bearer mock-token-12345"

            # 4. 转发（或修改后转发）
            await route.continue_(headers=headers)

        # 注册路由拦截
        await context.route("**/*", handle_route)

        page = await context.new_page()

        # 5. Mock API 响应示例
        async def mock_api(route, request):
            """拦截特定 API 并返回 mock 数据"""
            if "jsonplaceholder.typicode.com" in request.url:
                mock_data = [
                    {"id": 1, "title": "Mock Post 1", "body": "This is mocked!"},
                    {"id": 2, "title": "Mock Post 2", "body": "No real API call needed"},
                ]
                await route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(mock_data),
                )
            else:
                await route.continue_()

        # 创建第二个页面演示 mock
        page2 = await context.new_page()
        await page2.route("**/posts*", mock_api)

        # 访问真实页面测试拦截
        print("[*] 测试请求拦截...")
        await page.goto("https://httpbin.org/anything", wait_until="networkidle")

        print(f"[+] 拦截到 {len(intercepted['requests'])} 个请求")
        print(f"[+] 阻止了 {intercepted['blocked']} 个资源(图片/字体)")
        print(f"\n前5个请求:")
        for r in intercepted["requests"][:5]:
            print(f"  {r['method']} {r['type']:>8} | {r['url']}")

        # 测试 mock
        print(f"\n[*] 测试 API Mock...")
        await page2.goto(
            "https://jsonplaceholder.typicode.com/posts", wait_until="networkidle"
        )
        content = await page2.content()
        if "Mock Post 1" in content:
            print("[✓] Mock 数据成功返回！")
        else:
            print("[!] Mock 未生效，检查路由模式")

        await browser.close()
        print("\n[✓] 网络拦截演示完成")


async def demo_console_capture():
    """演示：捕获浏览器 console 消息"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        page = await browser.new_page()

        messages = []

        def on_console(msg):
            messages.append(f"[{msg.type}] {msg.text}")

        page.on("console", on_console)

        await page.goto("https://httpbin.org/anything", wait_until="domcontentloaded")
        # 注入一些 console 输出
        await page.evaluate("console.log('Hello from Playwright!')")
        await page.evaluate("console.warn('This is a warning')")
        await page.evaluate("console.error('This is an error')")

        for m in messages:
            print(f"  {m}")

        await browser.close()


if __name__ == "__main__":
    print("=== 网络拦截 ===\n")
    asyncio.run(demo_intercept())
    print("\n=== Console 捕获 ===\n")
    asyncio.run(demo_console_capture())