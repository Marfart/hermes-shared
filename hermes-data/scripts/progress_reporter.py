#!/c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe
"""Check recent activity and report if anything interesting is happening"""

import os, subprocess, json, time
from datetime import datetime

HERMES_HOME = r"C:\Users\Admin\AppData\Local\hermes"
WORKING_DIR = r"C:\Users\Admin\Desktop\Working"
REPORT_FILE = os.path.join(HERMES_HOME, ".last_5min_report")

now = time.time()
last_report = 0
try:
    if os.path.exists(REPORT_FILE):
        with open(REPORT_FILE) as f:
            last_report = float(f.read().strip())
except:
    pass

with open(REPORT_FILE, "w") as f:
    f.write(str(now))

# Check recent processes
recent_chrome = False
recent_terminal = False
try:
    result = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=10)
    processes = result.stdout
    chrome_count = processes.count("chrome.exe")
    if chrome_count > 5:
        recent_chrome = True
except:
    pass

# Check Working directory for recent changes
recent_files = []
try:
    result = subprocess.run(
        ["find", WORKING_DIR, "-maxdepth", "2", "-type", "f", "-newer", REPORT_FILE.replace(".last_5min_report", ".last_5min_check")],
        capture_output=True, text=True, timeout=10
    )
    if result.stdout.strip():
        recent_files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()][:5]
except:
    pass

# Create touch file for next comparison
check_file = REPORT_FILE.replace(".last_5min_report", ".last_5min_check")
try:
    open(check_file, "w").write(str(now))
except:
    pass

# Build report
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
report_parts = [f"[{ts}]"]

if recent_chrome:
    report_parts.append(f"Chrome运行中 ({chrome_count}进程)")
if recent_files:
    report_parts.append(f"最近文件变更: {len(recent_files)}个文件")
    
# Check if cron jobs are running
try:
    jobs_file = os.path.join(HERMES_HOME, "cron", "jobs.json")
    if os.path.exists(jobs_file):
        with open(jobs_file) as f:
            jobs = json.load(f)
        active_jobs = [j for j in (jobs if isinstance(jobs, list) else []) if j.get("enabled")]
        if active_jobs:
            report_parts.append(f"定时任务: {len(active_jobs)}个活跃")
except:
    pass

if len(report_parts) > 1:
    print(" | ".join(report_parts))
else:
    # Nothing to report - stay silent
    pass
