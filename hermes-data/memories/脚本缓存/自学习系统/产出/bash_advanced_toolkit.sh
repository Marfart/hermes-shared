#!/usr/bin/env bash
#===============================================================================
# Bash 高级脚本工具包 v1.0
# 学习自: dylanaraps/pure-bash-bible (36k+ ⭐)
#
# 功能:
#   1. 高级错误处理框架 (trap + ERR + 退出码)
#   2. 并行执行引擎 (纯bash后台进程+wait)
#   3. 管道优化与流处理
#   4. 日志系统 (分级+旋转)
#   5. 进度条与交互反馈
#   6. 函数式工具集 (从pure-bash-bible提取)
#
# 使用: source bash_advanced_toolkit.sh 或 bash bash_advanced_toolkit.sh
#===============================================================================

set -o pipefail  # 管道中任一命令失败都视为失败
shopt -s expand_aliases  # 允许别名在非交互shell工作

# ========== 颜色/ANSI 工具 ==========
readonly C_RESET='\e[m'
readonly C_BOLD='\e[1m'
readonly C_RED='\e[31m'
readonly C_GREEN='\e[32m'
readonly C_YELLOW='\e[33m'
readonly C_BLUE='\e[34m'
readonly C_CYAN='\e[36m'
readonly C_GRAY='\e[90m'

# ========== 日志系统 (分级+带时间戳) ==========
LOG_LEVEL=${LOG_LEVEL:-3}       # 0=ERROR 1=WARN 2=INFO 3=DEBUG
LOG_FILE="${LOG_FILE:-/tmp/bash_toolkit_$$.log}"

_log() {
    local level="$1" color="$2" msg="$3"
    local timestamp
    printf -v timestamp '%(%Y-%m-%d %H:%M:%S)T' -1
    # 终端输出
    echo -e "${color}[${level}]${C_RESET} ${timestamp} - ${msg}" >&2
    # 文件输出 (无颜色)
    echo "[${level}] ${timestamp} - ${msg}" >> "$LOG_FILE"
}

error()   { _log "ERROR"   "$C_RED"    "$1"; [[ -n "${2:-}" ]] && exit "$2"; }
warn()    { _log "WARN"    "$C_YELLOW" "$1"; }
info()    { _log "INFO"    "$C_GREEN"  "$1"; }
debug()   { (( LOG_LEVEL >= 3 )) && _log "DEBUG"   "$C_GRAY"    "$1"; :; }

# ========== 错误处理框架 ==========

# 错误处理钩子：每个命令执行完检查
__err_handler() {
    local ret=$?
    local last_cmd="${BASH_COMMAND}"
    [[ $ret -eq 0 ]] && return 0
    error "命令失败 [退出码=$ret]: ${last_cmd}"
}

# 退出清理：确保临时文件被删除
__cleanup() {
    local ret=$?
    if [[ -n "${__TEMP_DIRS:-}" ]]; then
        for d in $__TEMP_DIRS; do
            [[ -d "$d" ]] && rm -rf "$d"
        done
    fi
    info "清理完成，退出码: $ret"
    exit "$ret"
}

# 设定严格模式
strict_mode() {
    set -euo pipefail
    trap '__err_handler' ERR
    trap '__cleanup' EXIT
    info "严格模式已启用"
}

# ========== 注册临时资源 ==========
declare -a __TEMP_DIRS=()

make_temp_dir() {
    local template="${1:-tmp.XXXXXX}"
    local dir
    dir="$(mktemp -d "/tmp/${template}")"
    __TEMP_DIRS+=("$dir")
    printf '%s\n' "$dir"
}

# ========== 并行执行引擎 ==========

declare -A __JOB_PIDS=()   # job_name -> pid
declare -A __JOB_OUT=()    # job_name -> output file
declare -a __JOB_NAMES=()  # ordered job names

