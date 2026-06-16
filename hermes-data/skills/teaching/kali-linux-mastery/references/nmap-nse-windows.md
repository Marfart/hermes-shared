# nmap NSE 脚本编写 — Windows实战记录

> 2026-06-07, 在无Kali VM的情况下Windows原生nmap 7.80 + NSE

## 安装

```bash
winget install nmap
```

装完在 `C:\Program Files (x86)\Nmap\nmap.exe`

## 基础扫描

```bash
# TCP SYN扫描（秘密扫描，不完成握手）
nmap -sS 127.0.0.1
# → 发现 135/445/5000/5357

# TCP Connect扫描
nmap -sT -p 5000 127.0.0.1
# → 5000/tcp open upnp
```

## NSE脚本结构（参考 http-title.nse）

```lua
local http = require "http"
local stdnse = require "stdnse"

description = [[脚本描述]]
author = "你的名字"
license = "Same as Nmap"
categories = {"discovery", "safe"}

portrule = function(host, port)
    -- shortport.http 只认标准HTTP端口(80/8080/443)
    -- 自定义端口必须手写portrule
    if port.number == 5000 then return true end
    return false
end

action = function(host, port)
    local resp = http.get(host, port, "/")
    if not resp then return nil end
    local result = {}
    if resp.header and resp.header["server"] then
        result["server"] = resp.header["server"]
    end
    if resp.body then
        local title = string.match(resp.body, "<[Tt][Ii][Tt][Ll][Ee][^>]*>([^<]*)</[Tt][Ii][Tt][Ll][Ee]>")
        if title then result["title"] = title end
    end
    if next(result) then return result end
    return nil
end
```

## 运行自定义NSE脚本

```bash
# 用绝对路径指定脚本（无需admin权限）
nmap -p 5000 --script "C:/path/to/script.nse" 127.0.0.1 -v

# --script-updatedb 需要Program Files写入权限
# 替代方案：脚本放随便什么目录，用绝对路径加载
```

## 踩坑记录

1. shortport.http 不认自定义端口 — 只匹配80/8080/443等标准HTTP口
2. --script-updatedb 权限不够 — Program Files目录默认不可写
3. 版本扫描 -sV 在Windows上可能超时 -sS 和 -sT 都秒出