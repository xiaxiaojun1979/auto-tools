#!/bin/bash
echo "====== AutoTools 副业系统状态 ======"
echo ""
echo "📅 时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check local server
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 本地服务: 运行中 (http://localhost:8000)"
else
    echo "❌ 本地服务: 未运行"
fi

# Check online site
code=$(curl -s -o /dev/null -w "%{http_code}" https://xiaxiaojun.zeabur.app/health 2>/dev/null)
if [ "$code" = "200" ]; then
    echo "✅ 线上网站: 运行中 (https://xiaxiaojun.zeabur.app)"
else
    echo "⚠️ 线上网站: HTTP $code"
fi

# Check products
count=$(curl -s http://localhost:8000/api/products 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('total',d.get('products',[0])) if isinstance(d,list) else len(d.get('products',[])))" 2>/dev/null)
echo "📦 产品数量: ${count:-0}个"

# Check revenue today
today=$(date '+%Y-%m-%d')
rev=$(curl -s http://localhost:8000/api/stats 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    orders=d.get('orders',[])
    if not isinstance(orders,list) and isinstance(orders,dict):
        orders=orders.get('orders',[])
    today='$(date +%Y-%m-%d)'
    todays=[o for o in orders if o.get('created_at','').startswith(today)] if orders else []
    rev=sum(o.get('price',0) for o in todays)
    print(rev)
except:
    print(0)
" 2>/dev/null)
echo "💰 今日收益: ¥${rev:-0}"

# Check promo
echo ""
echo "🔥 当前推广活动:"
curl -s http://localhost:8000/api/promo/flash 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin).get('data', [])
    for item in data:
        print(f'  {item.get(\"emoji\",\"\")} {item.get(\"name\",\"\")} ¥{item.get(\"price\",0)} ({item.get(\"discount_pct\",0)}%OFF)')
except:
    print('  (暂无)')
" 2>/dev/null

# Check marketing
echo ""
echo "📢 推广统计:"
curl -s http://localhost:8000/api/promo/stats 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin).get('data', {})
    s = d.get('stats', {})
    print(f'  总推广次数: {s.get(\"total_promotions\", 0)}')
    print(f'  总点击: {s.get(\"total_clicks\", 0)}')
    print(f'  推广收入: ¥{s.get(\"promotion_revenue\", 0)}')
except:
    print('  (暂无数据)')
" 2>/dev/null

echo ""
echo "⏰ 定时任务:"
crontab -l 2>/dev/null | grep -v "^#" | while read line; do
    echo "  $line"
done

echo ""
echo "💡 快捷操作:"
echo "  启动服务: cd ~/auto_business && python3 app.py"
echo "  管理后台: http://localhost:8000/admin"
echo "  线上网站: https://xiaxiaojun.zeabur.app"
echo "  晚间工作流: python3 evening_workflow.py"
echo ""

# Check if running in background
ps aux | grep "python3 app.py" | grep -v grep > /dev/null && echo "🟢 后台进程运行中" || echo "🔴 后台进程未运行"
