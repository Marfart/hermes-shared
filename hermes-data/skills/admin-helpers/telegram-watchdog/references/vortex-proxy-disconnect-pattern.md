# Vortex/Clash Proxy 断联模式分析

## 事件记录：2026-06-04 16:19:32

### 时间线

| 时间 | 事件 | 日志来源 |
|:----:|------|----------|
| 16:19:32 | ❌ WeChat: `Cannot connect to ilinkai.weixin.qq.com:443 ssl:default [None]` | gateway.log |
| 16:19:33 | ❌ Telegram: `httpx.ConnectError` | gateway.log |
| 16:19:43 | ✅ Telegram 自动恢复（5s 后重连成功） | gateway.log |
| 16:19:51 | Discord 第 10 次重连尝试，再次超时（照常） | gateway.log |

### 关键发现

1. **双平台同时断**（同秒）→ 排除单平台服务器问题
2. **代理端口 7897 活着** → `netstat` 显示 LISTENING，PID 7724 (com.vortex.helper)
3. **curl 直连代理返回 400** → 端口在侦听，但**不转发 HTTPS 流量**
4. **机器处于空闲/背景模式** → user_activity 表显示 idle_seconds>7500，「未知（后台模式）」
5. **TG 自动恢复了但微信没有** → Telegram 有自带的 10 次网络重试机制；Weixin iLink 的重连路径不同

### Vortex/Clash 断流特征

- **不是进程崩溃** — PID 还在，端口还开着
- **不是 DNS 问题** — DNS 诊断全部通过
- **不是 SSL 证书问题** — 报的是连接失败（`ssl:default [None]`），不是证书验证
- **更像代理内部的路由切换/GC** — 代理通了一半（局部 GET 返回 400），但透传 HTTPS 全部超时
- **关联空闲状态** — 这次和多次之前的断联都发生在机器闲置（后台模式/Session 0）时，可能是因为代理在空闲超时后关闭了外部连接池

### 看门狗要改什么

**当前 PROXY 层（Layer 4）的问题：**
```python
# 当前代码 — 直接跳过，不做任何检测
def diag_layer4_proxy(ctx):
    ctx.diag_results.append({"layer": "PROXY", "ok": True, "detail": "代理检测跳过（非必需）"})
```

这是错误的。这个环境下代理是**必需**的——Gateway 的所有 Telegram/Weixin HTTPS 流量都经过 `127.0.0.1:7897`。代理断流时，看门狗会误判为 TARGET 问题并报告网络不可达。

**修复后的检测方案：**
```python
def diag_layer4_proxy(ctx):
    """穿透式代理检测 — 验证代理真实转发 HTTPS 流量，不只是端口开放"""
    proxy_url = "http://127.0.0.1:7897"
    runner = SubprocessRunner()
    try:
        code, out = runner.run(
            ["curl", "-s", "--connect-timeout", "5", "-o", "NUL",
             "-w", "%{http_code}", "-x", proxy_url,
             "https://www.baidu.com"],
            timeout=10
        )
        ok = out.strip() == "200"
        ctx.diag_results.append({"layer": "PROXY", "ok": ok,
            "detail": "代理正常" if ok else f"代理返回 HTTP {out.strip()}"})
    except SubprocessFailed as e:
        ctx.diag_results.append({"layer": "PROXY", "ok": False,
            "detail": f"代理断流: {str(e)[:50]}"})
    except SubprocessError as e:
        ctx.diag_results.append({"layer": "PROXY", "ok": False,
            "detail": f"代理端口不可达: {str(e)[:50]}"})
```

关键区别：
- **旧：** 检查端口是否开放（netstat 有 LISTENING = 'ok'）→ 假阳性
- **新：** 通过代理做完整 HTTPS 请求，验证**端到端可达性** → 真阳性

### 关联问题：旧看门狗误报淹没真实信号

事件发生时，看门狗 v8 因为 `-o /dev/null` 的 curl bug（在 git-bash 下返回 exit code 23）持续报告 ❌ TARGET 层失败。过去 30 次诊断记录全部显示：

```
17:43 | ❌ | TARGET   | cmd=curl code=23
17:46 | ❌ | TARGET   | cmd=curl code=23
17:48 | ❌ | TARGET   | cmd=curl code=23
...
```

看门狗认为"TARGET 一直不通"是常态，没把 16:19 的真正的双平台断联当作异常。这暴露了一个**诊断架构缺陷**：看门狗没有将"平台真实连接状态"（gateway_state.json）与"网络层诊断"交叉验证。