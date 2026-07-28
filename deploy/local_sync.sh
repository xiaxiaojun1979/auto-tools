#!/bin/bash
# AutoTools 本地同步到阿里云
# 在本地 Mac 上运行: bash deploy/local_sync.sh

LOCAL_DIR="/Users/tianmengpiaoxiang/auto_business"
REMOTE="root@118.31.4.27:/opt/autotools/"
KEY="/Users/tianmengpiaoxiang/.ssh/id_rsa_aliyun"

echo "🚀 同步代码到阿里云服务器..."
rsync -avz --delete \
    -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='cloudflared' \
    --exclude='ngrok' \
    --exclude='.DS_Store' \
    --exclude='*.tar.gz' \
    --exclude='xianyu_products/' \
    --exclude='daily_report/reports/*.html' \
    "$LOCAL_DIR/app.py" \
    "$LOCAL_DIR/email_report.py" \
    "$LOCAL_DIR/templates/" \
    "$REMOTE" 2>&1 | tail -5

echo ""
echo "🔄 重启服务..."
ssh -i "$KEY" -o StrictHostKeyChecking=no root@118.31.4.27 "systemctl restart autotools" 2>&1

echo ""
echo "✅ 同步完成!"
echo "🌐 http://118.31.4.27"
echo "📋 后台密码: xxj63858930"
