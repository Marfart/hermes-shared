# -*- coding: utf-8 -*-
"""测试 cron GBK 编码 v2"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gbk')
print("[看门狗] 证书升级 + DNS 刷新完成")
print("[状态] 平台: telegram=connected + weixin=connected")
print("[诊断] 六层诊断: 全部正常")
