#!/usr/bin/env node
/**
 * BLIIOT Pipeline Commander v1.0
 * 
 * 融合三大源码项目精华模式：
 * ✅ JSON配置驱动（借鉴 arrangeit.py）
 * ✅ 环境健康检查（借鉴 env_check.py）
 * ✅ 定时+重试（借鉴 wifi_checker.py）
 * ✅ 检查点断点续跑（借鉴 checkpoint 思想）
 * ✅ 统一日志（借鉴 fileinfo.py 的优雅输出）
 * ✅ 跨平台预检（借鉴 ping_subnet.py 的 os.name 判断）
 * 
 * 用法：
 *   node pipeline_commander.mjs --pipeline joinf         # 跑富通管道
 *   node pipeline_commander.mjs --pipeline google-maps    # 跑谷歌地图管道
 *   node pipeline_commander.mjs --status                  # 查看管道状态
 *   node pipeline_commander.mjs --check                   # 全身体检
 *   node pipeline_commander.mjs --resume send             # 断点续跑发送
 *   node pipeline_commander.mjs --all                     # 全自动一条龙
 */

import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

// ====== 配置加载（JSON驱动模式 from arrangeit.py）======

const CONFIG_PATH = path.join(
  import.meta.dirname || ".",
  "pipeline_config.json"
);

async function loadConfig() {
  try {
    const raw = await fs.readFile(CONFIG_PATH, "utf8");
    return JSON.parse(raw);
  } catch (err) {
    console.error("❌ Cannot load pipeline_config.json:", err.message);
    console.error("   Expected at:", CONFIG_PATH);
    process.exit(1);
  }
}

// ====== 日志系统（借鉴 fileinfo.py 的优雅输出）======

const DATE_STAMP = (() => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
})();

const TIMESTAMP = (() => {
  const now = new Date();
  return `${now.toISOString().replace("T", " ").slice(0, 19)}`;
})();

function log(level, msg, data = null) {
  const icon = { INFO: "ℹ️", OK: "✅", WARN: "⚠️", ERROR: "❌", STEP: "🚀", CHECK: "🔍" }[level] || "•";
  const line = `[${TIMESTAMP}] ${icon} [${level.padEnd(5)}] ${msg}`;
  console.log(line);
  if (data) console.log("   └─", typeof data === "object" ? JSON.stringify(data) : data);
}

// ====== 健康检查系统（借鉴 env_check.py + ping_servers.py 的逐个验证模式）======

async function checkChromePort(port, label) {
  try {
    const { stdout } = await execFileAsync("curl", [
      "-s",
      `http://127.0.0.1:${port}/json/version`,
    ]);
    const info = JSON.parse(stdout);
    return { alive: true, browser: info.Browser || "Chromium", port, label };
  } catch {
    return { alive: false, port, label, error: "Port not responding" };
  }
}

async function checkScriptsExist(scriptsDir, requiredScripts) {
  const results = [];
  for (const script of requiredScripts) {
    const fullPath = path.join(scriptsDir, script);
    try {
      await fs.access(fullPath);
      results.push({ name: script, exists: true });
    } catch {
      results.push({ name: script, exists: false });
    }
  }
  return results;
}

async function checkOutputDir(outputDir) {
  try {
    await fs.mkdir(outputDir, { recursive: true });
    const stat = await fs.stat(outputDir);
    return { exists: true, size: `${(stat.size / 1024 / 1024).toFixed(1)} MB` };
  } catch {
    return { exists: false, error: "Cannot create directory" };
  }
}

