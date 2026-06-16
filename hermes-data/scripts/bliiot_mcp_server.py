"""
BLIIOT工具包 MCP Server — 小马学习了FastMCP 3.x后亲手写的
给Hermes提供：客户查询、WhatsApp模板渲染、知识库搜索
"""
from fastmcp import FastMCP
import json, os, re
from datetime import datetime

mcp = FastMCP("bliiot-tools", version="1.0.0")

# ─── 客户开发管道工具 ───

@mcp.tool()
def search_customer_leads(keyword: str, country: str = "") -> str:
    """搜索BLIIOT客户开发管道中的客户记录"""
    base = os.path.expanduser("~/Desktop/Working")
    results = []
    
    # 搜索Excel/JSON客户文件
    for root, dirs, files in os.walk(base):
        for f in files:
            if f.endswith((".xlsx", ".json", ".csv")) and "lead" in f.lower():
                path = os.path.join(root, f)
                results.append(f"[{f}]({path})")
    
    if not results:
        return f"⚠️ 未找到客户文件。请先生成客户名单。"
    
    return f"找到 {len(results)} 个客户文件:\n" + "\n".join(results[:10])

@mcp.tool()
def count_knowledge_files() -> str:
    """统计自学习系统已积累的知识量"""
    base = os.path.expanduser("~/AppData/Local/hermes/memories/自学习系统/知识库")
    total_size = 0
    file_count = 0
    for f in os.listdir(base):
        if f.endswith(".md"):
            fp = os.path.join(base, f)
            sz = os.path.getsize(fp)
            total_size += sz
            file_count += 1
    
    obs_base = os.path.expanduser("~/Documents/Obsidian Vault/01-学习笔记/自学习系统")
    note_count = 0
    for root, dirs, files in os.walk(obs_base):
        note_count += sum(1 for f in files if f.endswith(".md") and not f.startswith("_"))
    
    return json.dumps({
        "knowledge_base_files": file_count,
        "knowledge_base_size_kb": round(total_size / 1024, 1),
        "obsidian_notes": note_count,
        "last_check": datetime.now().strftime("%H:%M")
    }, ensure_ascii=False)

@mcp.tool()
def check_watchdog_status() -> str:
    """查看小马所有后台看门狗和监控系统的运行状态"""
    import subprocess
    try:
        r = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq hermes.exe', '/NH'],
            capture_output=True, text=True, timeout=5
        )
        hermes_count = len([l for l in r.stdout.split('\n') if 'hermes' in l.lower() and 'No tasks' not in l])
    except:
        hermes_count = -1
    
    states = {
        "hermes_processes": hermes_count,
        "gateway": "running" if hermes_count > 0 else "unknown",
        "time": datetime.now().strftime("%H:%M:%S")
    }
    return json.dumps(states, ensure_ascii=False)

@mcp.tool()
def generate_whatsapp_greeting(style: str = "default") -> str:
    """生成WhatsApp开发信的开头问候语"""
    greetings = {
        "default": "Good day",
        "warm": "I hope you're having a wonderful day",
        "professional": "I hope this message finds you well",
        "casual": "Hope you're enjoying a good week"
    }
    return greetings.get(style, greetings["default"])

@mcp.resource("data://system-battery")
def system_status() -> str:
    """小马系统状态概览"""
    return "🤖 小马正在运行 · 2026-06-06 · dall-e-3"

@mcp.prompt()
def whatsapp_outreach(company: str, country: str, product: str) -> str:
    """WhatsApp开发信模板生成器"""
    return f"""You are writing a WhatsApp business development message for BLIIOT (Shenzhen Bliiot Technology Co., Ltd).
Target company: {company} in {country}
Target product: {product}

Generate a 4-paragraph message:
1. Greeting + self-introduction
2. Observation about their industry + how BLIIOT's {product} can help
3. Call to action (short catalog)
4. Professional closing

Keep each paragraph under 3 lines. Use a warm but professional tone."""

if __name__ == "__main__":
    mcp.run(transport="stdio")