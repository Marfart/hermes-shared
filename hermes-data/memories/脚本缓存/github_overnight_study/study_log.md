# BLIIOT GitHub 夜间项目深度学习｜进度日志

## 方向纠正（2026-10-21）
Kali 说明“开发客户”指获客/客户开发，不是开发设备。此前 Node-RED 运行时研究是我误解范围，明确排除出客户开发成果；从现在起只研究 B2B 线索、公司画像、CRM、销售自动化和合规邮件流程。

## 启动进度（2026-10-20 23:57—2026-10-21 00:05，北京时间）

- **研究项目：** `node-red/node-red`。GitHub 元数据：Apache-2.0、未归档、最近 push `2026-10-20T10:16:57Z`；仓库 `package.json` 版本 5.0.8。
- **初筛方向：** 工业 IoT 平台（ThingsBoard、DGIOT、OpenRemote 等）与 Python CRM；星数仅用于发现候选，不作为质量判断。随后会核对源码、许可、维护与适配性。
- **独立环境：** Node v26.7.0 / npm 11.19.0；在桌面独立克隆 `Desktop/Working/GitHub_Overnight_Study/node-red`。执行 `npm ci --ignore-scripts --no-audit --no-fund`，876 个依赖安装完成；忽略安装脚本，未安装系统服务。
- **源码阅读：** `Flow.js`（节点生命周期与 flow context）、`flows/index.js`（load/deploy 状态机及 diff 协调）、`flows/util.js`（配置解析、节点/拓扑变更分类、环境变量解析）、`storage/localfilesystem/index.js`（存储插件及模块委托）；并读了 `Flow_spec.js` 与 `util_spec.js`。
- **设计结论：** 编辑器坐标不是运行时配置，不应导致节点重启；功能属性变更才重部署；线缆拓扑变更单独分类，再计算受影响节点。这能减少部署扰动。依据是 `diffNodes` 的过滤规则与 `diffConfigs` 的独立 rewired 处理逻辑，属于源码观察结论。
- **原创验证：** `C:/Users/Admin/AppData/Local/hermes/memories/脚本缓存/github_overnight_study/node_red_diff_probe.js` 直接调用上游实现；3/3 通过（坐标变化 false、wires 变化 false、Modbus unitId 变化 true）。
- **测试结果：** `npx mocha test/unit/_spec.js test/unit/@node-red/runtime/lib/flows/util_spec.js test/unit/@node-red/runtime/lib/flows/Flow_spec.js` → **92 passing (2s)**。克隆仓库 `git status` 干净。
- **BLIIOT 相关性（待实机验证的推断）：** BL118 的 Node-RED 可用于协议采集→数据变换→MQTT/HTTP→告警流程演示；需继续核验固件版本、可用节点包、断网缓存及权限配置，不把推断当产品承诺。客户发现问题可围绕现场协议/寄存器、采集频率、云平台、离线缓存、告警和控制权限形成需求清单。
- **安全边界：** 未连接 BLIIOT 设备，未访问/写入 Joinf CRM 或客户个人信息，未发送营销消息，未更改公司系统配置。
- **报告计划与实际：** 原 8 轮任务 `cc55482d3664` 因 `HTTP 404: No endpoints found for owl-alpha` 用尽次数后结束；获客方向任务 `8ab175e22cad` 手动触发同样失败并已暂停，避免继续空跑。未更改 Hermes 模型配置。当前实际完成的客户开发研究见第1轮；自动小时汇报尚未恢复。

## 第1轮｜客户开发方向（2026-10-21 约11:40–11:44 CST，不足一小时）
研究 EspoCRM `espocrm/espocrm`：AGPL-3.0-or-later；实读 Lead 实体/权限元数据、PostForm API、CaptureService、ConfirmationSender、OptInConfirmation Job、集成测试。发现入站线索支持验证码、表单字段筛选与净化、邮箱/电话去重、可选双重确认、后台邮件确认、目标名单/团队归属和阶段流转；PII 字段标记及 doNotCall 审计。原创静态验证 8/8 通过；PHP/PHPUnit 因本机无 PHP 未运行。该 CRM 适合官网询盘转销售流程，不负责外部潜客发现或证明需求。后台小时任务因为 `owl-alpha` 返回 404 已暂停；这份是当前会话亲自完成的短时研究，不足一小时。详报 `hourly_01.md`。

## 后续小时记录
（由每小时研究轮次按实际执行结果追加；没有运行的内容不预填。）
