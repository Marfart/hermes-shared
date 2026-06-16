# Windows Cron no_agent 中文编码修复

## 问题

Hermes cron 在 `no_agent=True` 模式下，用 `subprocess` 运行 Python 脚本并捕获 stdout。
Windows 默认使用 **cp936 (GBK)** 作为系统编码来解码子进程输出。

如果脚本输出 UTF-8 编码的中文/emoji，cron 用 cp936 解码 → 乱码（mojibake）。

## 根因

```
脚本 stdout (UTF-8 字节) → cron 子进程捕获 → decode(cp936) → 乱码
```

`sys.stdout.reconfigure(encoding='utf-8')` 无济于事——它只改变 Python 的编码器，
但 cron 读取管道时仍用自己的 cp936 解码器。

## 修复方案

### 1. 脚本 stdout 设成 GBK

```python
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')
```

这行必须在任何 `print()` 之前执行（模块级别，不要放在 `if __name__` 里）。

### 2. 替换所有 emoji

GBK（=cp936）**不支持 emoji**。`🔍 ✅ ❌ 🔧 🔐 ⏱️ 📊 📋` 等全部会触发：

```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f50d'
```

替换规则：

| 原始 emoji | 替换文字 |
|-----------|---------|
| 🔍 [看门狗] | |
| ⏱️ [时间] | |
| 📊 [状态] | |
| 📋 [诊断] | |
| ✅ [完成] | |
| ❌ [失败] | |
| 🔧 [修复] | |
| 🔐 [安全] | |
| ⚡ [错误] | |
| 🔄 [重启] | |
| ⛔ [跳过] | |
| 💥 [崩溃] | |
| ⚠️ [警告] | |

### 3. 验证编码完整性

确保脚本中所有中文字符串都能通过 GBK 编码：

```python
with open('script.py', encoding='utf-8') as f:
    content = f.read()

issues = []
for i, line in enumerate(content.split('\n'), 1):
    for m in re.finditer(r'[\u4e00-\u9fff]+', line):
        try:
            m.group().encode('gbk')
        except UnicodeEncodeError as e:
            issues.append((i, m.group(), str(e)))
```

## 验证方法

模拟 cron 的捕获方式：

```python
import subprocess, sys

r = subprocess.run([sys.executable, 'script.py'], capture_output=True)
cron_view = r.stdout.decode('cp936', errors='replace')
print(cron_view)  # 应该无乱码
```

## 已知坑

| 情况 | 结果 |
|------|------|
| 设 utf-8 + 纯英文 | 正常（无可编码对象） |
| 设 utf-8 + 中文 | cron 读到乱码 |
| 设 gbk + emoji | `UnicodeEncodeError` 崩溃 |
| 设 gbk + 中文 | 正常 ✅ |
| 设 gbk + 中文 + emoji 替换文字 | 正常 ✅ |

## 实战验证

Watchdog v8 (smart_watchdog_v8.py) 已用此方案修复：
- cron job_id: `af5f3c06d347`, schedule: `every 2m`, no_agent: True
- 运行状态从 `error`（编码崩溃）→ `ok`（中文正常输出）
- 修复前：`馃攼 璇佷功鍗囩骇 + DNS 鍒锋柊瀹屾垚`
- 修复后：`[安全] 证书升级 + DNS 刷新完成`
