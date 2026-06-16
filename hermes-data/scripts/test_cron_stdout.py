#!/usr/bin/env python3
"""test_cron_stdout.py — 验证cron能否捕获stdout"""
import sys
print("HELLO FROM CRON TEST")
sys.stdout.flush()