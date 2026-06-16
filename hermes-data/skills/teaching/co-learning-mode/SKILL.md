---
name: co-learning-mode
description: "小马陪学模式 — 每次和Kali一起学习时，自动记笔记到 Obsidian Vault，课后可翻阅回顾"
version: 2.1.0
author: Tachikoma
platforms: [windows]
---

# 小马陪学模式 🐾📖

## 前置条件：Obsidian 安装

Obsidian 以**便携版**安装在 Working 目录下（不是传统 MSI 安装）：

| 项目 | 路径 |
|:----|:-----|
| 启动文件 | `C:\\Users\\Admin\\Desktop\\Working\\Obsidian\\App\\Obsidian\\Obsidian.exe` |
| Vault 位置 | `C:\\Users\\Admin\\Documents\\Obsidian Vault\\` |
| 笔记脚本 | `C:\\Users\\Admin\\AppData\\Local\\hermes\\scripts\\learn_noter.py` |

**首次使用（只需一次）：**
1. 双击 `Working/Obsidian/App/Obsidian/Obsidian.exe` 启动
2. 选 **"打开本地仓库作为保管库"（Open folder as vault）**
3. 选 `C:\\Users\\Admin\\Documents\\Obsidian Vault\\`
4. 笔记立刻出现！

**注意：** 因为不是 MSI 安装，第一次必须手动关联 Vault。之后每次启动自动加载。

## 核心铁则

**🚨 当学习内容为软件项目/工具时，安装先行，笔记为后。**

## 🔥 三合一产品规格书精读法（Kali 2026-06-08确立，v2）

当学习BLIIOT产品规格书（datasheet）时，采用**三合一精读模式**：英语 + 技术 + 黑客。

### 模式规则

**1. 原文优先，一句一句来 — Kali说：要把原文内容一句一句拿出来**
- ❌ **绝对不要**自己总结/提炼/概述产品特性
- ❌ 不要先给一个「概览」再讲原文 — 直接从原文第一句开始
- ✅ 从DOCX原始文件逐句提取英文原文，完整保留每个句子
- ✅ 先贴原文句子 → 再逐词/逐短语讲解（英语词汇 + 技术原理）
- ✅ Kali说「你不懂我就会问，你就讲解」— 自己先完整讲一遍，等她问
- ✅ 她说「停」立即停，不要继续往下讲
- ⚠️ **每次只贴一个段落/一个应用场景** — 不要一次性把整节所有场景（如P30-P38共9个场景）全部摆出来。贴一个场景的原文→讲完→等她问或说继续→再贴下一个。
- ✅ 她问「可以用来做什么」→ 回到原文找应用场景段落，**逐个场景贴原文**，不要先给个总结再展开
- ✅ 她说继续或追问某个词 → 深入展开后再回到原文下一句
- ✅ 应用场景部分也要逐句讲（她问「可以用来做什么」时回归原文P30-P38）
- ⚠️ 黑客视角不是最后加一段总结，而是在每个技术点讲解时就嵌入

**2. 全技术细节拆解**
每个知识点必须讲清楚：
- **硬件**：芯片、接口、引脚、电气特性（电压/电流/隔离）
- **软件**：协议栈、OS、Web Server、固件架构
- **协议转换**：数据如何从A到B（如 Modbus RTU → MQTT）
- **架构位置**：这东西在实际系统里放哪里、干什么用

**3. 黑客视角永远融入**（不是最后加一段总结——是在每个技术点讲解时就嵌入）
- 讲**MQTT协议** → 同时讲1883明文/匿名订阅/可预测topic枚举/publish伪造
- 讲**Web Server** → 同时讲弱口令/CSRF/XSS/默认配置攻击
- 讲**RS485/Modbus RTU** → 同时讲总线监听/中间人/协议无认证
- 讲**远程维护(BLRAT)** → 同时讲后门隧道/穿透防火墙/隐蔽C2通道
- 讲**云平台对接(AWS/Ali/Huawei)** → 同时讲云API凭证泄露/未授权访问
- 讲**Linux OS(嵌入式)** → 同时讲固件提取/binwalk/反向shell可能性
- 讲**OPC UA(Pro版)** → 同时讲X.509证书认证/UA Binary协议解析漏洞
- 讲**硬件接口** → 同时讲物理访问/调试串口/JTAG/SWD接口利用

