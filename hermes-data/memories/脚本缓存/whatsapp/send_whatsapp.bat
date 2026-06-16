@echo off
title 🐾 Tachikoma WhatsApp Auto Sender
cd /d "C:\Users\Admin\AppData\Local\hermes\memories\脚本缓存\whatsapp"

echo ╔══════════════════════════════════════════╗
echo ║   🐾 塔奇克马 WhatsApp 自动发信工具  ║
echo ║   BLIIoT 客户开发信自动化                  ║
echo ╚══════════════════════════════════════════╝
echo.

:menu
echo 请选择操作:
echo.
echo  [1] 📋 预览全部 30 封开发信（不发送）
echo  [2] 🚀 全部自动发送（30 条）
echo  [3] 🎯 只发送 TOP 5 客户
echo  [4] 🔍 按类别发送
echo  [5] 🏗️  安装依赖（首次使用）
echo  [0] ❌ 退出
echo.

set /p choice="输入数字: "

if "%choice%"=="1" (
    python whatsapp_auto_sender.py --dry-run
    goto end
)
if "%choice%"=="2" (
    python whatsapp_auto_sender.py
    goto end
)
if "%choice%"=="3" (
    python whatsapp_auto_sender.py --start 1 --end 5
    goto end
)
if "%choice%"=="4" (
    echo.
    echo 可选类别:
    echo  - System Integrator
    echo  - Automation Company
    echo  - Industrial Automation
    echo  - Machine Builder
    echo  - Building Automation
    echo  - Electrical Engineering
    echo  - Industrial Distribution
    echo  - Process Automation
    echo  - Control Systems
    echo  - Engineering Solutions
    echo  - Software/Automation
    echo  - SmartGrid/IoT
    echo  - Telecom/SmartGrid
    echo.
    set /p cat="输入类别关键词: "
    python whatsapp_auto_sender.py --category "%cat%" --dry-run
    echo.
    set /p confirm="确认发送？(y/n): "
    if "!confirm!"=="y" (
        python whatsapp_auto_sender.py --category "%cat%"
    )
    goto end
)
if "%choice%"=="5" (
    echo 安装 Selenium...
    pip install selenium webdriver-manager
    echo.
    echo ✅ 依赖安装完成！
    goto menu
)
if "%choice%"=="0" exit /b

:end
echo.
pause
goto menu