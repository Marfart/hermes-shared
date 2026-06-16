---
name: pyhydra-brute-force
description: PyHydra — Python暴力破解引擎。支持HTTP FORM/GET登录爆破、SSH端口扫描、多线程字典攻击
---

# 🔥 PyHydra — Python暴力破解引擎

## 文件位置
- 脚本：`%LOCALAPPDATA%\hermes\memories\脚本缓存\网络攻防\pyhydra.py`
- 靶场（用于测试）：`%LOCALAPPDATA%\hermes\memories\脚本缓存\网络攻防\login_target.py`

## 功能
- HTTP POST表单爆破（指定成功/失败关键词）
- HTTP GET参数爆破
- SSH端口开放性扫描
- 多线程并发（默认4线程，可调至200）
- 找到即停模式
- 进度条 + 速率显示
- 内建用户/密码字典（8用户×15密码）
- 自定义字段名（如 user_field=email, pass_field=passwd）

## 用法

### 快速测试（使用内建字典）
```bash
python pyhydra.py http-form://目标地址/ -F "错误" -S "登录成功"
```

### 自定义字典
```bash
python pyhydra.py http-form://目标地址/ -U users.txt -P passwords.txt -F "错误"
```

### 单用户对密码列表
```bash
python pyhydra.py http-form://目标地址/ -u admin -P rockyou.txt -F "Invalid"
```

### 自定义表单字段
```bash
python pyhydra.py http-form://目标地址/ -u admin -P pass.txt -F "出错" --user-field email --pass-field passwd
```

### SSH端口扫描
```bash
python pyhydra.py ssh://192.168.1.1 -U users.txt -P passwords.txt -t 8
```

## 关键参数
| 参数 | 说明 |
|------|------|
| `-u` | 单个用户名 |
| `-U` | 用户名字典文件 |
| `-p` | 单个密码 |
| `-P` | 密码字典文件 |
| `-F` | 失败关键词（逗号分隔） |
| `-S` | 成功关键词（逗号分隔） |
| `-t` | 线程数 |
| `--delay` | 请求间隔秒数 |
| `--no-stop` | 找到后不停止 |
| `--user-field` | 表单用户名字段名 |
| `--pass-field` | 表单密码字段名 |

## 内建字典
用户名：admin, root, kali, manager, user, test, operator, guest
密码：常见弱密码15个（123456, password, admin, P@ssw0rd!, hunter2等）

## 实测性能
- 120组合 → 0.3秒完成，**347次/秒**
- 靶场http://127.0.0.1:5001/ 全破5个凭证

## 延伸用途
- BLIIOT网关密码强度检测（出厂默认密码爆破测试）
- 客户Web管理后台弱口令审计
- 批量设备登录凭证恢复