**4. 用户驱动节奏**
- Kali不问就不额外发散
- 她说「停」立即停，等新指令
- 她说某个词不懂 → 深入讲这个词及其技术背景
- 她问「可以用来做什么」→ 回原文的应用场景段落逐句讲

### 与陪学模式的关系

三合一精读法是co-learning-mode在**BLIIOT产品规格书学习**场景下的特化方法：
- 不需要立刻建Obsidian笔记（Kali说学的时候专注学，不打断节奏）
- 课后如果需要，再建笔记归档
- 黑客视角的两条铁律依然生效：
  1. BLIIOT业务知识绝不等同于黑客攻击目标
  2. 讲黑客视角是**为了理解技术边界和风险**，不是教犯罪

Kali's exact words: *"这些都是项目，而不是说你把它记成几个文字就完事了"*

这意味着：
- 从 GitHub 学到的项目 → **先 clone/download → install → create shortcuts → verify 能用**
- 笔记只是在安装完成后做的一份**摘要/索引**，不是交付物本身
- 交付物是一个**可运行的安装** + 桌面快捷方式/入口

## 工作流程

当 Kali 说「我们一起学XXX」或「教我XXX」时：

### Phase 0 — Research & Curate（先研究，再教学）
在创建笔记或开始讲授前，先做一轮外部调研：
1. **Web Search** — 用 `web_search` 搜索该主题的最新信息（结构、题型、资源）
2. **GitHub Search** — 用 `web_search` + `browser_navigate` 在 GitHub 上挖掘开源项目/工具
3. **Curate & Rank** — 对搜索结果做精选排名（按相关性、Stars、实用度）
4. **判断类型**：调研出的资源分两类处理
   - **Software/Tools**（桌面App、CLI工具、浏览器扩展、PDF资料集）→ 走 Phase 2
   - **Guides/Docs**（教程、方法论、知识内容）→ 走 Phase 1

### Phase 1 — Build & Teach（纯知识类）
1. **自动建笔记** → 在 Obsidian Vault 创建学习笔记（含调研成果）
2. **边教边记** → 每讲完一个知识点，追加到笔记
3. **课后索引** → 自动更新关联链接和目录

### Phase 2 — Install & Deploy（软件/工具/资料类）🚨 关键
**只有研究没安装=白做。先装后记。**

1. **Download** — 用 `git clone --depth 1` 或 `curl` 下 ZIP 包
   - 优先 shallow clone（快），ZIP 包也可
   - 超时则用 `curl -sL --connect-timeout 30 --max-time 180` 下 release ZIP
   - 下载到 `Desktop/Working/英语学习工具/` 或同类主题目录
2. **Install / Extract** — 解压到目标目录
3. **Create Shortcuts** — 对于在线工具/网站，创建 `.url` 桌面快捷方式
   - 快捷方式放到 `Desktop/英语学习工具包/` 或同类易找位置
   - 带 emoji 前缀命名（如 `📚 Qwerty Learner.url`）
4. **Copy Assets** — 对 PDF/文档类资源，直接拷贝到桌面目录供双击打开
5. **Create README** — 写一个 `README.md` 做快速索引说明
6. **Verify** — 确认下载的文件可打开/解压正确
7. **最后才写笔记** — 在 Obsidian 中为本次学习做一份**摘要笔记**，记录：
   - 安装了哪些项目
   - 各项目位置（路径）
   - 快捷方式位置
   - 使用方法简介

