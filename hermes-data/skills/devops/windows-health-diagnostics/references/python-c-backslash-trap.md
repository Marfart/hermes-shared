# MSYS 下 `python -c` 内联代码反斜杠吞字陷阱

## 症状

在 git-bash/MSYS 终端写 `python -c "..."` 时，反斜杠（`\`）和花括号（`{}`）被 MSYS 提前吞掉或解释：

```bash
# 你写的
python -c "import shutil; t,u,f=shutil.disk_usage('C:\\')"
# → SyntaxError: unterminated string literal

# 花括号+f-string
python -c "print(f'剩余: {f/g:.0f}G')"
# → SyntaxError: invalid decimal literal
```

## 根因

MSYS 的 POSIX 兼容层在处理命令行参数时，会：
1. 将 `\\` 解释为 MSYS 转义 → 传给 Python 的只剩 `\` → Python 语法错误
2. 将 `{...}` 尝试进行花括号扩展 → 与 f-string 冲突
3. 将 `C:\...` 当作类 UNIX 路径处理 → 路径被截断

## 四种解决方案

### 方案 A（推荐）：写成文件再执行

```bash
# 不要 inline
python script.py
```

### 方案 B：单引号 + 双反斜杠 + 不用 f-string

```bash
python -c "import shutil; t,u,f=shutil.disk_usage('C:\\\\'); g=1024**3; print(str(t/g) + 'G')"
# \\\\ 在 bash 里→ \\ 传给 python→ 字面反斜杠
```

### 方案 C：用 pathlib 避免反斜杠

```bash
python -c "from pathlib import Path; print(Path('C:/').drive)"
```

### 方案 D：临时脚本 + execute_code

在 Python `execute_code` 工具里写 `write_file` + `terminal`，绕过整个 MSYS 参数解析层。

## 黄金法则

> **任何包含反斜杠或 f-string 的内联 Python 命令，都写成 .py 文件再执行。不要省这一行。**