async function runHealthCheck(cfg) {
  log("CHECK", "🩺 管道全身体检开始...");
  log("CHECK", "━━━━━━━━━━━━━━━━━━━━━━━━━━━");

  // 1. 脚本完整性检查
  const scriptsDir = cfg.paths.scripts_dir;
  const required = [
    "fetch_joinf_business_search.mjs",
    "enrich_joinf_business_search.mjs",
    "enrich_google_maps_leads.mjs",
    "build_whatsapp_queue.mjs",
    "build_followup_document.mjs",
    "render_whatsapp_messages.mjs",
    "whatsapp_bulk_sender_cdp.mjs",
    "chrome_cdp_launcher.mjs",
  ];
  const scriptChecks = await checkScriptsExist(scriptsDir, required);
  const missingScripts = scriptChecks.filter((s) => !s.exists);
  if (missingScripts.length === 0) {
    log("OK", `所有 ${required.length} 个核心脚本就位 ✓`);
  } else {
    log("WARN", `${missingScripts.length} 个脚本缺失:`, missingScripts.map((s) => s.name));
  }

  // 2. Chrome端口检查（借鉴 ping_subnet.py 的逐个ping模式）
  const portChecks = await Promise.all([
    checkChromePort(cfg.chrome_ports.joinf_search, "富通搜索"),
    checkChromePort(cfg.chrome_ports.whatsapp_send, "WhatsApp发送"),
  ]);
  for (const pc of portChecks) {
    if (pc.alive) {
      log("OK", `Chrome ${pc.label} 端口 ${pc.port} 在线 ✓ (${pc.browser})`);
    } else {
      log("WARN", `Chrome ${pc.label} 端口 ${pc.port} 离线 - 需要先启动浏览器`);
    }
  }

  // 3. 输出目录检查
  const dirCheck = await checkOutputDir(cfg.paths.output_dir);
  if (dirCheck.exists) {
    log("OK", `输出目录就绪 ✓`);
  }

  // 4. 配置完整性检查
  const hasJoinf = cfg.pipeline_steps.joinf?.enabled;
  const hasMaps = cfg.pipeline_steps.google_maps?.enabled;
  log("OK", `配置就绪: 富通=${hasJoinf ? "开" : "关"}, GoogleMaps=${hasMaps ? "开" : "关"}`);

  log("CHECK", "━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  log("OK", "体检完成！");
}

// ====== 检查点系统（断点续跑模式）======

const CHECKPOINT_PATH = path.join(
  path.resolve(import.meta.dirname || ".", "..", "..", "memories", "buyer-development"),
  "pipeline_checkpoint.json"
);

async function saveCheckpoint(step, status, data = {}) {
  const checkpoint = {
    last_update: TIMESTAMP,
    date_stamp: DATE_STAMP,
    step,
    status,
    ...data,
  };
  await fs.writeFile(CHECKPOINT_PATH, JSON.stringify(checkpoint, null, 2), "utf8");
  log("STEP", `检查点保存: ${step} = ${status}`);
}

async function loadCheckpoint() {
  try {
    const raw = await fs.readFile(CHECKPOINT_PATH, "utf8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

// ====== 核心执行引擎（借鉴 wifi_checker.py 的 retry 模式）======

async function runNode(scriptPath, args, cfg, maxRetries = 2) {
  const scriptName = path.basename(scriptPath);
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const { stdout, stderr } = await execFileAsync(
        process.execPath,
        [scriptPath, ...args],
        {
          env: {
            ...process.env,
            NODE_PATH: cfg.paths.node_path,
          },
          maxBuffer: 10 * 1024 * 1024,
          windowsHide: true,
        }
      );
      const output = stdout.trim();
      if (stderr) log("WARN", `${scriptName} stderr:`, stderr.slice(0, 200));
      return { success: true, output, scriptName };
    } catch (err) {
      const errMsg = err.message?.slice(0, 300) || String(err);
      if (attempt < maxRetries) {
        log("WARN", `${scriptName} 第${attempt}次失败，重试中...\n   └─ ${errMsg}`);
        await new Promise((r) => setTimeout(r, 2000 * attempt)); // 退避等待
      } else {
        log("ERROR", `${scriptName} 第${attempt}次均失败！`, errMsg);
        return { success: false, error: errMsg, scriptName };
      }
    }
  }
  return { success: false, error: "Max retries exceeded", scriptName };
}

// ====== 管道步骤执行器 ======

async function runJoinfPipeline(cfg) {
  log("STEP", "🚀 富通管道启动...");
  const { scripts_dir: SCRIPTS_DIR, output_dir: OUTPUT_DIR } = cfg.paths;
  const jc = cfg.pipeline_steps.joinf;

  // Step 1: 搜索
  log("STEP", "Step 1/5: 富通搜索客户...");
  const rawBase = `${jc.output_prefix}_${DATE_STAMP}`;
  const r1 = await runNode(
    path.join(SCRIPTS_DIR, "fetch_joinf_business_search.mjs"),
    [OUTPUT_DIR, rawBase, `http://127.0.0.1:${cfg.chrome_ports.joinf_search}`],
    cfg
  );
  if (!r1.success) { log("ERROR", "❌ 搜索失败，管道中止"); return false; }
  await saveCheckpoint("joinf_fetch", "done", { base: rawBase });

  // Step 2: 增强分析
  log("STEP", "Step 2/5: AI增强分析...");
  const enrichedBase = `${jc.enrich_prefix}_${DATE_STAMP}`;
  const rawJsonPath = path.join(OUTPUT_DIR, `${rawBase}.json`);
  const r2 = await runNode(
    path.join(SCRIPTS_DIR, "enrich_joinf_business_search.mjs"),
    [rawJsonPath, OUTPUT_DIR, enrichedBase],
    cfg
  );
  if (!r2.success) { log("ERROR", "❌ 增强分析失败"); return false; }
  await saveCheckpoint("joinf_enrich", "done", { base: enrichedBase });

  // Step 3: 构建队列
  log("STEP", "Step 3/5: 构建WhatsApp队列...");
  const queueBase = `${jc.queue_prefix}_${DATE_STAMP}`;
  const enrichedJsonPath = path.join(OUTPUT_DIR, `${enrichedBase}.json`);
  const r3 = await runNode(
    path.join(SCRIPTS_DIR, "build_whatsapp_queue.mjs"),
    [enrichedJsonPath, OUTPUT_DIR, queueBase],
    cfg
  );
  if (!r3.success) { log("ERROR", "❌ 构建队列失败"); return false; }
  await saveCheckpoint("joinf_queue", "done", { base: queueBase });

  // Step 4: 生成跟进文档
  log("STEP", "Step 4/5: 生成跟进文档...");
  const followupBase = `${jc.followup_prefix}_${DATE_STAMP}`;
  const queueJsonPath = path.join(OUTPUT_DIR, `${queueBase}.json`);
  const r4 = await runNode(
    path.join(SCRIPTS_DIR, "build_followup_document.mjs"),
    [enrichedJsonPath, queueJsonPath, OUTPUT_DIR, followupBase],
    cfg
  );
  if (!r4.success) { log("ERROR", "❌ 跟进文档生成失败"); return false; }
  await saveCheckpoint("joinf_followup", "done", { base: followupBase });

  // Step 5: 渲染消息
  log("STEP", "Step 5/5: 渲染WhatsApp消息...");
  const messagesBase = `${jc.messages_prefix}_${DATE_STAMP}`;
  const r5 = await runNode(
    path.join(SCRIPTS_DIR, "render_whatsapp_messages.mjs"),
    [queueJsonPath, OUTPUT_DIR, messagesBase],
    cfg
  );
  if (!r5.success) { log("ERROR", "❌ 消息渲染失败"); return false; }
  await saveCheckpoint("joinf_render", "done", { base: messagesBase });

  log("OK", `🎉 富通管道全部完成！`);
  log("INFO", `   队列: ${queueBase}.json`);
  log("INFO", `   跟进: ${followupBase}.json`);
  log("INFO", `   消息: ${messagesBase}.json`);
  return true;
}

async function runSend(cfg, pipeline = "joinf") {
  log("STEP", "📤 启动WhatsApp发送...");
  const jc = cfg.pipeline_steps[pipeline] || cfg.pipeline_steps.joinf;
  const messagesBase = `${jc.messages_prefix}_${DATE_STAMP}`;
  const OUTPUT_DIR = cfg.paths.output_dir;

  // 检查消息文件
  const messagesPath = path.join(OUTPUT_DIR, `${messagesBase}.json`);
  try {
    await fs.access(messagesPath);
  } catch {
    // 尝试从检查点找
    const cp = await loadCheckpoint();
    if (cp?.messagesBase) {
      const altPath = path.join(OUTPUT_DIR, `${cp.messagesBase}.json`);
      try {
        await fs.access(altPath);
        log("INFO", `使用检查点路径: ${cp.messagesBase}.json`);
        messagesPath = altPath;
      } catch {
        log("ERROR", "找不到消息文件，请先跑 --pipeline");
        return false;
      }
    } else {
      log("ERROR", "找不到消息文件，请先跑 --pipeline");
      return false;
    }
  }

  const r = await runNode(
    path.join(cfg.paths.scripts_dir, "whatsapp_bulk_sender_cdp.mjs"),
    ["--mode", "send", "--queue", messagesPath, "--limit", String(jc.send_limit || 50)],
    cfg
  );
  if (r.success) {
    log("OK", "✅ WhatsApp发送完成！");
    await saveCheckpoint("send", "done", { pipeline, messagesBase, sentAt: TIMESTAMP });
  }
  return r.success;
}

// ====== 状态查看（借鉴 fileinfo.py 的字典驱动输出模式）======

async function showStatus(cfg) {
  log("INFO", "📊 管道状态报告");
  log("INFO", "━━━━━━━━━━━━━━━━━━━━");

  const cp = await loadCheckpoint();
  if (cp) {
    log("OK", `上次运行: ${cp.last_update}`);
    log("INFO", `最后步骤: ${cp.step} = ${cp.status}`);
    log("INFO", `日期标记: ${cp.date_stamp}`);
  } else {
    log("INFO", "尚无运行记录");
  }

  // 列出输出目录中的最新文件
  const outputDir = cfg.paths.output_dir;
  try {
    const files = await fs.readdir(outputDir);
    const jsonFiles = files
      .filter((f) => f.endsWith(".json") && !f.includes("checkpoint"))
      .sort()
      .reverse()
      .slice(0, 10);
    if (jsonFiles.length) {
      log("INFO", "\n📁 最近输出文件:");
      for (const f of jsonFiles) {
        const stat = await fs.stat(path.join(outputDir, f));
        const size = (stat.size / 1024).toFixed(1);
        log("INFO", `   ${f} (${size} KB)`);
      }
    }
  } catch {
    log("WARN", "输出目录不可读");
  }
}

// ====== 主入口 ======

async function main() {
  const args = process.argv.slice(2);
  const cfg = await loadConfig();

  // 借鉴 argparse 模式（从 batch_file_rename.py）
  const opts = {
    pipeline: null,
    mode: "run",
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case "--pipeline":
        opts.pipeline = args[++i] || null;
        break;
      case "--check":
        opts.mode = "check";
        break;
      case "--status":
        opts.mode = "status";
        break;
      case "--resume":
        opts.mode = "resume";
        opts.resumeStep = args[++i] || "send";
        break;
      case "--all":
        opts.mode = "all";
        break;
      case "--help":
      case "-h":
        console.log(`
BLIIOT Pipeline Commander v1.0

用法:
  node pipeline_commander.mjs --pipeline joinf       # 跑富通管道
  node pipeline_commander.mjs --pipeline google-maps  # 跑谷歌地图管道
  node pipeline_commander.mjs --check                 # 全身体检
  node pipeline_commander.mjs --status                # 查看状态
  node pipeline_commander.mjs --resume send           # 断点续跑发送
  node pipeline_commander.mjs --all                   # 全自动一条龙
  node pipeline_commander.mjs --help                  # 显示帮助
`);
        process.exit(0);
    }
  }

  // == 模式分发 ==
  if (opts.mode === "check") {
    await runHealthCheck(cfg);
  } else if (opts.mode === "status") {
    await showStatus(cfg);
  } else if (opts.mode === "resume") {
    log("INFO", `🔄 断点续跑模式: ${opts.resumeStep}`);
    if (opts.resumeStep === "send") {
      const cp = await loadCheckpoint();
      const pipeline = cp?.pipeline || "joinf";
      await runSend(cfg, pipeline);
    }
  } else if (opts.mode === "all") {
    log("STEP", "🔥 全自动一条龙模式启动！");
    log("STEP", "━━━━━━━━━━━━━━━━━━━━━━━━━");
    
    // 先体检
    await runHealthCheck(cfg);
    
    // 再跑富通管道
    const joinfOk = await runJoinfPipeline(cfg);
    if (joinfOk) {
      log("OK", "富通管道完成，开始发送...");
      await runSend(cfg, "joinf");
    }
  } else if (opts.pipeline === "joinf") {
    await runJoinfPipeline(cfg);
  } else if (opts.pipeline === "google-maps") {
    log("INFO", "Google Maps管道由 run_google_maps_to_whatsapp_pipeline.mjs 负责");
    log("INFO", "请直接运行: node run_google_maps_to_whatsapp_pipeline.mjs");
  } else {
    log("WARN", "未指定管道，使用 --check 或 --help");
    await runHealthCheck(cfg);
  }
}

main().catch((err) => {
  console.error("❌ 致命错误:", err.message);
  process.exit(1);
});