#!/usr/bin/env python3
"""Open WhatsApp Web to show QR code for scanning"""
import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument(r'--user-data-dir=C:\Users\Admin\AppData\Local\Google\Chrome\User Data')
chrome_options.add_argument('--profile-directory=Default')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1280,900')
chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

print("🐾 塔奇克马 — 正在打开 WhatsApp Web QR 码...")
print("📱 请用手机 WhatsApp → 已链接的设备 → 扫描二维码")
print("⏳ 窗口会保持打开 3 分钟，扫完后可以关掉")
print()

driver = webdriver.Chrome(options=chrome_options)
driver.get('https://web.whatsapp.com')

try:
    time.sleep(180)
except KeyboardInterrupt:
    pass
finally:
    driver.quit()
    print("✅ 已关闭")