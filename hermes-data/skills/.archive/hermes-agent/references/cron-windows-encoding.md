# Windows Cron no_agent 中文乱码修复

When running `no_agent=True` cron jobs on Windows, Chinese + emoji output from
Python scripts arrives as garbled mojibake (e.g. `馃攳璇佷功鍗囩骇`).

## Root Cause

The cron scheduler captures stdout from the child process using
the **system default encoding** (cp936 / GBK on Chinese Windows), regardless
of what encoding the script sets. If the script writes UTF-8 bytes to stdout,
the cron system decodes them as cp936 -> each multi-byte UTF-8 sequence gets
reinterpreted as different characters -> mojibake.

The script-level fix `sys.stdout.reconfigure(encoding='utf-8')` or
`io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` does NOT help because
the cron system reads from the pipe *after* Python's stdout encoding has
already applied -- the bytes in the pipe ARE correct UTF-8, but the cron
delivery layer itself decodes them with cp936.

## Fix: Match the Cron Side's Encoding

```python
import sys, io
# Write GBK-encoded bytes so cp936-decoding by cron produces correct Chinese
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')
```

## Emoji Limitation

GBK (codepage 936) does **not** support emoji characters (U+1Fxxx range,
e.g. white_check_mark, magnifying_glass_tilted_right, wrench, warning_sign).
Attempting to print emoji with GBK encoding raises
`UnicodeEncodeError: 'gbk' codec can't encode character`.

**Fix:** Replace emoji with Chinese text equivalents before printing:

- white_check_mark -> [完成]
- cross_mark -> [失败]
- wrench -> [修复]
- locked -> [安全]
- warning -> [警告]
- bar_chart -> [状态]
- clipboard -> [诊断]
- stopwatch -> [时间]
- counterclockwise -> [重启]
- high_voltage -> [错误]
- magnifying_glass -> [看门狗]
- no_entry -> [跳过]
- collision -> [崩溃]

## Verification

Run this test to confirm the fix works:

```python
import subprocess, sys

r = subprocess.run([sys.executable, '-c', '''
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="gbk")
print("看门狗检查完成")
print("DNS刷新正常")
'''], capture_output=True)

result = r.stdout.decode('cp936', errors='replace')
print(result)  # Should show correct Chinese
```

## Clean ASCII Fallback (Alternative)

If GBK encoding is too restrictive and you need emoji, the only reliable
workaround is to **output pure ASCII** -- replace all Chinese and emoji with
English text equivalents. This avoids encoding issues entirely but loses the
Chinese-language UX.

## Debugging Checklist

- [ ] Script sets `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')`
      before any print() call -- at module level, before any imports that print
- [ ] No emoji in any `print()` or `f-string` output
- [ ] All Chinese characters are within GBK encoding range
- [ ] Test with `subprocess.run(... capture_output=True)` then decode with cp936
