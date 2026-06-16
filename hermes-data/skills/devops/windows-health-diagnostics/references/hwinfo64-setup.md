# HWiNFO64 安装与使用

## 下载（绕过 Cloudflare）

HWiNFO 官网 https://www.hwinfo.com/download/ 有 Cloudflare 防护，curl/browser 工具无法直接下载。

**可用镜像**：
- SAC (Slovak Antivirus Center): `https://www.sac.sk/download/utildiag/hwi_848.zip` — 无 Cloudflare
- 便携版 zip 内含 HWiNFO32.exe + HWiNFO64.exe + HWiNFO_ARM64.exe

**Playwright 绕过法**：Playwright MCP 使用本机 Chrome（真实浏览器指纹），可通过 Cloudflare 正常访问并点击下载链接。下载后从浏览器临时目录复制文件到目标位置。

## 权限

HWiNFO64 必须管理员权限运行（Error 740）。因为需要加载内核驱动访问：
- CPU 温度/频率/电压传感器
- GPU 温度/风扇转速
- 主板传感器（南桥/VRM温度）
- 风扇转速

## 命令行

Pro 版才有完整命令行支持。免费版支持：
- `/S` — 直接打开 Sensors-only 视图
- 启动时弹出选择：Sensors-only / Summary-only

## 位置

本机安装：`C:\Users\Admin\Desktop\Working\HWiNFO64\`
桌面快捷方式：`桌面\HWiNFO64.lnk`
