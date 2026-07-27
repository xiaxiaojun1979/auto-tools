#!/bin/bash
echo "🚀 启动自动副业系统..."
echo ""
echo "📁 产品网站: http://localhost:8080"
echo "📋 订单管理: http://localhost:8080/admin"
echo "📊 收益报告: daily_report/reports/"
echo "🤖 优化引擎: python3 auto_optimizer.py --daily"
echo ""
echo "⏳ 启动中..."
cd "$(dirname "$0")"
nohup python3 delivery/order_server.py > /tmp/auto_biz.log 2>&1 &
sleep 2
echo "✅ 系统已启动！"
echo ""
echo "🌐 打开浏览器访问: http://localhost:8080"
open http://localhost:8080 2>/dev/null || true
