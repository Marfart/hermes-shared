---
name: hermes-plugin-development
description: "Hermes Agent 插件开发 — 从零创建可用插件（工具/钩子/命令）"
version: 1.0.0
author: agent
---

# Hermes 插件开发

当需要为 Hermes 添加自定义工具、钩子、slash命令时加载此技能。

## 插件结构
```
~/.hermes/plugins/my-plugin/
├── plugin.yaml      # name/version/description/requires_env/provides_tools
├── __init__.py      # 入口: def register(ctx):
├── schemas.py       # JSON Schema for tools
└── tools.py         # 工具处理器 (return json.dumps(...))
```

## __init__.py 可注册的内容
```python
def register(ctx):
    ctx.register_tool(name=..., toolset=..., schema=..., handler=..., description=...)
    ctx.register_hook("pre_tool_call", callback)
    ctx.register_command(name="slashcmd", handler=fn, description="...")
    ctx.register_cli_command(name="subcmd", help="...", setup_fn=fn, handler_fn=fn)
    ctx.register_skill(name="skill-name", path="...")   # 作为 plugin:skill
    ctx.llm.complete("prompt")                           # 借用用户模型
    ctx.inject_message(content="...", role="user")
```

## 可用钩子
pre/post_tool_call, pre/post_llm_call, on_session_start/end/reset, pre_gateway_dispatch, pre/post_approval_request/response

## 管理命令
```bash
hermes plugins               # 交互式开关
hermes plugins list          # 列表
hermes plugins enable/disable <name>  # 启用/禁用
```

## 我们的 Demo
- 位置: `memories/脚本缓存/hermes_plugins/demo-plugin/`
- 已安装到: `~/.hermes/plugins/system-monitor-plugin/`
- 提供: sys_info, sys_disk_usage, sys_uptime + /sysstat slash命令
- 状态: ✅ 已 enabled（需 /reset 后生效）