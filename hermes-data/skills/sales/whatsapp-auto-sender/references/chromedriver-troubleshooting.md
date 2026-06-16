# ChromeDriver 启动故障排查指南 (Windows)

## 错误模式索引

| 错误信息 | 根因 | 解决 |
|---------|------|------|
| `DevToolsActivePort file doesn't exist` | Chrome 实例冲突 (已有旧 Chrome 进程) 或启动参数错误 | 先 `taskkill /F /IM chrome.exe` 再启动 |
| `cannot connect to chrome at 127.0.0.1:9222` | Chrome 没有用 `--remote-debugging-port` 启动 | 启动参数必须含 `--remote-debugging-port=9222` |
| `SessionNotCreatedException` | Chromedriver 版本 vs Chrome 版本不匹配 | 用 Selenium Manager 自动管理驱动 |

## 真实环境探测命令

```powershell
# 检查 Chrome 是否有残留进程
tasklist //FI "IMAGENAME eq chrome.exe"

# 检查调试端口是否监听
netstat -ano | grep 9222

# 检查 Chromedriver 版本
/c/Users/Admin/.cache/selenium/chromedriver/win64/*/chromedriver.exe --version

# 检查 Chrome 版本
"C:/Program Files/Google/Chrome/Application/chrome.exe" --version

# 检查本地 Selenium 版本
pip show selenium
```

## 本机 Chromedriver 缓存路径

```
/c/Users/Admin/.cache/selenium/chromedriver/win64/148.0.7778.178/chromedriver.exe
```

Selenium 4.44.0 自带 Selenium Manager，自动管理驱动。如果版本不匹配，删掉缓存目录让其重新下载:

```bash
rm -rf /c/Users/Admin/.cache/selenium/chromedriver
```

## 两种启动策略对比

### 策略 A: Selenium 自动启动 Chrome（默认）
```python
driver = webdriver.Chrome(options=opts)  # Selenium 自动找 chromedriver + 启动 Chrome
```
**问题**: Windows 上旧 Chrome 进程冲突时，DevToolsActivePort 无法创建

### 策略 B: CDP 连接到已有 Chrome（推荐）
```python
# 1. 手动（或 subprocess.Popen）启动 Chrome + 调试端口
# 2. 用 debuggerAddress 连接现有实例
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=opts)
```
**优点**: 避免端口冲突、可先扫 QR 再连接、稳定

## 快速诊断脚本（Python）

```python
import subprocess, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def diagnose_chrome():
    """诊断 Chrome + Chromedriver 状态"""
    import os
    
    # 1. 检查 chromedriver
    cd_path = None
    for root, dirs, files in os.walk(r"C:\Users\Admin\.cache\selenium\chromedriver"):
        for f in files:
            if f == "chromedriver.exe":
                cd_path = os.path.join(root, f)
    print(f"chromedriver: {cd_path or 'NOT FOUND'}")
    
    # 2. 检查 Chrome 进程数
    result = subprocess.run("tasklist //FI \"IMAGENAME eq chrome.exe\"", 
                          shell=True, capture_output=True, text=True)
    chrome_count = result.stdout.count("chrome.exe")
    print(f"Chrome processes: {chrome_count}")
    
    # 3. 检查 9222 端口
    result = subprocess.run("netstat -ano | grep 9222", 
                          shell=True, capture_output=True, text=True)
    print(f"Port 9222: {'LISTENING' if result.stdout.strip() else 'NOT OPEN'}")
    
    # 4. 推荐操作
    if chrome_count > 3:
        print("ACTION: Kill old Chrome → restart with --remote-debugging-port=9222")
    elif not result.stdout.strip():
        print("ACTION: Restart Chrome with debugging port")
    else:
        print("READY: Connect via debuggerAddress")