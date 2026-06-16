# Hermes Shared 🐴

跨机器文件同步仓库（Windows ↔ macOS）

## 目录结构
```
scripts/      # 共享脚本
config/       # 共享配置
watchdog/     # 看门狗相关
polling/      # 轮询相关
docs/         # 文档
```

## 同步规则
- 每5分钟自动 pull/push
- .gitignore 排除密钥和临时文件
- 冲突时手动解决，不自动合并
