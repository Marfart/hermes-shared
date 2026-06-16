#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WhatsApp 单条测试脚本 — 只发1条测试消息
位置: skill 关联脚本，与主脚本同步
"""
import time, json, os, subprocess, sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

CHROME_USER_DATA = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE = "Default"
LOG_DIR = r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\whatsapp_bot"
os.makedirs(LOG_DIR, exist_ok=True)

# === 测试数据（可修改为你想测试的客户） ===
TEST_COMPANY = "Agora Automation"
TEST_PHONE = "+27 82 363 7667"
TEST_PHONE_CLEAN = "27823637667"

TEST_MSG = """Hi Agora Automation,

I'm reaching out from BLIIoT (bliiot.com), an industrial IoT manufacturer based in Shenzhen, China.

We specialize in ARMxy edge controllers, remote I/O modules (Modbus/OPC UA/MQTT/BACnet), IoT gateways, and 4G industrial routers - a complete IIoT product line for industrial automation and SmartGrid applications.

As a system integrator, our products can help you deliver cost-effective automation solutions. Would you be interested in receiving our product catalog and pricing?

Best regards,
Kali
BLIIoT | Shenzhen Beilai Technology Co., Ltd"""

print("=" * 50)
print("📱 WhatsApp 单条测试")
print("=" * 50)
print(f"\n📋 Target: {TEST_COMPANY}")
print(f"📞 Phone: {TEST_PHONE}")
print(f"💬 Message Length: {len(TEST_MSG)} chars")
print()

# === Step 1: Kill old Chrome ===
print("🔪 Killing existing Chrome processes...")
subprocess.run("taskkill /F /IM chrome.exe 2>nul", shell=True)
time.sleep(2)

# === Step 2: Start Chrome with remote debugging ===
print("🚀 Starting Chrome with remote debugging port...")
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
debug_port = "9222"

# 注意：必须等 --remote-debugging-port 参数确保端口监听成功
chrome_proc = subprocess.Popen([
    chrome_path,
    f"--remote-debugging-port={debug_port}",
    f"--user-data-dir={CHROME_USER_DATA}",
    f"--profile-directory={CHROME_PROFILE}",
    "--no-first-run",
    "--disable-blink-features=AutomationControlled",
    "--window-size=1200,800",
    "https://web.whatsapp.com"
])

time.sleep(3)
print(f"✅ Chrome started (PID: {chrome_proc.pid})")

# === Step 3: Connect via DevTools ===
print("🔗 Connecting to Chrome via DevTools...")
opts = Options()
opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

driver = webdriver.Chrome(options=opts)
print("✅ Connected to Chrome!")

# === Step 4: Wait for WhatsApp login ===
print("\n⏳ Waiting for WhatsApp Web...")
print("📱 If QR code appears → scan with your phone!\n")

try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    print("✅ WhatsApp Web ready! (already logged in)")
except TimeoutException:
    print("⏳ QR code scan needed... (waiting up to 120s)")
    try:
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
        )
        print("✅ WhatsApp Web ready! (QR scanned)")
    except TimeoutException:
        print("❌ Login timeout. Please scan QR and run again")
        input("\nPress Enter to close...")
        driver.quit()
        chrome_proc.kill()
        sys.exit(1)

# === Step 5: Send message ===
print(f"\n📤 Sending test message to {TEST_COMPANY}...")

try:
    # New chat button
    nc = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@title="新聊天"]'))
    )
    nc.click()
    time.sleep(1.5)

    # Search
    sb = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    sb.clear()
    sb.send_keys(TEST_PHONE_CLEAN)
    print("⏳ Searching contact...")
    time.sleep(3)

    try:
        contact = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="_ak8q"]'))
        )
        contact.click()
        time.sleep(2)

        # Type message
        mb = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
        )
        mb.click()
        time.sleep(0.5)
        for line in TEST_MSG.split('\n'):
            mb.send_keys(line)
            mb.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.05)
        time.sleep(0.5)

        # Send
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-tab="11"]'))
        )
        btn.click()
        print("\n✅ ✅ ✅ MESSAGE SENT SUCCESSFULLY! ✅ ✅ ✅")

    except TimeoutException:
        print(f"\n⚠️ Contact '{TEST_COMPANY}' not found on WhatsApp")
        print("The number might not be registered on WhatsApp")

except Exception as e:
    print(f"\n❌ Error: {e}")

print(f"\n{'='*50}")
print("✅ Test complete! Browser stays open for you to check.")
print("💡 Close the window or press Enter when done")
print(f"{'='*50}")

input("\nPress Enter to close Chrome...")
driver.quit()
chrome_proc.kill()
print("Done!")