### Phase 2 — Pitfalls（安装陷阱）
- **Git clone 超时** → 先 `kill` 残留 git 进程（`taskkill //F //IM git.exe`），删空目录，改走 `curl -sL --connect-timeout 30 --max-time 180` 下 ZIP
- **ZIP 下载后占用** → 某些 git 进程会锁住 `.git/pack/` 文件，`rm -rf` 前先 `taskkill`
- **Chrome 扩展安装** → 需要登录 Chrome 账号才能装。无账号时只能下载源码，没法通过浏览器工具直接 side-load
- **Download 目录** → 统一放 `Desktop/Working/学习主题/`，不要到处放；桌面入口放 `Desktop/学习工具包/`

## 笔记自动生成规则

### 笔记目录结构

```
Obsidian Vault/
├── 学习笔记首页.md              ← 总索引（自动更新）
├── 01-学习笔记/
│   ├── Python脚本/              ← Python 相关
│   ├── Hermes技能/              ← Hermes 相关
│   ├── BLIIOT业务/              ← 工作相关
│   ├── 英语IELTS/               ← 英语学习
│   └── 投资理财/                ← 财经学习
├── 02-小马日志/                 ← 小马每日总结
└── 03-参考资料/                 ← 外部链接/引用
```

### 笔记模板

每篇笔记自动包含：

```markdown
# 笔记标题

> 📅 2026-06-02 | #标签1 #标签2

---

## 📌 知识点

（小马详细讲解的内容）

## 💻 代码示例（如果有）

```python
print("Hello World")
```

## 📝 Kali的备注

（预留空间，Kali可以手写补充）

## 🔗 关联笔记

[[相关笔记1]]、[[相关笔记2]]

---

> 🐾 小马自动记录 | [[学习笔记首页]]
```

## 技能调用方式

当 Kali 说以下内容时自动激活：
- 「一起学XX」
- 「教我XX」
- 「XX怎么用」
- 「今天学XX」
- 任何带「学」字的知识传授请求

### 每次响应中，小马应该：

1. **第一次响应**时：用 `learn_noter.py` 创建笔记
2. **教学中**：每讲完一个子主题，用 `learn_noter.py append` 追加内容
3. **结束后**：更新 [[学习笔记首页]] 的最近笔记列表

### 坑：大量笔记内容用 terminal 传 heredoc 会失败
- ❌ 不要 `cat > /tmp/script.py << 'PYEOF'` 然后用 `python /tmp/script.py` 方式运行
- 当 append 的内容很大（超过几KB）时，foreground terminal 会报 "& backgrounding" 错误
- ✅ 正确做法：
  1. 先 `write_file` 把 Python 脚本写到磁盘（含所有 learn_noter.py append 调用）
  2. 再 `terminal` 执行这个脚本文件

### 脚本位置

```
python "C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py" create <分类> <标题> <内容>
python "C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py" append <分类> <标题> <新内容>
python "C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py" list [分类]
```

### 快捷别名（手动使用时）

```bash
# 记录一个知识点
python "C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py" create "Python脚本" "变量类型" "笔记内容..."

# 追加更多内容到已有笔记
python "C:\Users\Admin\AppData\Local\hermes\scripts\learn_noter.py" append "Python脚本" "变量类型" "今天学了字典..."
```

### 分类对应表

| Kali说的主题 | 分类目录 |
|:------------|:---------|
| Python / 脚本 / 代码 | Python脚本 |
| Hermes / 技能 / 工具 | Hermes技能 |
| BLIIOT / 报价 / 客户 / WhatsApp | BLIIOT业务 |
| 英语 / IELTS | 英语IELTS |
| 投资 / 理财 / 财经 | 投资理财 |
| 其他 | Hermes技能（兜底） |

### 陪学风格（Kali偏好 2026-06-11确立）