# 并行运行命令，收集输出
# 用法: parallel_run "job_name" "命令字符串"
parallel_run() {
    local job_name="$1" cmd="$2"
    local outfile
    outfile="$(mktemp "/tmp/parallel_${job_name}_XXXXXX.out")"
    __JOB_OUT["$job_name"]="$outfile"
    __JOB_NAMES+=("$job_name")

    (
        # 在子shell中执行，捕获输出
        eval "$cmd" > "$outfile" 2>&1
        exit $?
    ) &
    local pid=$!
    __JOB_PIDS["$job_name"]=$pid
    debug "作业 '${job_name}' 已启动 (PID: $pid)"
}

# 等待所有并行作业完成
# 返回: 0=全部成功, 1=有失败
parallel_wait() {
    local failed=0
    local all_ok=true

    for job_name in "${__JOB_NAMES[@]}"; do
        local pid="${__JOB_PIDS[$job_name]}"
        local outfile="${__JOB_OUT[$job_name]}"

        wait "$pid" 2>/dev/null
        local ret=$?

        if [[ $ret -eq 0 ]]; then
            info "✅ 作业 '${job_name}' 成功"
        else
            error "❌ 作业 '${job_name}' 失败 (退出码: $ret)"
            all_ok=false
            ((failed++))
        fi

        # 输出结果摘要 (最多20行)
        if [[ -f "$outfile" ]]; then
            local line_count
            line_count=$(wc -l < "$outfile")
            if (( line_count > 0 )); then
                echo -e "${C_GRAY}--- ${job_name} 输出 ---${C_RESET}" >&2
                if (( line_count <= 20 )); then
                    cat "$outfile" >&2
                else
                    head -n 10 "$outfile" >&2
                    echo -e "${C_YELLOW}... ($((line_count - 10)) more lines) ...${C_RESET}" >&2
                fi
            fi
            rm -f "$outfile"
        fi
    done

    # 清空状态
    __JOB_PIDS=()
    __JOB_OUT=()
    __JOB_NAMES=()

    $all_ok && return 0 || return 1
}

# 带超时的并行等待
parallel_wait_timeout() {
    local timeout="$1"  # 秒
    local deadline=$(( $(date +%s) + timeout ))

    for job_name in "${__JOB_NAMES[@]}"; do
        local pid="${__JOB_PIDS[$job_name]}"
        local remaining=$(( deadline - $(date +%s) ))

        if (( remaining <= 0 )); then
            warn "作业 '${job_name}' 超时，强制终止 (PID: $pid)"
            kill "$pid" 2>/dev/null || true
            continue
        fi

        # 带超时的 wait
        timeout "$remaining" wait "$pid" 2>/dev/null || {
            warn "作业 '${job_name}' 超时"
            kill "$pid" 2>/dev/null || true
        }
    done
}

# ========== 管道优化工具 ==========

# 去重流 (保留顺序)
dedup_lines() {
    awk '!seen[$0]++'
}

# 只保留匹配行上下文的行 (替代 grep -C)
grep_context() {
    local pattern="$1" before="${2:-0}" after="${3:-0}"
    awk -v pat="$pattern" -v b="$before" -v a="$after" '
    {
        lines[NR] = $0
        if ($0 ~ pat) {
            for (i = NR - b; i <= NR + a; i++) {
                if (i > 0 && !marked[i]) {
                    marked[i] = 1
                }
            }
        }
    }
    END {
        for (i = 1; i <= NR; i++) {
            if (marked[i]) print lines[i]
        }
    }'
}

# 缓冲行输出 (每N行刷新一次)
buffered_echo() {
    local batch_size="${1:-100}"
    local count=0 buf=""
    while IFS= read -r line; do
        buf+="${line}"$'\n'
        ((count++))
        if (( count >= batch_size )); then
            printf '%s' "$buf"
            buf=""
            count=0
        fi
    done
    printf '%s' "$buf"  # 剩余
}

# ========== 从 pure-bash-bible 提取的函数式工具 ==========

# 修剪空白 (纯bash, 不用sed)
trim_string() {
    : "${1#${1%%[![:space:]]*}}"
    : "${_%${_##*[![:space:]]}}"
    printf '%s\n' "$_"
}

# 分割字符串 (纯bash, 不用cut)
split() {
    IFS=$'\n' read -d "" -ra arr <<< "${1//$2/$'\n'}"
    printf '%s\n' "${arr[@]}"
}

