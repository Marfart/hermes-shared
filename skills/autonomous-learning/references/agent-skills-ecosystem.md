# Agent Skills 生态研究报告 + 真学验证记录

> 来源: obra/superpowers (224K⭐) + addyosmani/agent-skills (54K⭐) + trailofbits/skills (15K⭐)
> 日期: 2026-06-12

## 一、项目对比

| 维度 | superpowers | agent-skills | trailofbits |
|------|-------------|-------------|-------------|
| ⭐ Stars | 224K | 54K | 15K |
| Skills数量 | 14 | 24 | 74 (41 plugins) |
| 核心哲学 | 流程强制质量 | 工具可用性驱动采纳 | 安全审计零误报 |
| Anti-Rat | 9条集中在writing-plans | 每个skill少量 | **每个skill都有专门表** |
| 流水线 | 刚性7步 | 灵活5层 | **最复杂9步+3层agent** |
| 验证 | verification-before-completion | doubt-driven-review | **fp-check独立双路径** |
| 子agent | subagent-driven-development | 无 | **编排器+工人+裁判** |

## 二、设计模式落地状态

| 设计模式 | 状态 | 落地方式 |
|---------|------|---------|
| HARD-GATE + Anti-Rat | ✅ 已落地 | 8个技能patch+2个新技能 |
| Doubt-Driven Review | ✅ 已落地 | 新技能 doubt-driven-review |
| Context Engineering | ✅ 已落地 | 新技能 context-engineering |
| Model Tiering | ✅ 已落地 | subagent + doubt-driven-review |
| Skill Discovery Pipeline | ✅ 已验证 | 验证代码 skill_system_verification.py |
| FP-Check Engine | ✅ 已验证 | 验证代码 trailofbits_verification.py |
| Sharp Edges Detector | ✅ 已验证 | 验证代码 trailofbits_verification.py |
| Phase-Gated Pipeline | ✅ 已验证 | 验证代码 trailofbits_verification.py |
| Supply Chain Risk | ✅ 已落地 | security-audit 技能 |
| Security Audit Workflow | ✅ 已落地 | security-audit 技能 |
| Skill间引用 | 📋 待落地 | 需要逐步去重 |

## 八、ECC真学验证（2026-06-12）— affaan-m/ECC (Anthropic黑客松冠军)

### 验证代码
- 文件: `memories/脚本缓存/skill_verification/ecc_verification.py`

### 验证结果
- Instinct引擎 ✅ (observe + confidence增长 + 2项目promote为global)
- Context Budget审计 ✅ (530组件, 74 issues, -181.6% context超标)
- AgentShield扫描 ✅ (3 findings: 2 hardcoded passwords + 1 MCP)
- 端到端集成 ✅ (Instinct→Budget→Shield三模式协同)

### 核心Why理解
1. **Instinct > Skill**: skill太重confidence低时硬塞污染全局，instinct是0.3→0.9渐进的，project-scoped隔离，2+项目自动promote
2. **Context Budget审计**: 200K - 20 MCPs = 70K有效空间，必须审计bloat
3. **AgentShield 5面扫描**: secrets/permissions/hooks/mcp/prompts，CVE-2025-59536 CVSS 8.7证明真实攻击面
4. **Cost-Aware路由**: 简单任务用Haiku省3-4x，不是所有任务都要Sonnet
5. **Observation Contract**: tool response必须含status+summary+next_actions+artifacts
6. **Prompt Defense**: "Agentic is just a fancy new way to get a shell"

### 项目规模对比（4项目完整）

| 维度 | superpowers | agent-skills | trailofbits | **ECC** |
|------|------------|-------------|-------------|---------|
| ⭐ Stars | 224K | 54K | 15K | ~82K |
| Skills | 14 | 24 | 74 | **262** |
| Agents | 0 | 0 | 0 | **64** |
| Anti-Rat | 9条集中 | 每个skill少量 | 每个skill专门表 | **6条核心** |
| 安全 | 无 | 无 | Phase-Gate+FP-Check | **AgentShield 5面** |
| 学习 | 无 | 无 | 无 | **Instinct-Based** |
| 成本 | 无 | 无 | 无 | **Cost-Aware路由** |
| 上下文 | HARD-GATE | Context层级 | 无 | **Budget审计** |

