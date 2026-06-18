"""
BLIIOT CRM 一键跟进 — 快速添加跟进记录
用法：
  python crm_quick.py add <客户ID> "<内容>" [--type 邮件/WhatsApp/电话/报价/跟进] [--sync]
  python crm_quick.py add-by-name "<客户名称>" "<内容>" [--type ...] [--sync]
  python crm_quick.py customer "<客户名称或ID>"     # 查客户信息和跟进历史
  python crm_quick.py search "<关键词>"              # 搜索跟进记录
  python crm_quick.py stats                          # 统计
  python crm_quick.py sync                           # 同步到富通
  python crm_quick.py excel                          # 刷新Excel
"""
import sys, os, json, subprocess

CRM_DIR = os.path.join(os.environ.get('LOCALAPPDATA', r'C:\Users\Admin\AppData\Local'),
                       'hermes', 'memories', '脚本缓存', '富通CRM')
CRM_SCRIPT = os.path.join(CRM_DIR, 'bliiot_crm.py')
CUSTOMER_DATA_PATH = os.path.join(CRM_DIR, 'all_customers_raw.json')

def _run_crm(*args):
    """Run the CRM CLI tool"""
    result = subprocess.run(['python', CRM_SCRIPT] + list(args),
                          capture_output=True, text=True, cwd=CRM_DIR)
    return result.stdout, result.stderr

def load_customers():
    if os.path.exists(CUSTOMER_DATA_PATH):
        with open(CUSTOMER_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def find_customer(query):
    """Find customer by name/ID and return info"""
    customers = load_customers()
    query = query.strip().lower()
    
    # Try exact ID match first
    if query.isdigit():
        cid = int(query)
        for c in customers:
            if c.get('id') == cid:
                return c
    
    # Try name match
    matches = []
    for c in customers:
        name = (c.get('name') or '').lower()
        contact = (c.get('contactName') or '').lower()
        code = (c.get('code') or '').lower()
        if query in name or query in contact or query == code.lower():
            matches.append(c)
    
    if matches:
        return matches[0]  # Best match
    return None

def add_followup(customer_id, content, type_='跟进', sync=False):
    """Add a follow-up record"""
    args = ['add', str(customer_id), content, '--type', type_]
    if sync: args.append('--sync')
    stdout, stderr = _run_crm(*args)
    return stdout, stderr

def add_followup_by_name(customer_name, content, type_='跟进', sync=False):
    """Find customer by name then add follow-up"""
    customer = find_customer(customer_name)
    if not customer:
        return f"❌ 未找到客户「{customer_name}」\n建议先用 customer 命令查准确名称", ''
    cid = customer.get('id')
    name = customer.get('name', '')
    return add_followup(cid, content, type_, sync), name

def show_customer(query):
    """Show customer info and follow-up history"""
    customer = find_customer(query)
    if not customer:
        output = [f"❌ 未找到客户「{query}」"]
        # Show similar names
        customers = load_customers()
        query_lower = query.lower()
        similar = []
        for c in customers:
            n = (c.get('name') or '').lower()
            if query_lower in n:
                similar.append(c.get('name'))
        if similar:
            output.append(f"\n📋 相似客户 ({len(similar)}):")
            for s in similar[:10]:
                output.append(f"  • {s}")
        return '\n'.join(output)
    
    cid = customer.get('id')
    name = customer.get('name', '')
    contact = customer.get('contactName', '')
    email = customer.get('contactEmail', '')
    phone = customer.get('contactMobile', '')
    region = customer.get('displayRegion', '')
    source = customer.get('source', '')
    grade = customer.get('grade', '')
    website = customer.get('webSite', '')
    desc = customer.get('description', '')
    code = customer.get('code', '')
    
    output = [
        f"📋 客户信息: {name}",
        f"   ID: {cid}  |  代码: {code}",
        f"   联系人: {contact}",
        f"   邮箱: {email}",
        f"   手机: {phone}",
        f"   国家: {region}",
        f"   来源: {source}  |  等级: {grade}",
        f"   网站: {website or '无'}",
        f"   备注: {desc or '无'}",
        "",
        f"💬 跟进记录:",
    ]
    
    # Get follow-up history
    stdout, _ = _run_crm('list', '--customer', str(cid), '--limit', '10')
    output.append(stdout if stdout.strip() else "  暂无跟进记录")
    
    return '\n'.join(output)

def cmd_help():
    return """BLIIOT CRM 一键跟进工具 🚀

用法:
  python crm_quick.py add <客户ID> "<内容>" [--type 类型] [--sync]
  python crm_quick.py add-by-name "<客户名>" "<内容>" [--type 类型] [--sync]
  python crm_quick.py customer "<客户名/ID>"    ← 查客户+跟进记录
  python crm_quick.py search "<关键词>"         ← 搜索跟进
  python crm_quick.py stats                    ← 统计
  python crm_quick.py excel                    ← 刷新Excel
  python crm_quick.py sync                     ← 同步到富通

跟进类型: 跟进, 邮件, WhatsApp, 电话, 报价, 订单, 会议, 备注

示例:
  python crm_quick.py add 235327923 "发了BL460报价，客户说下周回复" --type 邮件 --sync
  python crm_quick.py add-by-name "hsinsight" "WhatsApp联系，已读产品资料" --type WhatsApp
  python crm_quick.py customer "hsinsight"
"""

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(cmd_help())
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'add':
        if len(sys.argv) < 4:
            print("❌ 用法: add <客户ID> \"<内容>\" [--type X] [--sync]")
            sys.exit(1)
        cid = int(sys.argv[2])
        content = sys.argv[3]
        type_ = '跟进'
        sync = False
        if '--type' in sys.argv:
            ti = sys.argv.index('--type')
            type_ = sys.argv[ti + 1]
        if '--sync' in sys.argv:
            sync = True
        stdout, stderr = add_followup(cid, content, type_, sync)
        print(stdout)
        if stderr: print(stderr)
    
    elif cmd == 'add-by-name':
        if len(sys.argv) < 4:
            print("❌ 用法: add-by-name \"<客户名>\" \"<内容>\" [--type X] [--sync]")
            sys.exit(1)
        customer_name = sys.argv[2]
        content = sys.argv[3]
        type_ = '跟进'
        sync = False
        if '--type' in sys.argv:
            ti = sys.argv.index('--type')
            type_ = sys.argv[ti + 1]
        if '--sync' in sys.argv:
            sync = True
        result, name = add_followup_by_name(customer_name, content, type_, sync)
        print(result)
    
    elif cmd == 'customer':
        if len(sys.argv) < 3:
            print("❌ 用法: customer \"<客户名/ID>\"")
            sys.exit(1)
        print(show_customer(sys.argv[2]))
    
    elif cmd in ['stats', 'generate-excel', 'excel']:
        stdout, stderr = _run_crm('generate-excel' if cmd in ['excel', 'generate-excel'] else 'stats')
        print(stdout)
    
    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("❌ 用法: search \"<关键词>\"")
            sys.exit(1)
        stdout, stderr = _run_crm('search', sys.argv[2])
        print(stdout)
    
    elif cmd == 'sync':
        print("⚠️ 同步需要连接CDP浏览器:")
        print("   cd " + CRM_DIR)
        print("   node sync_all_pending.mjs")
    
    elif cmd == 'init':
        stdout, stderr = _run_crm('init')
        print(stdout)
    
    else:
        print(f"未知命令: {cmd}")
        print(cmd_help())