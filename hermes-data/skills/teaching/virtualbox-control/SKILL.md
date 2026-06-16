---
name: virtualbox-control
description: "VirtualBox 虚拟机完全操控手册 — VBoxManage CLI/Python API/Headless/网络/快照/自动化，从GitHub顶级项目提取的实战知识"
version: 1.0.0
author: Tachikoma
trigger: "用户说学VirtualBox/虚拟机/VBoxManage/操控虚拟机/VM自动化"
---

# VirtualBox 完全操控手册 🖥️

> 从 GitHub 6 个项目 + 官方文档提取的实战知识体系

---

## 🏗️ 第1层：VBoxManage CLI — 命令行的完全控制

VBoxManage 是 VirtualBox 的命令行接口，**比 GUI 更强大**。装好 VirtualBox 后，把路径加入 PATH：

```cmd
# Windows
set PATH=%PATH%;"C:\Program Files\Oracle\VirtualBox"

# 验证
VBoxManage --version
```

### 1.1 查信息

```bash
# 列出所有注册的 VM
VBoxManage list vms

# 列出所有正在运行的 VM
VBoxManage list runningvms

# 列出所有操作系统类型（创建VM时用）
VBoxManage list ostypes

# 列出所有桥接网络接口
VBoxManage list bridgedifs

# 列出所有仅主机网络
VBoxManage list hostonlyifs

# 列出所有NAT网络
VBoxManage list natnets

# 列出所有硬盘
VBoxManage list hdds

# 列出所有DVD镜像
VBoxManage list dvds

# 查看特定VM详细信息
VBoxManage showvminfo <VM名称>
```

### 1.2 创建VM（完整流程）

```bash
# 第1步：创建虚拟硬盘（动态分配，32GB）
VBoxManage createhd --filename "MyVM.vdi" --size 32768

# 第2步：创建并注册VM
VBoxManage createvm --name "MyVM" --ostype "Ubuntu_64" --register

# 第3步：添加SATA控制器 + 挂载硬盘
VBoxManage storagectl "MyVM" --name "SATA Controller" --add sata --controller IntelAHCI
VBoxManage storageattach "MyVM" --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium "MyVM.vdi"

# 第4步：添加IDE控制器 + 挂载安装ISO
VBoxManage storagectl "MyVM" --name "IDE Controller" --add ide
VBoxManage storageattach "MyVM" --storagectl "IDE Controller" --port 0 --device 0 --type dvddrive --medium "/path/to/ubuntu.iso"

# 第5步：配置系统参数
VBoxManage modifyvm "MyVM" --memory 4096 --vram 128
VBoxManage modifyvm "MyVM" --cpus 4
VBoxManage modifyvm "MyVM" --ioapic on
VBoxManage modifyvm "MyVM" --boot1 dvd --boot2 disk --boot3 none --boot4 none
VBoxManage modifyvm "MyVM" --graphicscontroller vmsvga
VBoxManage modifyvm "MyVM" --accelerate3d on

# 第6步：配置网络（桥接模式，像独立电脑）
VBoxManage modifyvm "MyVM" --nic1 bridged --bridgeadapter1 "Realtek PCIe GbE"

# 或 NAT 模式（能上网，外面看不见）
VBoxManage modifyvm "MyVM" --nic1 nat

# 或仅主机模式（只有宿主机和VM互通）
VBoxManage modifyvm "MyVM" --nic1 hostonly --hostonlyadapter1 "VirtualBox Host-Only Ethernet Adapter"
```

### 1.3 启动/停止/控制

```bash
# 启动（有GUI窗口）
VBoxManage startvm "MyVM" --type gui

# 启动（无界面 — headless模式，后台运行）
VBoxManage startvm "MyVM" --type headless

# 启动（分离模式 — 启动后不锁控制台）
VBoxManage startvm "MyVM" --type separate

# 暂停
VBoxManage controlvm "MyVM" pause

# 恢复
VBoxManage controlvm "MyVM" resume

# 发送ACPI关机信号（优雅关机）
VBoxManage controlvm "MyVM" acpipowerbutton

# 强制断电
VBoxManage controlvm "MyVM" poweroff

# 保存状态（下次启动恢复原样）
VBoxManage controlvm "MyVM" savestate

# 紧急停止（卡死时用）
VBoxManage startvm "MyVM" --type emergencystop

# 重启
VBoxManage controlvm "MyVM" reset
```

