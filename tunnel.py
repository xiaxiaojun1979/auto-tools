#!/usr/bin/env python3
"""
Tunnel Manager - 将本地服务暴露到公网
Use localhost.run (free, no registration)
"""
import subprocess, time, os, signal, re, sys
from urllib.request import urlopen

PID_FILE = "/tmp/auto_tunnel.pid"
LOG_FILE = "/tmp/auto_tunnel.log"

def start_tunnel():
    """Start SSH tunnel to localhost.run"""
    kill_tunnel()
    
    # Wait for server
    for i in range(10):
        try:
            urlopen("http://127.0.0.1:8080", timeout=2)
            break
        except:
            time.sleep(1)
    
    # Start tunnel with output capture
    with open(LOG_FILE, 'w') as log:
        proc = subprocess.Popen(
            ['ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'ServerAliveInterval=30',
             '-o', 'ExitOnForwardFailure=yes',
             '-R', '80:localhost:8080',
             'nokey@localhost.run'],
            stdout=log, stderr=subprocess.STDOUT, text=True
        )
    
    with open(PID_FILE, 'w') as f:
        f.write(str(proc.pid))
    
    # Wait for URL
    time.sleep(8)
    url = get_url()
    return url

def get_url():
    """Extract URL from tunnel log"""
    try:
        with open(LOG_FILE, 'r') as f:
            content = f.read()
        match = re.search(r'([a-zA-Z0-9-]+\.lhr\.life)', content)
        if match:
            return f"https://{match.group(1)}"
    except:
        pass
    return None

def kill_tunnel():
    """Kill existing tunnel"""
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
    except:
        pass
    os.system("pkill -f 'nokey@localhost.run' 2>/dev/null")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        kill_tunnel()
        print("Tunnel stopped")
    else:
        url = start_tunnel()
        if url:
            print(f"\n🌐 公网地址: {url}")
            print(f"📋 管理后台: {url}/admin")
            print(f"\n⚠️  注意：此地址每次重启都会变化")
            print(f"   请不要关闭此窗口")
        else:
            print("Tunnel starting... check status with:")
            print(f"  cat {LOG_FILE}")
