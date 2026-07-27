#!/bin/bash
# AutoTools 副业系统 - 状态查看和控制脚本
# 用法: bash status.sh [url|status|restart|stop|admin]

source /Users/tianmengpiaoxiang/auto_business/.env 2>/dev/null

show_status() {
    echo ""
    echo "============================================"
    echo "  🚀 AutoTools 副业系统 - 状态报告"
    echo "============================================"
    echo ""
    
    # 检查本地服务器
    if curl -s --max-time 3 http://127.0.0.1:8080 > /dev/null 2>&1; then
        echo "  ✅ 本地服务器: 运行中"
    else
        echo "  ❌ 本地服务器: 未运行"
    fi
    
    # 检查隧道
    TUNNEL_URL=$(cat /tmp/auto_tunnel_url.txt 2>/dev/null || echo "")
    if [ -n "$TUNNEL_URL" ]; then
        echo "  ✅ 公网隧道: 活跃"
        echo "  🌐 网站地址: $TUNNEL_URL"
        echo "  📋 管理后台: $TUNNEL_URL/admin"
    else
        if ps aux | grep -q "nokey@localhost.run"; then
            echo "  ⏳ 公网隧道: 连接中..."
        else
            echo "  ❌ 公网隧道: 未连接"
        fi
    fi
    
    echo ""
    echo "  📊 收益统计:"
    cd /Users/tianmengpiaoxiang/auto_business
    python3 auto_optimizer.py --status 2>/dev/null | tail -8
    
    echo ""
    echo "  ⚙️ 系统服务:"
    launchctl list | grep "com.auto" | while read pid code label; do
        if [ "$pid" = "-" ]; then
            echo "    ❌ $label (已停止，代码: $code)"
        else
            echo "    ✅ $label (PID: $pid)"
        fi
    done
    
    echo ""
    echo "============================================"
    echo "  收款方式:"
    echo "  💙 支付宝: 15156215580"
    echo "  💚 微信: 扫描网站上的收款码"
    echo "============================================"
    echo ""
}

case "${1:-status}" in
    url)
        URL=$(cat /tmp/auto_tunnel_url.txt 2>/dev/null || echo "获取中...")
        echo $URL
        if [ "$URL" != "获取中..." ] && [ -n "$URL" ]; then
            echo "📋 后台: $URL/admin"
        fi
        ;;
    status)
        show_status
        ;;
    restart)
        echo "重新启动系统..."
        launchctl unload ~/Library/LaunchAgents/com.auto.tunnel.plist 2>/dev/null
        launchctl unload ~/Library/LaunchAgents/com.auto.order-server.plist 2>/dev/null
        sleep 2
        launchctl load ~/Library/LaunchAgents/com.auto.order-server.plist
        launchctl load ~/Library/LaunchAgents/com.auto.tunnel.plist
        echo "✅ 系统已重启"
        sleep 3
        bash "$0" url
        ;;
    stop)
        echo "🛑 停止系统..."
        launchctl unload ~/Library/LaunchAgents/com.auto.tunnel.plist 2>/dev/null
        launchctl unload ~/Library/LaunchAgents/com.auto.order-server.plist 2>/dev/null
        echo "✅ 系统已停止"
        ;;
    admin)
        URL=$(cat /tmp/auto_tunnel_url.txt 2>/dev/null || echo "")
        if [ -n "$URL" ]; then
            echo "📋 管理后台: $URL/admin"
            echo ""
            echo "访问上述地址即可查看和管理订单。"
            echo "当收到买家付款通知后，去后台确认即可。"
        else
            echo "⏳ 隧道尚未建立，请稍候..."
        fi
        ;;
    *)
        echo "用法: bash status.sh [url|status|restart|stop|admin]"
        ;;
esac
