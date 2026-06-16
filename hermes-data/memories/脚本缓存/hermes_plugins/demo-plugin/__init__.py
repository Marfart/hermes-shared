"""
__init__.py — Hermes Plugin Entry Point
=======================================
注册系统监控工具、钩子和 slash 命令

📦 安装:
  1. 把 demo-plugin 文件夹复制到 ~/.hermes/plugins/ 目录下
  2. 重启 Hermes 或者运行 hermes plugins enable system-monitor
  3. 通过 /reset 就可以使用 sys_info / sys_disk_usage / sys_uptime 工具

🔧 注册了什么:
  - sys_info(toolset=system)  — 系统基本信息/详细信息
  - sys_disk_usage(toolset=system) — 磁盘使用情况
  - sys_uptime(toolset=system)  — 系统运行时间
  - /sysstat (slash command)   — CLI/Gateway 快捷查看
  - pre_tool_call hook         — 每次工具调用前记录日志
"""

from pathlib import Path
from . import schemas
from . import tools

# 拿到插件自有目录，方便引用 data/ 等
PLUGIN_DIR = Path(__file__).parent


def _on_tool_call(tool_name, params, result):
    """Hook: 每次工具调用后记录到日志"""
    print(f"[system-monitor] tool called: {tool_name}")


def register(ctx):
    """Hermes 插件入口 — register() 是唯一的约定接口"""

    # ─── 注册工具 ─────────────────────────────────────────
    ctx.register_tool(
        name="sys_info",
        toolset="system",
        schema=schemas.SYS_INFO_SCHEMA,
        handler=tools.handle_sys_info,
        description="Get system information: OS, CPU, RAM, hostname",
    )

    ctx.register_tool(
        name="sys_disk_usage",
        toolset="system",
        schema=schemas.SYS_DISK_USAGE_SCHEMA,
        handler=tools.handle_disk_usage,
        description="Check disk usage for all drives",
    )

    ctx.register_tool(
        name="sys_uptime",
        toolset="system",
        schema=schemas.SYS_UPTIME_SCHEMA,
        handler=tools.handle_uptime,
        description="Check how long the system has been running",
    )

    # ─── 注册钩子 ─────────────────────────────────────────
    ctx.register_hook("pre_tool_call", _on_tool_call)

    # ─── 注册 Slash 命令 ──────────────────────────────────
    def handle_sysstat(name: str, args: str, **kwargs):
        """处理 /sysstat 命令 — 快速查看系统状态"""
        return {
            "type": "text",
            "content": (
                "📊 **系统状态速览**\n\n"
                f"OS: {__import__('platform').system()} "
                f"{__import__('platform').release()}\n"
                f"主机名: {__import__('platform').node()}\n"
                f"Python: {__import__('platform').python_version()}"
            ),
        }

    ctx.register_command(
        name="sysstat",
        handler=handle_sysstat,
        description="Quick system status overview",
    )

    # ─── 注册 CLI 命令 ──────────────────────────────────
    def setup_sysmon(subparsers):
        p = subparsers.add_parser(
            "sysmon", help="System monitor subcommands"
        )
        p.add_argument("action", choices=["info", "disk", "uptime"])
        p.add_argument("--path", help="Disk path to check")

    def run_sysmon(args, **kwargs):
        if args.action == "info":
            return tools.handle_sys_info({"detail": "basic"})
        elif args.action == "disk":
            return tools.handle_disk_usage({"path": args.path or ""})
        elif args.action == "uptime":
            return tools.handle_uptime({"format": "human"})

    ctx.register_cli_command(
        name="sysmon",
        help="Check system status from the CLI",
        setup_fn=setup_sysmon,
        handler_fn=run_sysmon,
    )

    print(f"[system-monitor] plugin loaded from {PLUGIN_DIR}")