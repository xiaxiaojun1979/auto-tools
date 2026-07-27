#!/usr/bin/env python3
"""快速看门狗 - 只检查服务器是否在运行，不在则重启"""
import socket, subprocess
from pathlib import Path

BASE = Path(__file__).parent
LOG = open("/tmp/auto_watchdog.log", "a")

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(5)
result = sock.connect_ex(('127.0.0.1', 8000))
sock.close()

if result != 0:
    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG.write(f"[{now}] ⚠️ 服务器离线，自动重启...\n")
    proc = subprocess.Popen(
        ["python3", "app.py"],
        cwd=str(BASE),
        stdout=open("/tmp/autotools_server.log", "a"),
        stderr=subprocess.STDOUT
    )
    LOG.write(f"[{now}] ✅ 服务器已重启 (PID: {proc.pid})\n")
else:
    pass  # 服务器运行正常
LOG.close()
