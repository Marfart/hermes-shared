# 方向纠正（2026-10-21）
Kali 明确说明“开发客户”指客户开发/获客，不是开发机器。此前 Node-RED 研究属于我的范围误解，不作为本任务成果；后续只研究B2B线索发现、官网画像、名单治理、CRM和合规销售自动化。

# 启动进度｜BLIIOT GitHub 项目夜间深度学习

- 启动：2026-10-20 23:57:04（北京时间，UTC+8）
- 本次进度截点：2026-10-21 00:05（北京时间）
- 项目：`node-red/node-red`，GitHub 公共仓库，Apache-2.0；GitHub API 当前读取到最近 push 为 2026-10-20 10:16:57Z，非归档。仓库 `package.json` 版本 5.0.8。
- 环境：Node v26.7.0、npm 11.19.0；在独立克隆目录执行 `npm ci --ignore-scripts --no-audit --no-fund`，876 个依赖安装成功，未运行包安装脚本。
- 源码阅读：
  1. `packages/node_modules/@node-red/runtime/lib/flows/Flow.js`：Flow 负责节点创建、启动、停止；每个 flow 绑定自己的 context，并按层级解析环境变量。
  2. `packages/node_modules/@node-red/runtime/lib/flows/index.js`：装载/部署状态机，先解析配置、计算 diff，再协调存储、凭证和运行时；支持不同范围的 deploy。
  3. `packages/node_modules/@node-red/runtime/lib/flows/util.js`：节点变更识别、配置解析、env/JSONata/credential 值解析；diff 将节点属性变化与连线变化分开，并追踪受影响的相邻节点。
  4. `packages/node_modules/@node-red/runtime/lib/storage/localfilesystem/index.js`：本地存储插件负责 userDir 初始化，并将 flows、credentials、settings、sessions、projects 等职责委托给子模块。
  5. 测试：`test/unit/@node-red/runtime/lib/flows/Flow_spec.js`、`util_spec.js`，检查启停、上下文、配置解析与变更 diff。
- WHY：编辑器坐标变化不应重启运行时节点；功能属性变化需重新部署；连线变化由单独的 rewired diff 处理，避免误将画布移动当作设备逻辑变更。这是从实现和测试观察到的设计意图。
- 实验：在独立目录编写 `node_red_diff_probe.js`，直接调用上游 `diffNodes`。3 项通过：仅移动节点坐标→不算运行时变化；仅 wires 改变→由上层拓扑 diff 处理，不作为普通节点属性变化；Modbus `unitId` 改变→识别为需重新部署的属性变化。
- 测试：执行 `npx mocha test/unit/_spec.js test/unit/@node-red/runtime/lib/flows/util_spec.js test/unit/@node-red/runtime/lib/flows/Flow_spec.js`，92 passing（2 秒）。克隆目录 `git status` 干净，没有修改上游源码。
- 对 BLIIOT 的关联（推断，尚未在 BL118 实机验证）：Node-RED 已用于 BL118，可将协议采集、数据变换、MQTT/HTTP 上报、告警编排成可演示工作流。客户需求访谈可先问：现场协议/寄存器、数据频率、断网缓存、目标平台、告警规则和远程控制权限。
- 未验证：BL118 当前固件内置 Node-RED 版本、可用节点包、真实 Modbus 设备通信与发布流程。没有部署到公司设备、CRM 或客户环境。
- 后续：继续研究 ThingsBoard/EdgeX/ChirpStack 等产品开发项目，以及 n8n/Twenty CRM 等客户流程项目；每轮以具体源码和可运行实验为准。
- 客户开发方向的实际研究：2026-10-21 约11:40–11:44，EspoCRM 入站获客流程；报告 `hourly_01.md`，静态验证 8/8；PHP 项目测试因缺少 PHP 未运行。
- 自动小时报告状态：原计划任务 `cc55482d3664` 已因模型 endpoint 404 用尽 8 次并结束；客户开发修正后的任务 `8ab175e22cad` 第一次手动触发也因 `No endpoints found for owl-alpha` 失败，已暂停避免空跑。没有自动小时报告正在运行；未改 Hermes 模型配置。