### 验证代码归档
- superpowers/agent-skills: `memories/脚本缓存/skill_verification/skill_system_verification.py` (921行, 5测试)
- trailofbits: `memories/脚本缓存/skill_verification/trailofbits_verification.py` (978行, 4测试)
- ECC: `memories/脚本缓存/skill_verification/ecc_verification.py` (234行, 4测试)

### 验证代码
- superpowers/agent-skills: `memories/脚本缓存/skill_verification/skill_system_verification.py`
- trailofbits: `memories/脚本缓存/skill_verification/trailofbits_verification.py`

### 验证结果
- HARD-GATE解析器 ✅ (条件提取+Anti-Rat表)
- HARD-GATE运行时检查器 ✅ (条件不满足=STOP)
- Doubt-Driven Review引擎 ✅ (5步对抗性审查循环)
- Skill Discovery Pipeline ✅ (意图→关键词→阶段→推荐)
- 端到端集成 ✅ (Discovery→GATE→Doubt三模式协同)
- FP-Check Engine ✅ (Standard/Deep双路径验证)
- Sharp Edges Detector ✅ (6类API安全陷阱检测+4/6类别实测)
- Phase-Gated Pipeline ✅ (9阶段有序检查+跳过阻断)

### 核心Why理解
1. **Anti-Rationalization**: LLM在安全审计中最危险的行为是合理化跳过
2. **FP-Check独立流程**: 报告不存在的漏洞比漏报更危险——会浪费团队时间并降低可信度
3. **Phase-Gate强制**: 安全世界跳过=漏报，没有"快速通道"
4. **Sharp Edges/Pit of Success**: 安全用法应该是最简单路径，如果开发者必须理解密码学才能避免漏洞，API就失败了
5. **Variant Analysis**: 找到一个漏洞后必须搜索同类——一个模式漏洞往往意味着更多

## 八、ECC真学验证（2026-06-12）— affaan-m/ECC (Anthropic黑客松冠军)

### 验证代码
- 文件: `memories/脚本缓存/skill_verification/ecc_verification.py`

### 验证结果
- Instinct引擎 ✅ (observe + confidence增长 + 2项目promote为global)
- Context Budget审计 ✅ (530组件, 74 issues, -181.6% context超标)
- AgentShield扫描 ✅ (3 findings: 2 hardcoded passwords + 1 MCP)
- 端到端集成 ✅ (Instinct→Budget→Shield三模式协同)

### 核心Why理解
1. **Instinct > Skill**: skill太重confidence低时硬塞污染全局，instinct是0.3→0.9渐进的
2. **Context Budget审计**: 200K - 20 MCPs = 70K有效空间，必须审计bloat
3. **AgentShield 5面扫描**: CVE-2025-59536 (CVSS 8.7) 证明agent系统有真实攻击面
4. **Cost-Aware路由**: 简单任务用Haiku省3-4x，不是所有任务都要Sonnet
5. **Observation Contract**: tool response必须含status+summary+next_actions+artifacts
6. **Prompt Defense**: "Agentic is just a fancy new way to get a shell"

### 项目规模对比更新

| 维度 | superpowers | agent-skills | trailofbits | **ECC** |
|------|------------|-------------|-------------|---------|
| ⭐ Stars | 224K | 54K | 15K | ~82K |
| Skills | 14 | 24 | 74 | **262** |
| Agents | 0 | 0 | 0 | **64** |
| Anti-Rat | 9条集中 | 每个skill少量 | 每个skill专门表 | **6条核心** |
| 安全 | 无 | 无 | Phase-Gate+FP-Check | **AgentShield 5面** |
| 学习 | 无 | 无 | 无 | **Instinct-Based** |
| 成本 | 无 | 无 | 无 | **Cost-Aware路由** |
| 上下文 | HARD-GATE | Context层级 | 无 | **Budget审计** |