- 风格三合一：**卡哇伊 + 专业 + 带学**
  - 卡哇伊 🧸✨ — 用emoji、颜文字、可爱的比喻（MQTT=发朋友圈, OPC UA=顺丰快递）
  - 专业 — 每个知识点讲清楚原理、谁在用、为什么用
  - 带学 — 用**类比**让复杂概念变简单
- 内容要详细，不能敷衍
- 每个知识点要有**为什么这么用**的解释
- 代码示例必须**完整可运行**
- 最后要问「这部分记好了，继续学下一部分吗？」

### 产品线教学风格（BLIIOT product knowledge专用）

当教BLIIOT产品知识（如IOy/ARMxy/网关系列）时, 采用此格式：

1. **先给一句话核心** — 这东西到底是干嘛的，用最简单的话说
2. **拆解工作流程** — 数据从哪来→经过什么处理→到哪去
3. **六兄弟/多型号格式** — 每个型号用独立色块+emoji区分：🟢🔵🟣🟠🔴🟡
4. **每型号必讲**：
   - **语言**（说的什么协议）
   - **对接**（说给谁听）
   - **客户**（谁会买这个）
   - **场景**（实际部署例子）
   - **卖点**（为什么选它不选别的）
   - **小马点评**（一句比喻总结，如「Modbus TCP就像可口可乐🥤——不是最好喝的，但全世界哪都有」）
5. **类比驱动** — 每个协议/技术用生活比喻：MQTT=发朋友圈, OPC UA=顺丰快递带加密, SNMP=IT小哥遥控器, IEC 104=电网身份证, BACnet/IP=大楼管家
6. **最后上选型口诀** — 方便记忆的顺口溜（如「普通工厂找🟢BL190, 信息安全要🔵BL191...」）
7. **硬件统一讲** — 多个型号共享同一硬件的，先讲共同的再讲差异
8. **尽量引用datasheet原文** — 不是自己编，是真的从文档里读出来的

## Vault 路径

```
C:\Users\Admin\Documents\Obsidian Vault\
```

## 与 LLM Wiki 的集成

Wiki 知识库通过 Junction 挂载到 Obsidian Vault 的 `04-Wiki/` 目录：

```
Obsidian Vault/
├── 04-Wiki/  ← mklink /J 指向 Working/wiki/
│   ├── SCHEMA.md
│   ├── index.md
│   ├── log.md
│   ├── concepts/
│   ├── entities/
│   └── raw/
```

- Wiki 的内容是结构化的知识沉淀，学习笔记是教程式随堂记录
- 成熟的学习笔记可以归档提炼到 Wiki 的 `concepts/` 或 `entities/` 下
- 两个系统通过 `[[wikilinks]]` 互相引用

**不要在 learning-mode 中编辑 Wiki 页面**（Wiki 属于 llm-wiki skill 的管辖范围），但可以在学习笔记中引用 Wiki 页面。

## 关联参考文件

| 文件 | 用途 |
|:---|:-----|
| `references/digital-file-search.md` | 电子书/数字文件搜索方法论 — 多源链式搜索 + Kali格式偏好 |

## Obsidian 安装须知（非 MSI 便携版）

Obsidian 以**便携版**从 Squirrel 安装器解包部署（不是传统 MSI 安装）：

| 项目 | 路径 |
|:----|:-----|
| 启动文件 | `Working/Obsidian/App/Obsidian/Obsidian.exe` |
| 部署方式 | 7za -t# 从 Squirrel exe 提取 4.7z → 解压 |
| 首次使用 | 必须手动打开 Vault 目录关联 |

**首次使用步骤：**
1. 双击 `Working/Obsidian/App/Obsidian/Obsidian.exe`
2. 选 "打开本地仓库作为保管库" → 定位到 `C:\Users\Admin\Documents\Obsidian Vault\`
3. 笔记和 Wiki 直接出现

**更新版本：** 重新下载新版的 `.exe`，用 `7za` 解包覆盖 `App/Obsidian/` 即可。