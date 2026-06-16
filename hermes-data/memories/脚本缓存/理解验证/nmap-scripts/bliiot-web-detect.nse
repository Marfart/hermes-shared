local http = require "http"
local nmap = require "nmap"
local stdnse = require "stdnse"

description = [[
检查Web服务器
]]

author = "Tachikoma @ BLIIOT"
license = "Same as Nmap--See https://nmap.org/book/man-legal.html"
categories = {"discovery", "safe"}

portrule = function(host, port)
    -- 匹配5000端口 (我们的靶场)
    if port.number == 5000 then
        return true
    end
    -- 也匹配标准HTTP端口
    if port.protocol == "tcp" and (port.number == 80 or port.number == 8080 or port.number == 443) then
        return true
    end
    return false
end

action = function(host, port)
  local resp = http.get(host, port, "/")
  if not resp then
    return "No response"
  end
  
  local result = {}
  
  if resp.header and resp.header["server"] then
    result["server"] = resp.header["server"]
  end
  
  if resp.body then
    local title = string.match(resp.body, "<[Tt][Ii][Tt][Ll][Ee][^>]*>([^<]*)</[Tt][Ii][Tt][Ll][Ee]>")
    if title then
      result["title"] = title
    end
    
    if resp.body:find("BLIIOT") then
      result["app"] = "BLIIOT Vuln Test Server"
    end
  end
  
  if next(result) then
    return result
  end
  return "Page loaded, no interesting info"
end