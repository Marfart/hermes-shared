#!/usr/bin/env python3
"""Robust WhatsApp sender - one page per message, proper timeouts"""
import asyncio, json, os, re, sys, time
from playwright.async_api import async_playwright

CDP_URL = "http://127.0.0.1:9223"
MSG_FILE = r"C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\google_maps_latam_fresh_messages_2026-06-02.json"
REGISTRY_FILE = r"C:\Users\Admin\AppData\Local\hermes\memories\buyer-development\whatsapp_sent_registry.json"
RESULTS_DIR = r"C:\Users\Admin\AppData\Local\hermes\memories\buyer-development"
SEND_DELAY = 4  # seconds between sends

def normalize_phone(phone):
    return re.sub(r'\D', '', str(phone or ''))

def load_registry():
    try:
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_registry(reg):
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(reg, f, indent=2)

def is_already_sent(phone, registry):
    digits = normalize_phone(phone)
    if not digits:
        return False
    for r_phone in registry:
        if digits.endswith(r_phone[-7:]) or r_phone.endswith(digits[-7:]):
            return True
    return False

async def send_one_message(page, lead, registry):
    """Returns dict with result"""
    phone = lead['whatsapp_number']
    name = lead['name']
    qid = lead['queue_id']
    message = lead['message']
    style_id = lead.get('style_id', '')
    variant_id = lead.get('variant_id', '')
    
    result = {
        'queue_id': qid,
        'name': name,
        'whatsapp_number': phone,
        'style_id': style_id,
        'variant_id': variant_id,
        'mode': 'send',
        'status': 'pending'
    }
    
    # Check registry
    if is_already_sent(phone, registry):
        result['status'] = 'skipped_already_sent'
        return result
    
    digits = normalize_phone(phone)
    if not digits:
        result['status'] = 'error'
        result['error'] = 'Invalid phone number'
        return result
    
    url = f"https://web.whatsapp.com/send?phone={digits}&text={__import__('urllib.parse').quote(message)}"
    
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=25000)
        await page.wait_for_timeout(3000)
        
        # Check if we're on a valid WhatsApp page
        body = await page.evaluate('document.body.innerText').catch(lambda: '')
        
        # Try to find send button
        send_found = False
        for selector in [
            'button[aria-label="发送"]',
            'button[aria-label="Send"]',
            'span[data-icon="send"]',
            'button:has(span[data-icon="send"])'
        ]:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=3000):
                    await btn.click(timeout=3000)
                    send_found = True
                    break
            except:
                continue
        
        if not send_found:
            # Try Enter key
            try:
                await page.keyboard.press('Enter')
                send_found = True
            except:
                pass
        
        if send_found:
            result['status'] = 'sent'
            result['opened_url'] = url
            # Update registry
            digits_clean = normalize_phone(phone)
            registry[digits_clean] = {
                'phone': digits_clean,
                'first_sent_at': registry.get(digits_clean, {}).get('first_sent_at') or time.strftime('%Y-%m-%dT%H:%M:%S'),
                'last_sent_at': time.strftime('%Y-%m-%d-%H-%M-%S'),
                'names': list(set(registry.get(digits_clean, {}).get('names', []) + [name])),
                'variants': list(set(registry.get(digits_clean, {}).get('variants', []) + [variant_id])),
                'send_count': registry.get(digits_clean, {}).get('send_count', 0) + 1,
            }
        else:
            result['status'] = 'error'
            result['error'] = 'Send button not found (likely not a WhatsApp number)'
    
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)[:200]
    
    return result

async def main():
    with open(MSG_FILE) as f:
        messages = json.load(f)
    
    registry = load_registry()
    
    # Find unsent
    unsent = []
    for m in messages:
        if not is_already_sent(m['whatsapp_number'], registry):
            unsent.append(m)
    
    print(f"Total in queue: {len(messages)}")
    print(f"Already sent: {len(messages) - len(unsent)}")
    print(f"Remaining to try: {len(unsent)}")
    
    if not unsent:
        print("All done! No more to send.")
        return
    
    target = min(20, len(unsent))  # work towards 20 total
    already_sent_this_run = 0
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        
        all_results = []
        
        for i, lead in enumerate(unsent[:target]):
            print(f"\n--- [{i+1}/{target}] {lead['name'][:35]} | {lead['whatsapp_number']} ---")
            
            page = await context.new_page()
            try:
                result = await send_one_message(page, lead, registry)
                all_results.append(result)
                status_icon = '✅' if result['status'] == 'sent' else ('⏭️' if result['status'] == 'skipped_already_sent' else '❌')
                print(f"  {status_icon} {result['status']}: {result.get('error','')[:80]}")
                if result['status'] == 'sent':
                    already_sent_this_run += 1
            except Exception as e:
                result = {'queue_id': lead['queue_id'], 'name': lead['name'], 'whatsapp_number': lead['whatsapp_number'], 'status': 'error', 'error': str(e)[:200]}
                all_results.append(result)
                print(f"  ❌ error: {str(e)[:80]}")
            finally:
                await page.close().catch(lambda: None)
            
            if result['status'] == 'sent':
                save_registry(registry)
            
            if SEND_DELAY > 0:
                await asyncio.sleep(SEND_DELAY)
        
        await browser.close()
    
    # Save results
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S')
    out_path = os.path.join(RESULTS_DIR, f"whatsapp_bulk_send_results_{timestamp}.json")
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    sent_count = sum(1 for r in all_results if r['status'] == 'sent')
    skipped_count = sum(1 for r in all_results if r['status'] == 'skipped_already_sent')
    error_count = sum(1 for r in all_results if r['status'] == 'error')
    
    print(f"\n{'='*50}")
    print(f"✅ Sent this batch: {sent_count}")
    print(f"⏭️  Skipped (already sent): {skipped_count}")
    print(f"❌ Errors (not WhatsApp): {error_count}")
    print(f"📁 Results saved: {out_path}")
    print(f"{'='*50}")

if __name__ == '__main__':
    asyncio.run(main())