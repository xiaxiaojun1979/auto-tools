#!/bin/bash
set -e
echo "🚀 AutoTools 国内服务器一键部署"
echo "==============================="

# 安装依赖
echo "[1/5] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip nginx git 2>/dev/null || yum install -y python3 python3-pip nginx git 2>/dev/null

# 获取代码
echo "[2/5] 下载代码..."
cd /opt
if [ -d auto-tools ]; then
    cd auto-tools && git pull
else
    git clone https://github.com/xiaxiaojun1979/auto-tools.git
    cd auto-tools
fi

# 安装Python依赖
echo "[3/5] 安装Python依赖..."
pip3 install -r requirements.txt -q

# 配置systemd服务
echo "[4/5] 配置开机自启..."
cat > /etc/systemd/system/autotools.service << 'UNIT'
[Unit]
Description=AutoTools Web App
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/auto-tools
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable autotools
systemctl restart autotools

# 配置Nginx反向代理
echo "[5/5] 配置Nginx..."
cat > /etc/nginx/sites-available/autotools << 'NGINX'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
NGINX

if [ -d /etc/nginx/sites-enabled ]; then
    ln -sf /etc/nginx/sites-available/autotools /etc/nginx/sites-enabled/
fi
nginx -t && systemctl restart nginx

echo ""
echo "✅ 部署完成！"
echo "🌐 访问: http://服务器IP"
echo "📋 后台: http://服务器IP/admin"
echo "🔑 密码: xxj63858930"
echo ""
echo "查看状态: systemctl status autotools"
echo "查看日志: journalctl -u autotools -f"