### 1.4 快照系统（核心技能）

```bash
# 拍摄快照
VBoxManage snapshot "MyVM" take "安装完成_纯净状态"

# 拍摄快照（带描述）
VBoxManage snapshot "MyVM" take "安装完成" --description "Ubuntu 22.04 纯净系统，已装好Guest Additions"

# 列出快照
VBoxManage snapshot "MyVM" list

# 恢复快照
VBoxManage snapshot "MyVM" restore "安装完成_纯净状态"

# 删除快照
VBoxManage snapshot "MyVM" delete "某个旧快照"

# 恢复到当前快照的父快照（不指定名字）
VBoxManage snapshot "MyVM" restorecurrent
```

### 1.5 克隆/导出/导入

```bash
# 完整克隆（独立副本，占独立磁盘空间）
VBoxManage clonevm "MyVM" --name "MyVM_Clone" --register

# 链接克隆（节省磁盘，依赖父VM）
VBoxManage clonevm "MyVM" --name "MyVM_Linked" --register --options link

# 导出为 OVA（便携文件，可发给别人直接导入）
VBoxManage export "MyVM" -o "MyVM.ova"

# 导入 OVA
VBoxManage import "MyVM.ova"
```

### 1.6 共享文件夹

```bash
# 添加共享文件夹（宿主机目录 → VM内可见）
VBoxManage sharedfolder add "MyVM" --name "shared" --hostpath "C:\Users\Admin\共享"

# 自动挂载
VBoxManage sharedfolder add "MyVM" --name "shared" --hostpath "C:\Users\Admin\共享" --automount

# 永久挂载（重启仍保留）
VBoxManage sharedfolder add "MyVM" --name "shared" --hostpath "C:\Users\Admin\共享" --automount --persistent

# 删除共享文件夹
VBoxManage sharedfolder remove "MyVM" --name "shared"

# VM内部挂载（Linux guest）
# sudo mount -t vboxsf shared /mnt/shared
# sudo usermod -a -G vboxsf $USER  # 当前用户不用sudo也能挂载
```

---

## 🌐 第2层：网络模式详解

| 模式 | 通信方向 | IP获取 | 外部访问VM | 适用场景 |
|:----|:--------|:-------|:-----------|:---------|
| **NAT** 🏆默认 | VM→外网✅ 外网→VM❌ | DHCP自动 | ❌ | 只需上网，最简单 |
| **桥接** | 像独立电脑 | DHCP/静态 | ✅ 有独立IP | 需要被外部访问 |
| **仅主机** | VM↔宿主机✅ | DHCP自动 | ❌ | 安全隔离测试 |
| **NAT网络** | VM↔外网✅ VM间↔✅ | DHCP自动 | ✅ 端口转发 | 多台VM互联+上网 |
| **内部网络** | VM间↔✅ | 手动设置 | ❌ 连宿主机都不可达 | 最高安全隔离 |

### 端口转发（NAT模式下让外部访问VM）

```bash
# 宿主机:2222 → VM:22 (SSH)
VBoxManage natnetwork modify --netname "NatNetwork" --port-forward-4 "ssh:tcp:[]:2222:[10.0.2.4]:22"

# 或直接modifyvm
VBoxManage modifyvm "MyVM" --natpf1 "ssh,tcp,,2222,,22"
VBoxManage modifyvm "MyVM" --natpf1 "http,tcp,,8080,,80"
```

### 高级网络操作

```bash
# 创建NAT网络（多VM互联）
VBoxManage natnetwork add --netname "MyNatNet" --network "10.0.100.0/24" --enable

# 创建仅主机网络
VBoxManage hostonlyif create
VBoxManage hostonlyif ipconfig "vboxnet0" --ip 192.168.56.1 --netmask 255.255.255.0

# 添加第二个网卡（多网络配置）
VBoxManage modifyvm "MyVM" --nic2 hostonly --hostonlyadapter2 "vboxnet0"
```

### 找VM的IP

```bash
# 方式1：NAT/桥接模式查DHCP租约
VBoxManage list dhcpservers

# 方式2：用guestproperty（需装Guest Additions）
VBoxManage guestproperty get "MyVM" "/VirtualBox/GuestInfo/Net/0/V4/IP"

# 方式3：查看VM信息
VBoxManage showvminfo "MyVM" | grep "NIC\|IP\|MAC"
```

---

