# ThrottleStop 安全配置指南

## ⚠️ 用户偏好（最高优先级）

**零蓝屏容忍。** 本用户明确要求：任何可能引发蓝屏的设置（包括降压/超频）**不得主动应用**，除非用户明确要求"来点激进的"或"试试超频"。

安全区操作（锁睿频、关BD PROCHOT、调EPP）可以直接做。灰色区（降压、功耗墙）必须等用户开口。

## 简介

ThrottleStop 是 Intel CPU 性能释放工具，通过解除主板固件限制让 CPU 跑满标称睿频。免费、绿色、1.7MB。适用于 10 代及更早的 Intel CPU（以及部分 12 代+）。

**核心原理**：主板厂商为了控制功耗/温度/噪音，给 CPU 设置了多重降频限制。ThrottleStop 可以绕过这些限制。

## 下载安装

### 方式 A：TechPowerUp（原始来源）

1. 访问 `https://www.techpowerup.com/download/techpowerup-throttlestop/`
2. 找到最新版本（当前 9.7.3 Beta 或 9.7 Stable）
3. 点击 Download → 等待自动下载 `ThrottleStop_9.7.zip`
4. 解压到任意目录即可使用

⚠️ TechPowerUp 使用 Cloudflare 保护，curl/requests 直接访问可能被拦截。推荐浏览器直接下载或用 Uptodown 镜像。

⚠️ TPU 的下载按钮是 `<form method="POST"><input type="hidden" name="id"><input type="submit">` 格式，不是直接的 `<a>` 链接。

### 方式 B：Uptodown 镜像（已验证）

浏览器打开 `https://throttlestop.en.uptodown.com/windows/download`，接受 Cookie，点击 Download。

### 方式 C：Playwright MCP 无人值守下载（已验证通过 Uptodown）

```javascript
// 打开下载页
await page.goto('https://throttlestop.en.uptodown.com/windows/download');

// 接受 Cookie（否则按钮被遮挡）
await page.locator('#cookiescript_accept').click();

// 点击下载按钮
await page.locator('#detail-download-button').click();

// 文件保存位置：~/.playwright-mcp/throttlestop-9-7.zip
```

**注意**：Playwright MCP 的下载保存在 `$CWD/.playwright-mcp/` 目录下，不在 Downloads 也不在 Temp。用 `find . -name "*throttle*"` 定位。

## 安全配置（i5-10400 + H510MHP 已验证）

### 主界面

**勾选**：
- [x] Set Multiplier → 43（锁定最高 4.3GHz）
- [x] Speed Shift → EPP 拉到 0（偏向性能）
- [x] **取消 BD PROCHOT** ⬅ 最重要

BD PROCHOT 是 CPU 过热保护信号，但低端主板 VRM 温度误报也会触发它，强制 CPU 降到 800MHz。办公场景取消勾选极安全。

### 降压（FIVR 窗口）

右下角 FIVR → CPU Core / CPU Cache → Offset Voltage **-50 mV** → Save。
温度降 3-5°C。蓝屏就回退到 -30mV。

### 压力测试

FIVR → TS Bench → 960M → Start。温度不超过 85°C 算稳定。

### 开机自启

Options → Start Minimized（也可以直接在启动文件夹加快捷方式）。

## CUA 驱动自动化配置（无人值守）

### 前提
- ThrottleStop.exe 已下载解压到已知目录
- CUA 守护进程已运行
- `ShellExecuteW(None, "runas", exe_path, "", None, 0)` 提权启动（UAC 弹窗需要用户点"是"）

### 关键规则

1. **每次子窗口打开/关闭后必须重新 `get_window_state`** — element_index 会重新编号
2. FIVR 和 Options 子窗口的控件**合并到主窗口的 UIA 树中**，不需要单独 window_id
3. 键盘输入用 `hotkey()` + `press_key()` 组合（`type_text` 工具依赖 window_id）
4. 子窗口操作后要回到主窗口点 Turn On 才能生效

### 配置全流程（已验证）

