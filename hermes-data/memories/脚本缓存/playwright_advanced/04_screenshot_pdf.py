#!/usr/bin/env python3
"""
Playwright 截图 + PDF 生成 + 视觉对比

学习要点：
1. page.screenshot() - 全页/元素截图
2. page.pdf() - PDF 生成（需要 Chromium）
3. pixelmatch 进行视觉差分比较
4. 定时截图监控页面变化

用法：python 04_screenshot_pdf.py
"""

import asyncio
import hashlib
from playwright.async_api import async_playwright

SCREENSHOT_DIR = (
    "C:\\Users\\Admin\\AppData\\Local\\hermes\\memories\\"
    "脚本缓存\\playwright_advanced\\"
)


async def demo_screenshot():
    """截图技术合集"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 720})

        await page.set_content("""<html><body><h1>Test Page</h1><p>Hello from Playwright!</p></body></html>""")

        # 1. 完整页面截图
        await page.screenshot(
            path=f"{SCREENSHOT_DIR}full_page.png", full_page=True
        )
        print("[✓] 全页截图: full_page.png")

        # 2. 视口截图（只拍当前显示区域）
        await page.screenshot(
            path=f"{SCREENSHOT_DIR}viewport.png", full_page=False
        )
        print("[✓] 视口截图: viewport.png")

        # 3. 元素截图
        element = await page.query_selector("h1")
        if element:
            await element.screenshot(path=f"{SCREENSHOT_DIR}element_h1.png")
            print("[✓] 元素截图: element_h1.png")

        # 4. 带裁剪的截图
        await page.screenshot(
            path=f"{SCREENSHOT_DIR}clipped.png",
            clip={"x": 0, "y": 0, "width": 400, "height": 200},
        )
        print("[✓] 裁剪截图: clipped.png")

        await browser.close()


async def demo_pdf_generation():
    """PDF 生成 - 将网页转为 PDF"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        page = await browser.new_page()

        # 创建带内容的测试页面
        html_content = """
        <html>
        <head><style>
            body { font-family: Arial; padding: 40px; }
            h1 { color: #2563eb; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            .section { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background: #2563eb; color: white; }
        </style></head>
        <body>
            <h1>BLIIoT Product Catalog</h1>
            <div class="section">
                <h2>Industrial IoT Gateways</h2>
                <table>
                    <tr><th>Model</th><th>CPU</th><th>Features</th></tr>
                    <tr><td>BL116</td><td>ARM Cortex-A72</td><td>4G LTE, WiFi, Edge Computing</td></tr>
                    <tr><td>BL118</td><td>ARM Cortex-A53</td><td>Dual Ethernet, Modbus</td></tr>
                </table>
            </div>
            <div class="section">
                <h2>ARM Edge Controllers</h2>
                <p>ARMxy series with dual-core processors, AI acceleration support.</p>
            </div>
        </body>
        </html>
        """

        await page.set_content(html_content)

        # 生成 PDF
        pdf_path = f"{SCREENSHOT_DIR}demo_catalog.pdf"
        await page.pdf(
            path=pdf_path,
            format="A4",
            margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"},
            print_background=True,
        )
        print(f"[✓] PDF 已生成: {pdf_path}")

        # 检查 PDF 文件大小
        import os

        size = os.path.getsize(pdf_path)
        print(f"    文件大小: {size / 1024:.1f} KB")

        await browser.close()
        print("[*] 提示: Playwright PDF 适合生成报告、发票、产品目录")


async def demo_visual_diff():
    """
    视觉对比 - 使用哈希值检测页面变化
    注意：完整 pixelmatch 需要安装 pillow + pixelmatch
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=(
                r"C:\Users\Admin\AppData\Local\ms-playwright\chromium-1223"
                r"\chrome-win64\chrome.exe"
            ),
        )

        page = await browser.new_page()

        # 拍两次截图并对比
        await page.set_content("""<html><body><h1>Visual Diff Test</h1></body></html>""")

        screenshot1 = f"{SCREENSHOT_DIR}diff_before.png"
        await page.screenshot(path=screenshot1)

        with open(screenshot1, "rb") as f:
            hash1 = hashlib.md5(f.read()).hexdigest()

        # 第二次截图（应相同）
        screenshot2 = f"{SCREENSHOT_DIR}diff_after.png"
        await page.screenshot(path=screenshot2)

        with open(screenshot2, "rb") as f:
            hash2 = hashlib.md5(f.read()).hexdigest()

        if hash1 == hash2:
            print("[✓] 视觉对比：页面未变化 (哈希匹配)")
        else:
            print("[!] 视觉对比：页面已变化! (哈希不匹配)")

        # 如果有 pillow，可以做像素级对比
        try:
            from PIL import Image
            import numpy as np

            img1 = Image.open(screenshot1)
            img2 = Image.open(screenshot2)
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            diff_pixels = np.sum(arr1 != arr2)
            total_pixels = arr1.size
            pct = diff_pixels / total_pixels * 100
            print(f"    像素差异: {diff_pixels}/{total_pixels} ({pct:.2f}%)")
        except ImportError:
            print("[*] 安装 pillow+np 可做像素级对比: pip install pillow numpy")

        await browser.close()


if __name__ == "__main__":
    import os

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    print("=== 截图技术 ===\n")
    asyncio.run(demo_screenshot())

    print("\n=== PDF 生成 ===\n")
    asyncio.run(demo_pdf_generation())

    print("\n=== 视觉对比 ===\n")
    asyncio.run(demo_visual_diff())