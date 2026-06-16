#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WhatsApp 单条测试脚本 — 只发1条给 Agora Automation
"""
import time, json, os, re
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

# === 测试数据：第1个客户 Agora Automation ===
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
print("📱 WhatsApp 单条测试 v1.0")
print("=" * 50)
print(f"\n📋 Target: {TEST_COMPANY}")
print(f"📞 Phone: {TEST_PHONE}")
print(f"💬 Message Length: {len(TEST_MSG)} chars")
print()

# Launch Chrome
print("🔧 Launching Chrome (your profile)...")
opts = Options()
opts.add_argument(f"--user-data-dir={CHROME_USER_DATA}")
opts.add_argument(f"--profile-directory={CHROME_PROFILE}")
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("useAutomationExtension", False)
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_argument("--window-size=1200,800")

driver = webdriver.Chrome(options=opts)
driver.get("https://web.whatsapp.com")

print("\n⏳ Waiting for WhatsApp Web...")
print("📱 If QR code appears → scan with your phone!\n")

try:
    # First try: 30s (if already logged in)
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
        driver.quit()
        exit(1)

print(f"\n📤 Sending test message to {TEST_COMPANY}...")

try:
    # Click new chat button
    nc = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//div[@title="新聊天"]'))
    )
    nc.click()
    time.sleep(1)

    # Search contact
    sb = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    sb.clear()
    sb.send_keys(TEST_PHONE_CLEAN)
    print("⏳ Searching contact...")
    time.sleep(3)

    try:
        # Click contact result
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

        # Send button
        btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@data-tab="11"]'))
        )
        btn.click()
        print("\n✅ ✅ ✅ MESSAGE SENT SUCCESSFULLY! ✅ ✅ ✅")
        
        # Save log
        log = {"company": TEST_COMPANY, "phone": TEST_PHONE,
               "sent_at": datetime.now().isoformat(), "status": "success"}
        with open(os.path.join(LOG_DIR, "test_result.json"), 'w') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    except TimeoutException:
        print(f"\n⚠️ Contact '{TEST_COMPANY}' not found on WhatsApp")
        print("The number might not be registered on WhatsApp")
        log = {"company": TEST_COMPANY, "phone": TEST_PHONE,
               "sent_at": datetime.now().isoformat(), "status": "not_found"}
        with open(os.path.join(LOG_DIR, "test_result.json"), 'w') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

except Exception as e:
    print(f"\n❌ Error: {e}")
    log = {"company": TEST_COMPANY, "phone": TEST_PHONE,
           "sent_at": datetime.now().isoformat(), "status": f"error: {str(e)[:100]}"}
    with open(os.path.join(LOG_DIR, "test_result.json"), 'w') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

print(f"\n{'='*50}")
print("✅ Test complete! Browser stays open for you to see.")
print("📝 Log saved to test_result.json")
print("💡 Close the browser window when done")
print(f"{'='*50}")

input("\nPress Enter to close Chrome...")
driver.quit()
print("Chrome closed. Bye!")