#!/usr/bin/env python
"""
WhatsApp Web 启动器 - 用你的 Chrome 登录 WhatsApp
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, subprocess

# ====== 先检查 Chrome 是不是已经用 debugging 端口在跑了 ======
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
debug_port_busy = sock.connect_ex(('127.0.0.1', 9222))
sock.close()

if debug_port_busy == 0:
    print("✅ Found Chrome with remote debugging on port 9222!")
    print("   Connecting to existing Chrome...")
    opts = Options()
    opts.debugger_address = "127.0.0.1:9222"
    driver = webdriver.Chrome(options=opts)
else:
    print("🔧 Starting Chrome with remote debugging...")
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    
    # Close all existing Chrome instances first (so we can use user-data-dir)
    os.system("taskkill /F /IM chrome.exe 2>nul")
    time.sleep(1)
    
    # Start Chrome with remote debugging
    subprocess.Popen([
        chrome_path,
        f"--remote-debugging-port=9222",
        "--user-data-dir=C:\\Users\\Admin\\AppData\\Local\\Google\\Chrome\\User Data",
    ])
    time.sleep(3)
    
    opts = Options()
    opts.debugger_address = "127.0.0.1:9222"
    driver = webdriver.Chrome(options=opts)

# Go to WhatsApp Web
driver.get("https://web.whatsapp.com")
print("\n" + "=" * 55)
print("📱 WhatsApp Web 已打开！")
print("=" * 55)
print("")
print("⭐ Kali，请在你的电脑屏幕上：")
print("   1️⃣ 看浏览器 - WhatsApp Web 已打开")
print("   2️⃣ 如果显示二维码 → 用手机 WhatsApp 扫码")
print("   3️⃣ 等到聊天列表出现 → 告诉我'好了'")
print("")
print("💡 之后我会自动帮你发开发信！")

input("\n⏳ 按 Enter 继续检查登录状态...")

try:
    # Check if logged in - look for the search bar
    search = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
    print("✅ WhatsApp Web 已登录！Session 已保存~")
except:
    print("⏳ 还没登录？继续等...")
    input("扫码后按 Enter 继续...")
    try:
        search = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]')
        print("✅ 登录成功！")
    except:
        print("❌ 还没登录成功，请检查屏幕")

print("\n💡 Chrome 保持打开。之后运行 whatsapp_bot.py 时直接输入:")
print("   python whatsapp_bot.py")
print("")

keep = input("按 Enter 关闭浏览器...")
driver.quit()
os.system("taskkill /F /IM chrome.exe 2>nul")