# 大写/小写 (bash 4+)
lower() { printf '%s\n' "${1,,}"; }
upper() { printf '%s\n' "${1^^}"; }

# URL编码 (纯bash, 不用curl/python)
urlencode() {
    local LC_ALL=C
    for (( i = 0; i < ${#1}; i++ )); do
        : "${1:i:1}"
        case "$_" in
            [a-zA-Z0-9.~_-]) printf '%s' "$_" ;;
            *) printf '%%%02X' "'$_" ;;
        esac
    done
    printf '\n'
}

# 进度条 (纯bash)
progress_bar() {
    local elapsed=$1 total=${2:-50}
    local filled=$(( elapsed * total / 100 ))
    local empty=$(( total - filled ))
    printf -v prog "%${filled}s"
    printf -v rest "%${empty}s"
    printf '\r[%s%s] %3d%%' "${prog// /#}" "${rest// /-}" "$elapsed"
}

# UUID v4 (纯bash)
uuid() {
    C="89ab"
    for ((N=0; N<16; ++N)); do
        B="$((RANDOM%256))"
        case "$N" in
            6)  printf '4%x' "$((B%16))" ;;
            8)  printf '%c%x' "${C:$RANDOM%${#C}:1}" "$((B%16))" ;;
            3|5|7|9) printf '%02x-' "$B" ;;
            *) printf '%02x' "$B" ;;
        esac
    done
    printf '\n'
}

# 检查命令是否存在
has_cmd() { command -v "$1" &>/dev/null; }

# 获取脚本运行时间
elapsed() {
    printf '运行时间: %d 秒\n' "$SECONDS"
}

# ========== 演示/自测 ==========

demo() {
    echo -e "${C_BOLD}${C_CYAN}╔════════════════════════════════════════╗${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}║   Bash 高级脚本工具包 — 演示模式      ║${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}╚════════════════════════════════════════╝${C_RESET}"
    echo
    info "开始演示..."

    # 测试错误处理
    echo -e "\n${C_BOLD}1️⃣  测试错误处理${C_RESET}"
    info "故意运行一个失败命令..."
    command_not_exists_12345 2>/dev/null || warn "捕获到失败命令 (预期行为)"

    # 测试分割/字符串
    echo -e "\n${C_BOLD}2️⃣  字符串处理${C_RESET}"
    local test_str="  Hello,   Bash World!  "
    echo "原始字符串: '${test_str}'"
    echo "修剪后    : '$(trim_string "${test_str}")'"
    echo "大写      : $(upper "bash")"
    echo "分割 test:one:two:three →"
    split "test:one:two:three" ":" | sed 's/^/  /'

    # 测试并行执行
    echo -e "\n${C_BOLD}3️⃣  并行执行测试${C_RESET}"
    echo "启动3个并行作业..."
    parallel_run "ping_local"   "sleep 0.5 && echo 'ping 完成'"
    parallel_run "date_job"     "sleep 0.3 && echo '当前时间: $(date)'"
    parallel_run "calc_job"     "sleep 0.7 && echo '1+2+3+4+5 = $((1+2+3+4+5))'"
    parallel_wait || warn "部分作业失败"

    # 测试进度条
    echo -e "\n${C_BOLD}4️⃣  进度条演示${C_RESET}"
    for ((i=0; i<=100; i+=5)); do
        progress_bar "$i" 30
        sleep 0.05
    done
    printf '\n'

    # 测试URL编码
    echo -e "\n${C_BOLD}5️⃣  URL编码${C_RESET}"
    echo "$(urlencode "https://github.com/dylanaraps/pure-bash-bible")"

    # UUID
    echo -e "\n${C_BOLD}6️⃣  UUID生成${C_RESET}"
    echo "$(uuid)"
    echo "$(uuid)"

    echo -e "\n${C_GREEN}✅ 演示完成${C_RESET}"
    elapsed
}

# ========== 主入口 ==========
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # 作为独立脚本运行 → 执行demo
    demo
else
    # 被 source → 安静加载
    info "Bash工具包已加载。运行 demo() 查看示例。"
fi