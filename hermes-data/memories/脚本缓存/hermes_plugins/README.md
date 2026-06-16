<!-- SKILL.md -->
---
name: hermes-plugin-development
description: "Hermes Agent 插件开发指南 — 从零创建可用插件"
version: 1.0.0
author: agent (小马)
---

# Hermes Agent 插件开发指南

## 插件结构

```
~/.hermes/plugins/my-plugin/
├── plugin.yaml       # 清单文件（必需）
├── __init__.py       # 入口 register(ctx)（必需）
├── schemas.py        # 工具 JSON schema
├── tools.py          # 工具处理器
└── (data/, templates/, etc.)
```

### plugin.yaml 格式

```yaml
name: my-plugin
version: "1.0.0"
description: "Description here"
requires_env: [API_KEY]      # 可选：需要的环境变量
provides_tools: [tool1, tool2]
provides_hooks: [pre_tool_call]
```

### __init__.py 入口

```python
def register(ctx):
    # 注册工具
    ctx.register_tool(name="my_tool", toolset="my_tools",
                       schema=SCHEMA, handler=handler_fn,
                       description="...")
    
    # 注册钩子
    ctx.register_hook("pre_tool_call", callback_fn)
    
    # 注册 Slash 命令（CLI + Gateway 通用）
    ctx.register_command(name="mycmd", handler=fn, description="...")
    
    # 注册 CLI 子命令
    ctx.register_cli_command(name="mycli", help="...",
                              setup_fn=subparser_fn,
                              handler_fn=handler_fn)
    
    # 注册 Skill（namespace: plugin:skill）
    ctx.register_skill(name="my-skill", path="...")
    
    # 注入消息
    ctx.inject_message(content="...", role="user")
    
    # LLM 调用（借用用户当前模型）
    ctx.llm.complete("prompt")
    ctx.llm.complete_structured("prompt", schema=JSON_SCHEMA)
```

## 可用钩子

| 钩子名 | 触发时机 |
|--------|---------|
| `pre_tool_call` | 工具调用前 |
| `post_tool_call` | 工具调用后 |
| `pre_llm_call` | LLM 推理前 |
| `post_llm_call` | LLM 推理后 |
| `on_session_start` | 会话开始 |
| `on_session_end` | 会话结束 |
| `on_session_reset` | 会话重置 |
| `pre_gateway_dispatch` | Gateway 消息分发前 |
| `pre_approval_request` | 危险命令审批前 |
| `post_approval_response` | 审批响应后 |

## 插件发现源

| 源 | 路径 | 覆盖优先级 |
|----|------|-----------|
| 内置 | `<repo>/plugins/` | 最低 |
| 用户 | `~/.hermes/plugins/` | 中 |
| 项目 | `.hermes/plugins/` | 高（需 HERMES_ENABLE_PROJECT_PLUGINS=true） |
| pip | `hermes_agent.plugins` entry_point | 最高 |

## 插件管理

```bash
hermes plugins                  # 交互式启用/禁用
hermes plugins list             # 列出所有插件
hermes plugins enable <name>    # 启用
hermes plugins disable <name>   # 禁用
hermes plugins install owner/repo  # 从 GitHub 安装
```

插件默认 opt-in，需显式启用后才加载。

## 特殊插件类型

| 类型 | 目录 | 特点 |
|------|------|------|
| Memory Provider | `~/.hermes/plugins/memory/<name>/` | 单例，继承 MemoryProvider |
| Context Engine | `~/.hermes/plugins/context_engine/<name>/` | 单例 |
| Model Provider | `~/.hermes/plugins/model-providers/<name>/` | 单例，register_provider() |
| Platform | `~/.hermes/plugins/platforms/<name>/` | Gateway 频道适配器 |
| Image Gen | `~/.hermes/plugins/image_gen/<name>/` | 图片生成后端 |

## 我们的 Demo 插件

**位置**: `memories/脚本缓存/hermes_plugins/demo-plugin/`
**安装到**: `~/.hermes/plugins/system-monitor-plugin/`
**提供**: `sys_info`, `sys_disk_usage`, `sys_uptime` 三个工具 + `/sysstat` slash 命令
**状态**: 已 hermes plugins enable 为 enabled