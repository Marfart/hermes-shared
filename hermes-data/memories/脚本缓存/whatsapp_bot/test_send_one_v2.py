#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WhatsApp 单条测试 v2 — 先杀旧Chrome再启动，修复 DevToolsActivePort
"""
import time, json, os, subprocess, sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

CHROME_USER_DATA = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE = "Default"
LOG_DIR = r"C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\whatsapp_bot"

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

# === Step 1: Kill all existing Chrome ===
print("🔪 Killing existing Chrome processes...")
subprocess.run("taskkill /F /IM chrome.exe 2>nul", shell=True)
time.sleep(2)

# === Step 2: Start Chrome with remote debugging ===
print("🚀 Starting Chrome with remote debugging port...")
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
debug_port = "9222"

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

# === Step 3: Connect via remote debugging ===
print("🔗 Connecting to Chrome via DevTools...")
opts = Options()
opts.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")

try:
    driver = webdriver.Chrome(options=opts)
    print("✅ Connected to Chrome!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("🔄 Retrying with fresh approach...")
    time.sleep(3)
    driver = webdriver.Chrome(options=opts)
    print("✅ Connected!")

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
        input("Press Enter to close...")
        driver.quit()
        sys.exit(1)

# === Step 4: Send message ===
print(f"\n📤 Sending test message to {TEST_COMPANY}...")

try:
    nc = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@title="新聊天"]'))
    )
    nc.click()
    time.sleep(1.5)

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
print("✅ Test complete! Browser stays open.")
print("💡 Check the WhatsApp Web window on your screen!")
print("💡 Close the window or press Enter when done")
print(f"{'='*50}")

input("\nPress Enter to close Chrome...")
driver.quit()
chrome_proc.kill()
print("Done!")