## 🐍 第3层：Python 编程操控（来自 `virtualbox-python` ⭐368）

`virtualbox-python` 是 VirtualBox COM API 的 Python 实现（368⭐，Apache-2.0），**可以完全用 Python 控制虚拟机**。

### 安装

```bash
# 第1步：装 VirtualBox SDK（从官网下载）
# 解压后进入 installer/ 目录
python vboxapisetup.py install

# 第2步：装 virtualbox-python
pip install virtualbox
```

### 核心操作

```python
import virtualbox

# 连接VirtualBox
vbox = virtualbox.VirtualBox()

# 列出所有VM
for m in vbox.machines:
    print(f"VM: {m.name} - State: {m.state}")

# 找指定VM
machine = vbox.find_machine("MyVM")

# 启动VM
session = virtualbox.Session()
# 老版API
# progress = machine.launch_vm_process(session, "gui", "")
# 新版API (6.1.2+)
progress = machine.launch_vm_process(session, "headless", [])
progress.wait_for_completion()  # 等待启动完成

# 查询状态
print(f"Session state: {session.state}")
print(f"Machine state: {machine.state}")

# 获取屏幕分辨率
h, w, _, _, _, _ = session.console.display.get_screen_resolution()

# 向VM发送键盘输入
session.console.keyboard.put_keys("Hello, Kali!\n")

# 在VM内执行命令（需Guest Additions+凭据）
guest_session = session.console.guest.create_session("user", "password")
proc, stdout, stderr = guest_session.execute(
    "/bin/bash", ["-c", "ls -la /home"]
)
print(f"Output: {stdout}")

# 注册键盘事件监听器
def on_key(event):
    print(f"Key pressed: {event.scancodes}")
session.console.keyboard.set_on_guest_keyboard(on_key)

# 关闭VM
session.console.power_down()
```

### 自动化测试框架（来自 `m4rm0k/vm-automation` ⭐3）

```bash
# 批量测试软件/脚本在多个VM上
python vm-automation.py binary.exe

# 配置示例
vms_list = ['w10_x64', 'w10_x86', 'w7_x64']
snapshots_list = ['java8', 'java11', 'office2013']
vm_gui = 'headless'
vm_guest_username = 'user'
vm_guest_password = 'P@ssw0rd'
timeout = 60

# 功能：
#   - 多线程并行测试
#   - 快照恢复 → 上传文件 → 执行 → 保存结果
#   - 支持网络开关
#   - 分辨率调整
#   - 前后置脚本
```

### Box.py — 轻量级CLI控制脚本

```python
import os
import argparse

# 从 GitHub Gist 提取的经典控制脚本
# 用法: python box.py --start --box "MyVM"
#       python box.py --status --box "MyVM"

def control_vm(action, box_name):
    if action == 'start':
        os.system(f'VBoxManage startvm "{box_name}" --type headless')
    elif action == 'pause':
        os.system(f'VBoxManage controlvm "{box_name}" pause')
    elif action == 'resume':
        os.system(f'VBoxManage controlvm "{box_name}" resume')
    elif action == 'poweroff':
        os.system(f'VBoxManage controlvm "{box_name}" poweroff')
    elif action == 'status':
        cmd = 'VBoxManage list runningvms'
        running = os.popen(cmd).read()
        if box_name in running:
            print(f"{box_name}: running")
        else:
            print(f"{box_name}: stopped")
```

---

## ⚙️ 第4层：Headless 无人值守模式

### 启动headless VM

```bash
VBoxManage startvm "MyVM" --type headless
```

### 用VBoxHeadless直接启动（轻量级，不依赖VirtualBox Manager）

```bash
VBoxHeadless --startvm "MyVM"
VBoxHeadless --startvm "{VM-UUID}"  # 用UUID
```

### 通过RDP连接headless VM

Headless 模式下没有GUI窗口，但 VirtualBox 内置 VRDP 服务器：

```bash
# 启用VRDP
VBoxManage modifyvm "MyVM" --vrde on

# 设置VRDP端口
VBoxManage modifyvm "MyVM" --vrdeport 3389

# 现在可以用任何RDP客户端连接
# Windows: mstsc /v:localhost:3389
```

### Web面板控制（来自 `nv1t/virtualbox-web-panel`）

