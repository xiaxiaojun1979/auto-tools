#!/bin/bash
# Simple tunnel runner for LaunchAgent - keeps SSH alive and saves URL
LOG_FILE="/tmp/auto_tunnel_log.txt"
URL_FILE="/tmp/auto_tunnel_url.txt"

# Clean up old log
> "$LOG_FILE"

# Start SSH with forced PTY allocation and capture output
ssh -tt -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=30 \
    -o ExitOnForwardFailure=yes \
    -R 80:localhost:8080 \
    nokey@localhost.run 2>&1 | tee "$LOG_FILE" &

SSH_PID=$!

# Wait for URL
for i in $(seq 1 20); do
    URL=$(grep -oE "https://[a-zA-Z0-9-]+\.lhr\.life" "$LOG_FILE" 2>/dev/null | head -1)
    if [ -n "$URL" ]; then
        echo "$URL" > "$URL_FILE"
        echo "Tunnel ready: $URL"
        break
    fi
    sleep 1
done

# Keep the script alive while SSH is alive
wait $SSH_PID
