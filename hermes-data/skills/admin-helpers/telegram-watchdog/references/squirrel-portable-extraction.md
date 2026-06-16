# Squirrel Installer 便携化解包法

## 背景

很多 Electron 应用（Obsidian、VS Code、Slack 等）用 **Squirrel.Windows** 打包。它的 .exe 安装器本质上是**内嵌了 7z 压缩包的自解压文件**，可以用 7za 直接解出应用本体。

**不需要等待 GUI 安装器运行完毕。** 直接解包即可获得便携版。

## 步骤

### 1. 下载 7za（只需一次，已存在于 portable launcher 工具包）

```
/c/Users/Admin/Desktop/Working/Obsidian/Obsidian-Portable-main/App/Utils/7za.exe
```

也可从 `https://www.7-zip.org/download.html` 下载独立的 `7za.exe`。

### 2. 列出安装器内容

```bash
7za l -t# "Obsidian-1.12.7.exe"
```

输出示例：
```
Type = #
   Name       Size
  1          216100           ← Squirrel 安装器
  2.7z    104095580           ← ARM64
  3               4
  4.7z    101818304           ← x64 (我们要的)
  5               4
  6.7z     88956126           ← x86
  7          444082
```

- `4.7z` = 64位版本
- `2.7z` = ARM64
- `6.7z` = 32位

### 3. 解出内嵌的 7z

```bash
7za x -t# -aoa "Obsidian-1.12.7.exe" -o"tmp" 4.7z
```

### 4. 再解真正的应用

```bash
7za x -aoa "tmp/4.7z" -o"App/Obsidian"
```

### 5. 验证

```bash
ls App/Obsidian/Obsidian.exe
# 应该看到 ~200MB 的 exe 文件
```

## 原理

Squirrel 用 `#` 格式（自定义 multi-part archive）把多个 .7z 包嵌在一个 .exe 文件尾部。`7za -t#` 直接读取并提取指定编号的压缩包，跳过 Squirrel 的安装逻辑。

## 适用范围

| 应用 | 验证 |
|:----|:----:|
| Obsidian | ✅ 已验证 (v1.12.7) |
| VS Code (Code.exe) | 理论可行，需测试 |
| Slack | 理论可行 |
| 其他 Electron + Squirrel 应用 | 通用方法 |

## 对比传统安装

| 方式 | 优点 | 缺点 |
|:----|:----|:-----|
| GUI 双击安装 | 有开始菜单、文件关联 | 需用户交互、只能装到固定位置 |
| `--silent` 静默安装 | 自动注册 | Squirrel 的 silent 不稳定 |
| **7za 解包（本方法）** | **零交互、可指定目录、即装即用** | 无注册表/开始菜单（便携版特性） |