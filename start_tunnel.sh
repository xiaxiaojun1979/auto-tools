#!/bin/bash
# Start SSH tunnel to localhost.run
cd /Users/tianmengpiaoxiang/auto_business
nohup script -q /tmp/tunnel_out.txt ssh -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=30 \
  -R 80:localhost:8080 \
  nokey@localhost.run > /dev/null 2>&1 &
TUNNEL_PID=$!
echo $TUNNEL_PID > /tmp/auto_tunnel_pid.txt
echo "Tunnel started with PID: $TUNNEL_PID"
# Wait for URL
sleep 12
grep -oE 'https://[a-zA-Z0-9-]+\.lhr\.life' /tmp/tunnel_out.txt | head -1