```bash
# 0. 获取窗口
cua-driver list_windows
# → 找到 PID 和 window_id

# 1. 配置主界面
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":5}'  # 勾选 Set Multiplier
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":16}'  # 点倍频编辑框
cua-driver call --tool press_key --json '{"pid":8156,"window_id":333730,"key":"Delete"}'
cua-driver call --tool press_key --json '{"pid":8156,"window_id":333730,"key":"4"}'
cua-driver call --tool press_key --json '{"pid":8156,"window_id":333730,"key":"3"}'       # 填入 43
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":34}'  # 勾选 Speed Shift EPP
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":35}'  # 点 EPP 编辑框
cua-driver call --tool press_key --json '{"pid":8156,"window_id":333730,"key":"Delete"}'
cua-driver call --tool press_key --json '{"pid":8156,"window_id":333730,"key":"0"}'       # 填入 0
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":8}'   # 取消 BD PROCHOT（toggle）

# 2. FIVR 窗口（降压）
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":20}'  # 点 FIVR
# → get_window_state 刷新 → 找到 FIVR 子窗口控件
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":24}'  # 选 FIVR Control tab
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":30}'  # 勾选 Unlock Adjustable Voltage
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":33}'  # 点 Offset Voltage 编辑框
cua-driver hotkey --json '{"pid":8156,"window_id":333730,"keys":["Ctrl","A"]}'            # 全选
cua-driver press_key --json '{"pid":8156,"window_id":333730,"key":"Delete"}'
cua-driver press_key --json '{"pid":8156,"window_id":333730,"key":"-"}'
cua-driver press_key --json '{"pid":8156,"window_id":333730,"key":"5"}'
cua-driver press_key --json '{"pid":8156,"window_id":333730,"key":"0"}'                   # 填入 -50
# 同样对 CPU Cache 再做一次
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":47}'  # 选 CPU Cache
# → 重复上述 Offset 设置操作
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":52}'  # 选 "Save Voltage Changes" radio
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":55}'  # OK

# 3. Options（开机自启）
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":104}'  # 点 Options
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":13}'   # 勾选 Start Minimized
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":38}'   # 勾选 Notification Area Icon
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":0}'    # OK

# 4. 应用
cua-driver call --tool click --json '{"pid":8156,"window_id":333730,"element_index":105}'  # Turn On

# 5. 自启提权（进入启动文件夹）
# 在启动文件夹创建快捷方式，用二进制修改第 0x15 字节 bit 5 设置 RunAs
# 这样每次登录自动弹出 UAC 提权
```

### 恢复出厂设置（复位所有降压/超频）

```bash
# 打开 FIVR → 分别选 CPU Core 和 CPU Cache
# 点 "Zero Offset" 按钮
# 选 "OK - Do not save voltages" radio
# 点 OK
# 回到主界面点 Save
# 这样其他设置（倍频、EPP、BD PROCHOT）不受影响
```

### 验证 INI 文件

所有持久设置保存在 ThrottleStop.ini（与 exe 同目录）。关键键值：

```
SSTEPP=0           # Speed Shift EPP = 0（性能优先）
OffsetRange=0      # 0 = 无降压偏移
LogoMin=0          # 启动时不显示窗口（配合 Start Minimized）
Options1=0x001001A0  # 编码多个checkbox状态
```

### 开机自启方案

ThrottleStop 需要管理员权限访问 MSR 寄存器，所以：

| 方案 | 说明 | 缺点 |
|:-----|:-----|:-----|
| 启动文件夹快捷方式 + RunAs | 简单 | 每次登录弹出 UAC |
| 计划任务 + RunLevel Highest | 无提示 | 需要管理员权限创建，且 S4U 会话不支持交互 |
| 启动文件夹（不提权） | 无提示 | 部分功能不可用（MSR 写失败） |

推荐用**启动文件夹快捷方式 + RunAs**，用户看到 UAC 点"是"即可。

## 效果预测

| 操作 | 效果 | 安全等级 |
|:-----|:-----|:---------|
| 关 BD PROCHOT | +5-10% | 🟢 |
| 锁睿频 4.3GHz | +10-15% | 🟢 |
| -50mV 降压 | 温度降 3-5°C | 🟢 |
| **综合** | **+15-25%** | **🟢** |

## 危险操作（在这台机器不要做）

| 操作 | 风险 |
|:-----|:-----|
| 拉高 PL1 功耗墙 >65W | 原装散热撑不住 |
| 加核心电压 | 烧 CPU |
| 全程禁用 C-State | 加速老化 |

## 针对不同散热

| 散热 | PL1 上限 | 建议 |
|:-----|:---------|:-----|
| 原装 Intel | ~65W | 不要拉功耗墙 |
| 百元塔式 | ~100W | 可安全拉 85W |
| 双塔/水冷 | ~130W+ | 10 代 i5 用不上 |

## 对比 Intel XTU

ThrottleStop 更好：更小（1.7MB vs 200MB）、绿色免装、有 BD PROCHOT 控制。二选一选 ThrottleStop，不要同时用。
