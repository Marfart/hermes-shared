# Windows CDP 连接排错指南

## 场景
需要通过CDP连接本机已登录Chrome（如WhatsApp Web）时，端口未开的排查和解决。

## 快速解决（一行命令）
```bash
# 关掉Chrome后，Win+R输入：
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9223
```

## 验证
```bash
netstat -ano | findstr :9223
# 或
curl http://127.0.0.1:9223/json/version
```

## 常见失败模式
| 症状 | 原因 | 解决 |
|------|------|------|
| 浏览器截图黑色 | 页面没加载（代理墙） | 开CDP连本机Chrome |
| Playwright MCP超时 | MCP配置/网络问题 | 用Hermes原生浏览器 |
| `netstat`无9223 | CDP端口没开 | 加启动参数重启Chrome |
| `curl`返回空 | 端口没开或防火墙 | 检查Chrome是否以调试模式启动 |

## 铁律
- WhatsApp操作必须用CDP连本机Chrome，不能用Playwright MCP
- Hermes浏览器工具走Vortex代理，访问WhatsApp会超时
- 不要浪费时间在失败的方案上，直接让用户开CDP端口
