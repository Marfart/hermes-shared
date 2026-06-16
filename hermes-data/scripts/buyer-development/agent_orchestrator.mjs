#!/usr/bin/env node
/**
 * BLIIOT Multi-Agent Orchestrator v1.0
 * ======================================
 * 
 * 灵感来源：CrewAI 角色分离模式 + LangGraph 状态机
 * 
 * 把扁平管道拆成 5 个专业 Agent：
 * 
 * ┌──────────────────────────────────────────────────────────────┐
 * │                    Coordinator Agent 🎯                      │
 * │  管道状态管理、任务调度、错误恢复、进度报告                      │
 * └────────────────┬─────────────────────────────────────────────┘
 *                  │ 派发任务
 *     ┌───────────┼───────────┬───────────┬───────────┐
 *     ▼           ▼           ▼           ▼           ▼
 *  ┌──────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
 *  │Scout │  │Analyst │  │Followup│  │Messenger│  │Sender  │
 *  │侦查员│  │分析员  │  │跟進文檔│  │消息渲染│  │发送员  │
 *  └──┬───┘  └───┬────┘  └───┬────┘  └───┬────┘  └───┬────┘
 *     │搜索客户   │增强分析   │生成跟进    │渲染消息    │发送消息
 *     │joinf/    │评分/      │文档        │4种style    │WhatsApp
 *     │Maps      │匹配产品   │            │变体        │Email
 *     └──────────┴──────────┴────────────┴────────────┴────────┘
 */

