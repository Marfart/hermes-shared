#!/usr/bin/env python
"""
Model Fallback Monitor
监控主模型(openrouter/owl-alpha)健康状态
当检测到超时/429限速/连接失败时，自动切换到备用模型
等主模型恢复后再切回来

用法: python model_fallback_monitor.py --once  (单次检查)
      python model_fallback_monitor.py          (守护循环)
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
CONFIG_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "hermes" / "config.yaml"
STATE_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "hermes" / "model_fallback_state.json"
LOG_PATH = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "hermes" / "scripts" / "model_fallback.log"

# 主模型（优先）
PRIMARY_PROVIDER = "openrouter"
PRIMARY_MODEL = "owl-alpha"

# 备用模型（主模型不可用时）
FALLBACK_PROVIDER = "ollama-cloud"
FALLBACK_MODEL = "glm-5.1"

# 检查间隔（秒）
CHECK_INTERVAL = 120

# 连续失败多少次才切换
FAIL_THRESHOLD = 2

# 切回主模型前等待的秒数（给主模型恢复时间）
RECOVERY_WAIT = 300

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_PATH), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("model-fallback")


def run_cmd(*args, timeout=10):
    try:
        r = subprocess.run(list(args), capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)


def get_current_model():
    """读取当前 config.yaml 中的 model 设置"""
    try:
        import yaml
        cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
        m = cfg.get("model", {})
        return m.get("provider", ""), m.get("model", "")
    except Exception:
        return "", ""


def set_model(provider, model):
    """切换模型"""
    run_cmd("hermes", "config", "set", "model.provider", provider)
    run_cmd("hermes", "config", "set", "model.model", model)
    log.info(f"🔄 模型切换: {provider}/{model}")


def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "using_fallback": False,
        "consecutive_failures": 0,
        "last_failure_time": None,
        "last_switch_time": None,
        "total_switches": 0,
    }


def save_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def check_primary_healthy():
    """
    用轻量请求测试主模型是否健康
    发送一个极简请求，检查是否返回有效响应
    """
    import urllib.request
    import urllib.error

    # 读取 OpenRouter API key
    env_path = CONFIG_PATH.parent / ".env"
    api_key = ""
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("OPENROUTER_API_KEY="):
                api_key = line.strip().split("=", 1)[1].strip()
                break

    if not api_key:
        log.warning("未找到 OPENROUTER_API_KEY，无法检测主模型")
        return True  # 无法检测时默认健康

    payload = json.dumps({
        "model": PRIMARY_MODEL,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 5,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                return True
            elif resp.status == 429:
                log.warning("主模型 429 Rate Limited")
                return False
            else:
                log.warning(f"主模型返回状态码: {resp.status}")
                return False
    except urllib.error.HTTPError as e:
        if e.code == 429:
            log.warning("主模型 429 Rate Limited")
        elif e.code == 401:
            log.error("主模型 401 Unauthorized — API Key 可能无效")
        else:
            log.warning(f"主模型 HTTP Error: {e.code}")
        return False
    except urllib.error.URLError as e:
        log.warning(f"主模型连接失败: {e.reason}")
        return False
    except Exception as e:
        log.warning(f"主模型检测异常: {e}")
        return False


def main():
    state = load_state()
    current_provider, current_model = get_current_model()

    log.info(f"🐴 模型Fallback监控启动")
    log.info(f"  主模型: {PRIMARY_PROVIDER}/{PRIMARY_MODEL}")
    log.info(f"  备用模型: {FALLBACK_PROVIDER}/{FALLBACK_MODEL}")
    log.info(f"  当前模型: {current_provider}/{current_model}")
    log.info(f"  使用备用: {state['using_fallback']}")

    is_healthy = check_primary_healthy()
    now = time.time()

    if state["using_fallback"]:
        # 当前在用备用模型，检查主模型是否恢复
        if is_healthy:
            # 主模型健康，检查是否已经过了恢复等待期
            last_switch = state.get("last_switch_time", 0)
            if now - last_switch >= RECOVERY_WAIT:
                log.info(f"✅ 主模型已恢复，切回 {PRIMARY_PROVIDER}/{PRIMARY_MODEL}")
                set_model(PRIMARY_PROVIDER, PRIMARY_MODEL)
                state["using_fallback"] = False
                state["consecutive_failures"] = 0
                state["last_switch_time"] = now
                state["total_switches"] += 1
                save_state(state)
            else:
                remaining = int(RECOVERY_WAIT - (now - last_switch))
                log.info(f"主模型已恢复，但需再等 {remaining}s 才切回")
        else:
            log.debug("主模型仍不可用，继续使用备用")
    else:
        # 当前在用主模型，检查是否健康
        if is_healthy:
            if state["consecutive_failures"] > 0:
                log.info("主模型恢复正常，重置失败计数")
                state["consecutive_failures"] = 0
                save_state(state)
        else:
            state["consecutive_failures"] += 1
            state["last_failure_time"] = now
            log.warning(f"主模型不健康 (连续失败 {state['consecutive_failures']}/{FAIL_THRESHOLD})")
            save_state(state)

            if state["consecutive_failures"] >= FAIL_THRESHOLD:
                log.warning(f"⚠️ 连续失败 {FAIL_THRESHOLD} 次，切换到备用模型")
                set_model(FALLBACK_PROVIDER, FALLBACK_MODEL)
                state["using_fallback"] = True
                state["last_switch_time"] = now
                state["total_switches"] += 1
                save_state(state)


if __name__ == "__main__":
    if "--once" in sys.argv:
        main()
    else:
        while True:
            try:
                main()
            except Exception as e:
                log.error(f"监控异常: {e}")
            time.sleep(CHECK_INTERVAL)
