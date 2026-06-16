# Model Fallback Management — Reference

## 模型切换命令

```bash
# 切换主模型（无 get 子命令，直接读 config.yaml 确认）
hermes config set model.provider <provider>
hermes config set model.model <model>

# 验证当前模型（直接读 yaml）
python -c "
import yaml, os
from pathlib import Path
cfg = yaml.safe_load(Path(os.environ['LOCALAPPDATA'], 'hermes', 'config.yaml').read_text())
m = cfg.get('model', {})
print(f\"{m.get('provider','?')}/{m.get('model','?')}\")
"
```

**⚠️ `hermes config` 没有 `get` 子命令**，只有 `show/edit/set/path/env-path/check/migrate`。读取当前值需直接解析 config.yaml。

## 当前模型配置（2026-06-17）

| 角色 | Provider | Model | 说明 |
|------|----------|-------|------|
| **主模型** | `openrouter` | `owl-alpha` | 优先使用 |
| **备用模型** | `ollama-cloud` | `glm-5.1` | 主模型超时/限速时切换 |

## Fallback 监控脚本

脚本位置：`%LOCALAPPDATA%/hermes/scripts/model_fallback_monitor.py`

**逻辑：**
1. 每 120 秒用轻量请求（max_tokens=5）测试主模型健康
2. 连续 2 次失败（超时/429/连接失败）→ 自动切到备用模型
3. 切到备用后，等主模型恢复 + 300 秒冷却期 → 自动切回主模型
4. 状态持久化到 `model_fallback_state.json`

**运行方式：**
```bash
# 单次检查
python model_fallback_monitor.py --once

# 守护循环（cron 调用）
python model_fallback_monitor.py
```

**Cron 配置：**
```
schedule: every 2m
no_agent: True
script: model_fallback_monitor.py
deliver: local
```

## 飞书模型配置

飞书群消息走同一个 Hermes agent，**没有独立的模型配置**。主模型切换后，飞书回复自动使用新模型。

飞书群的小马 bot 是另一个独立 Hermes 实例，如需切换需在对应机器上操作。

## OpenRouter 注意事项

- API Key 存储在 `.env` 的 `OPENROUTER_API_KEY`
- 429 = Rate Limited（用尽配额），触发 fallback
- 超时（默认 15s）也触发 fallback
- `hermes config set` 即时生效，无需重启 gateway

## 常见场景

### 场景：ollama-cloud 超时/限速
```
症状：回复极慢或 429 错误
处理：fallback 脚本自动切到 openrouter/owl-alpha
恢复：ollama 恢复后 5 分钟自动切回
```

### 场景：手动临时切换
```bash
# 临时切到备用
hermes config set model.provider ollama-cloud
hermes config set model.model glm-5.1

# 切回主模型
hermes config set model.provider openrouter
hermes config set model.model owl-alpha
```