import { execFile, spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

// ====================================================================
// 配置
// ====================================================================
const SCRIPTS_DIR = path.join(import.meta.dirname || ".");
const MEMORIES_DIR = path.join(
  process.env.LOCALAPPDATA || "C:\\Users\\Admin\\AppData\\Local",
  "hermes", "memories", "buyer-development"
);

const STATE_FILE = path.join(SCRIPTS_DIR, "orchestrator_state.json");

// Pipeline stages as they map to CrewAI-style agent roles
const PIPELINE_AGENTS = {
  scout: {
    name: "🕵️ Scout Agent",
    desc: "搜索客户线索",
    scripts: ["fetch_joinf_business_search.mjs", "scrape_google_maps_fresh_seeds.mjs"],
    parallel: false,
    rollback_stage: null,
  },
  analyst: {
    name: "📊 Analyst Agent",
    desc: "增强分析+评分匹配",
    scripts: ["enrich_joinf_business_search.mjs", "enrich_google_maps_leads.mjs"],
    parallel: true, // 两种来源可以并行分析
    rollback_stage: "scout",
  },
  followup: {
    name: "📋 Followup Agent",
    desc: "生成跟进文档",
    scripts: ["build_followup_document.mjs"],
    parallel: false,
    rollback_stage: "analyst",
  },
  queue: {
    name: "📝 Queue Agent",
    desc: "构建发送队列",
    scripts: ["build_whatsapp_queue.mjs"],
    parallel: false,
    rollback_stage: "followup",
  },
  messenger: {
    name: "💬 Messenger Agent",
    desc: "渲染个性化消息",
    scripts: ["render_whatsapp_messages.mjs"],
    parallel: false,
    rollback_stage: "queue",
  },
  sender: {
    name: "📤 Sender Agent",
    desc: "发送消息",
    scripts: ["whatsapp_bulk_sender_cdp.mjs"],
    parallel: false,
    rollback_stage: "messenger",
  },
};

// ====================================================================
// 状态管理（检查点模式）
// ====================================================================
class OrchestratorState {
  constructor() {
    this.pipeline = null;        // "joinf" | "google-maps" | "dual"
    this.current_stage = null;   // current agent role
    this.completed_stages = [];
    this.failed_stages = [];
    this.stage_results = {};
    this.errors = [];
    this.started_at = null;
    this.last_run_at = null;
    this.pid = null;
  }

  static async load() {
    try {
      const raw = await fs.readFile(STATE_FILE, "utf8");
      return Object.assign(new OrchestratorState(), JSON.parse(raw));
    } catch {
      return new OrchestratorState();
    }
  }

  async save() {
    this.last_run_at = new Date().toISOString();
    await fs.writeFile(STATE_FILE, JSON.stringify(this, null, 2), "utf8");
  }

  async resume(stage_name) {
    // 回滚到指定 stage，清理之后的状态
    const idx = Object.keys(PIPELINE_AGENTS).indexOf(stage_name);
    if (idx === -1) return false;
    const allStages = Object.keys(PIPELINE_AGENTS);
    this.completed_stages = allStages.slice(0, idx);
    this.current_stage = stage_name;
    this.failed_stages = [];
    return true;
  }
}

// ====================================================================
// 执行器
// ====================================================================
async function runScript(scriptName, args = [], timeout = 600) {
  const scriptPath = path.join(SCRIPTS_DIR, scriptName);
  console.log(`  ▶ 执行: ${scriptName} ${args.join(" ")}`);

  return new Promise((resolve, reject) => {
    const child = spawn("node", [scriptPath, ...args], {
      cwd: SCRIPTS_DIR,
      stdio: ["ignore", "pipe", "pipe"],
      timeout,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (d) => { stdout += d.toString(); });
    child.stderr.on("data", (d) => { stderr += d.toString(); });

    child.on("close", (code) => {
      resolve({ code, stdout, stderr });
    });
    child.on("error", (err) => {
      reject(err);
    });
  });
}

// ====================================================================
// 主逻辑
// ====================================================================
async function runPipeline(pipelineName, options = {}) {
  const state = await OrchestratorState.load();
  const { resume = null, dryRun = false } = options;

  // 选择管道
  if (pipelineName === "joinf" || pipelineName === "google-maps") {
    state.pipeline = pipelineName;
  } else if (pipelineName === "dual" || pipelineName === "all") {
    state.pipeline = "dual";
  } else {
    console.error(`❌ 未知管道: ${pipelineName}`);
    process.exit(1);
  }

  if (!state.started_at) {
    state.started_at = new Date().toISOString();
  }
  state.pid = process.pid;

  // 确定从哪个 stage 开始
  let startIdx = 0;
  const allStages = Object.keys(PIPELINE_AGENTS);

  if (resume) {
    const resumeIdx = allStages.indexOf(resume);
    if (resumeIdx >= 0) {
      startIdx = resumeIdx;
      await state.resume(resume);
      console.log(`\n🔄 从 ${resume} 断点续跑\n`);
    }
  } else if (state.current_stage && state.completed_stages.length > 0) {
    startIdx = allStages.indexOf(state.current_stage);
    if (startIdx > 0) startIdx; // 从当前 stage 继续，不跳过
  }

  const stages = allStages.slice(startIdx);
  const pipelineLabel = pipelineName === "dual" ? "双管道" : pipelineName;

  console.log(`\n${"═".repeat(56)}`);
  console.log(`  🎯 BLIIOT Multi-Agent Orchestrator`);
  console.log(`  管道: ${pipelineLabel}  |  模式: ${dryRun ? "预览" : "执行"}`);
  console.log(`${"═".repeat(56)}\n`);

  for (const stage of stages) {
    const agent = PIPELINE_AGENTS[stage];
    console.log(`\n${"─".repeat(48)}`);
    console.log(`  ${agent.name} — ${agent.desc}`);
    console.log(`${"─".repeat(48)}`);

    // 跳过不适用于当前管道的 stage
    if (pipelineName === "joinf" && stage === "scout") {
      // joinf 管道只跑 fetch_joinf
      console.log(`  ℹ️  执行 fetch_joinf_business_search.mjs`);
    } else if (pipelineName === "google-maps" && stage === "scout") {
      console.log(`  ℹ️  执行 scrape_google_maps_fresh_seeds.mjs`);
    }

    if (dryRun) {
      console.log(`  🔍 [预览] 将要执行: ${agent.scripts.join(", ")}`);
      state.completed_stages.push(stage);
      continue;
    }

    state.current_stage = stage;

    // 执行脚本（支持并行和串行）
    const scriptsToRun = agent.scripts.filter(s => {
      if (pipelineName === "joinf" && s.includes("google")) return false;
      if (pipelineName === "google-maps" && s.includes("joinf")) return false;
      return true;
    });

    let allPassed = true;

    if (agent.parallel && scriptsToRun.length > 1) {
      // 并行执行
      const results = await Promise.all(
        scriptsToRun.map(s => runScript(s, [], 600).catch(e => ({ code: -1, stderr: e.message })))
      );
      for (let i = 0; i < scriptsToRun.length; i++) {
        const r = results[i];
        if (r.code === 0 || r.code === null) {
          console.log(`  ✅ ${scriptsToRun[i]} 完成`);
        } else {
          console.log(`  ❌ ${scriptsToRun[i]} 失败 (code=${r.code})`);
          if (r.stderr) console.log(`     ${r.stderr.slice(0, 200)}`);
          allPassed = false;
        }
      }
    } else {
      // 串行执行
      for (const script of scriptsToRun) {
        const r = await runScript(script, [], 600);
        if (r.code === 0 || r.code === null) {
          console.log(`  ✅ ${script} 完成`);
          // 提取关键结果信息
          const infoLines = r.stdout.split("\n").filter(l => l.includes("✅") || l.includes("📊") || l.includes("📝"));
          infoLines.slice(0, 3).forEach(l => console.log(`     ${l.trim()}`));
        } else {
          console.log(`  ❌ ${script} 失败 (code=${r.code})`);
          if (r.stderr) console.log(`     ${r.stderr.slice(0, 200)}`);
          allPassed = false;
          state.errors.push({ stage, script, code: r.code, error: r.stderr.slice(0, 200) });
        }
      }
    }

    if (allPassed) {
      state.completed_stages.push(stage);
    } else {
      state.failed_stages.push(stage);
      console.log(`\n  ⚠️  ${agent.name} 失败, 回滚点: ${agent.rollback_stage || "无"}`);
      console.log(`  可在修复后用 --resume ${stage} 断点续跑`);
      await state.save();
      process.exit(1);
    }

    await state.save();
  }

  // 完成
  const duration = state.started_at
    ? Math.round((Date.now() - new Date(state.started_at).getTime()) / 1000)
    : 0;

  console.log(`\n${"═".repeat(56)}`);
  console.log(`  ✅ 管道执行完成！`);
  console.log(`  总耗时: ${Math.floor(duration / 60)}分${duration % 60}秒`);
  console.log(`  完成: ${state.completed_stages.length}/${allStages.length} 个阶段`);
  console.log(`${"═".repeat(56)}\n`);

  state.current_stage = null;
  await state.save();
}

// ====================================================================
// CLI
// ====================================================================
async function main() {
  const args = process.argv.slice(2);
  const cmd = args[0];

  if (!cmd || cmd === "--help" || cmd === "-h") {
    console.log(`
BLIIOT Multi-Agent Orchestrator v1.0
====================================

用法:
  node agent_orchestrator.mjs <command> [options]

命令:
  joinf              跑富通搜索管道
  google-maps        跑 Google Maps 管道  
  dual               跑双管道（推荐）
  status             查看管道状态
  reset              重置管道状态
  resume <stage>     从指定阶段断点续跑

阶段列表:
  scout       🕵️ 搜索客户线索
  analyst     📊 增强分析评分
  followup    📋 生成跟进文档
  queue       📝 构建发送队列
  messenger   💬 渲染消息
  sender      📤 发送消息

选项:
  --dry-run          预览模式（不执行）
  --help             显示帮助
`);
    return;
  }

  if (cmd === "status") {
    const state = await OrchestratorState.load();
    console.log(`\n📊 管道状态:\n`);
    console.log(`  管道:        ${state.pipeline || "-"}`);
    console.log(`  当前阶段:    ${state.current_stage || "-"}`);
    console.log(`  已完成:      ${state.completed_stages.join(" → ") || "-"}`);
    console.log(`  已失败:      ${state.failed_stages.join(", ") || "无"}`);
    console.log(`  开始时间:    ${state.started_at || "-"}`);
    console.log(`  最后运行:    ${state.last_run_at || "-"}`);
    if (state.errors.length > 0) {
      console.log(`\n  错误记录:`);
      state.errors.slice(-3).forEach(e =>
        console.log(`    ${e.stage}: ${e.error.slice(0, 100)}`)
      );
    }
    return;
  }

  if (cmd === "reset") {
    const fresh = new OrchestratorState();
    await fresh.save();
    console.log("✅ 状态已重置");
    return;
  }

  if (cmd === "resume") {
    const stage = args[1];
    if (!stage || !PIPELINE_AGENTS[stage]) {
      console.error(`❌ 无效阶段: ${stage}，可用: ${Object.keys(PIPELINE_AGENTS).join(", ")}`);
      process.exit(1);
    }
    const pipeline = args[2] || "dual";
    await runPipeline(pipeline, { resume: stage });
    return;
  }

  const options = {};
  if (args.includes("--dry-run")) options.dryRun = true;

  await runPipeline(cmd, options);
}

main().catch(err => {
  console.error(`❌ Orchestrator 异常:`, err.message);
  process.exit(1);
});