```bash
# 装VirtualBox Web控制面板（浏览器管理VM）
git clone https://github.com/nv1t/virtualbox-web-panel
cd virtualbox-web-panel
pip install -r requirements.txt
python webpanel.py

# 浏览器打开 http://localhost:5000
# 功能：启动/停止/暂停/快照/控制台
```

---

## 🐞 第5层：故障排除（从GitHub Gist提取）

### 常见问题解决

| 问题 | 原因 | 解决 |
|:----|:-----|:-----|
| `VBoxManage` not found | 没加PATH | `set PATH=%PATH%;"C:\Program Files\Oracle\VirtualBox"` |
| DVD镜像UUID冲突 | 移动VM后路径变了 | 编辑.vbox文件，删除`<DVDImages>`标签之间的内容 |
| VM卡在poweroff | 进程卡住 | `VBoxManage startvm "VM" --type emergencystop` |
| UEFI Shell不启动 | EFI设置问题 | 关掉 Enable EFI（特殊OS启用）选项 |
| 共享文件夹权限 | 没用vboxsf组 | `sudo usermod -a -G vboxsf $USER` |
| 网卡不存在 | 桥接选错接口 | `VBoxManage list bridgedifs` 看可用的 |
| 虚拟机没有IP | DHCP没分配 | 查 `VBoxManage list dhcpservers` |

### VirtualBox Guest Additions 安装

```bash
# 下载Guest Additions ISO
wget -c http://download.virtualbox.org/virtualbox/7.0/VBoxGuestAdditions_7.0.iso

# 挂载到VM
VBoxManage storageattach "MyVM" --storagectl "IDE Controller" --port 0 \
  --device 0 --type dvddrive --medium "VBoxGuestAdditions_7.0.iso"

# Linux VM内安装
sudo mount /dev/cdrom /mnt
sudo sh /mnt/VBoxLinuxAdditions.run

# 验证
lsmod | grep vbox
```

### Vagrant 集成（VM模板化）

```bash
# 把运行中的VM打成 Vagrant box
vagrant package --base "MyVM" --output ubuntu2204.box

# 然后用 Vagrant 管理
vagrant box add ubuntu2204 ubuntu2204.box
vagrant init ubuntu2204
vagrant up
```

---

## 📚 GitHub 学习资源汇总

| 项目 | ⭐ | 提取的核心价值 |
|:----|:-:|:--------------|
| `sethmlarson/virtualbox-python` | **368⭐** | Python COM API完整封装，代码级控制VM |
| `githubfoam/VirtualBox Cheat Sheet` | 8⭐ | 实战排错大全，含headless/Vagrant/网络 |
| `carmark/VBoxManage examples` | 6⭐ | 纯CLI创建VM的完整流水线 |
| `ashleykleynhans/box.py` | - | 轻量级Python VM控制脚本 |
| `m4rm0k/vm-automation` | 3⭐ | 多VM并行自动化测试框架 |
| `nv1t/virtualbox-web-panel` | - | 浏览器管理VirtualBox的Web面板 |

---

## ⚡ 速查表：最常用的20个VBoxManage命令

```bash
# 查
VBoxManage list vms                    # 所有VM
VBoxManage list runningvms             # 正在跑的
VBoxManage showvminfo "MyVM" | more    # 详细信息

# 建
VBoxManage createvm --name "MyVM" --ostype Ubuntu_64 --register
VBoxManage createhd --filename "MyVM.vdi" --size 40960
VBoxManage storagectl "MyVM" --name SATA --add sata
VBoxManage modifyvm "MyVM" --memory 4096 --cpus 4

# 跑
VBoxManage startvm "MyVM" --type headless   # 后台无界面
VBoxManage startvm "MyVM" --type gui        # 有界面

# 停
VBoxManage controlvm "MyVM" acpipowerbutton  # 优雅关机
VBoxManage controlvm "MyVM" savestate        # 保存状态
VBoxManage controlvm "MyVM" poweroff         # 强制断电

# 快照
VBoxManage snapshot "MyVM" take "momento"
VBoxManage snapshot "MyVM" restore "momento"
VBoxManage snapshot "MyVM" list

# 网络
VBoxManage modifyvm "MyVM" --nic1 bridged --bridgeadapter1 "eth0"
VBoxManage modifyvm "MyVM" --nic1 nat
VBoxManage modifyvm "MyVM" --natpf1 "ssh,tcp,,2222,,22"

# 共享
VBoxManage sharedfolder add "MyVM" --name share --hostpath "C:\Share" --automount
```