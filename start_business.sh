#!/bin/bash
# AutoTools 每日运营系统启动脚本
# 收益第一原则！每天自动检查、优化、增加收入

BASE="/Users/tianmengpiaoxiang/auto_business"
LOG="$BASE/daily_report/daily_run.log"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)

echo "" >> "$LOG"
echo "==========================================" >> "$LOG"
echo " 🚀 AutoTools 每日运营系统" >> "$LOG"
echo " 📅 $DATE $TIME" >> "$LOG"
echo "==========================================" >> "$LOG"

# === 1. 启动/检查本地服务器 ===
if ! pgrep -f "python3.*app.py" > /dev/null; then
    echo "🔧 启动本地服务器..." >> "$LOG"
    cd "$BASE" && python3 app.py &
    sleep 2
    echo "✅ 服务器已启动 (PID: $!)" >> "$LOG"
else
    echo "✅ 本地服务器运行中" >> "$LOG"
fi

# === 2. 生成运营报告 ===
echo "" >> "$LOG"
echo "📊 生成每日报告..." >> "$LOG"
cd "$BASE" && python3 daily_report/reporter.py >> "$LOG" 2>&1

# === 3. 收益分析 ===
echo "" >> "$LOG"
echo "💰 收益分析..." >> "$LOG"
cd "$BASE" && python3 revenue/tracker.py >> "$LOG" 2>&1

# === 4. 生成推广文案 ===
echo "" >> "$LOG"
echo "📢 生成推广文案..." >> "$LOG"
cd "$BASE" && python3 marketing/auto_publisher.py >> "$LOG" 2>&1

# === 5. 检查新工具开发 ===
echo "" >> "$LOG"
echo "🏭 检查工具开发流水线..." >> "$LOG"
cd "$BASE" && python3 -c "
import json
from pathlib import Path

# 检查已经开发了多少工具代码
code_files = list(Path('products').rglob('*.py'))
tool_files = [f for f in code_files if f.stem not in ('main', 'dev_pipeline', 'TOOL_TEMPLATE', '__init__')]
print(f'📦 已开发 {len(tool_files)} 个工具代码文件')

# 检查 products.json 中有多少产品
with open('products/products.json') as f:
    products = json.load(f)
print(f'📋 产品列表: {len(products)} 个')
print(f'💰 总价值: ¥{sum(p[\"price\"] for p in products)}')

# 检查收入情况
orders_file = Path('daily_report/data/orders.json')
if orders_file.exists():
    with open(orders_file) as f:
        data = json.load(f)
    print(f'💵 累计收入: ¥{data.get(\"total_revenue\", 0)}')
    print(f'📝 总订单: {len(data.get(\"orders\", []))}')
else:
    print('💵 暂无订单数据')
" >> "$LOG" 2>&1

# === 6. 检查 Zeabur 部署状态 ===
echo "" >> "$LOG"
echo "🌐 检查 Zeabur 部署..." >> "$LOG"
python3 -c "
import urllib.request
try:
    resp = urllib.request.urlopen('https://xiaxiaojun.com/api/products', timeout=10)
    data = resp.read().decode()
    import json
    products = json.loads(data)
    print(f'✅ Zeabur 在线 - {len(products.get(\"products\",[]))} 个产品')
except Exception as e:
    print(f'⚠️ Zeabur 检查失败: {e}')
" >> "$LOG" 2>&1

# === 7. 检查待处理订单 ===
echo "" >> "$LOG"
echo "📋 检查待处理订单..." >> "$LOG"
python3 -c "
import json
from pathlib import Path
f = Path('$BASE/daily_report/data/orders.json')
if f.exists():
    data = json.loads(f.read_text())
    pending = [o for o in data.get('orders',[]) if o.get('status')=='pending']
    if pending:
        print(f'⚠️ 有 {len(pending)} 笔待处理订单!')
        for o in pending:
            print(f'  🔴 {o[\"product_name\"]} - ¥{o[\"price\"]} - {o[\"buyer_email\"]} - {o.get(\"created_at\",\"\")}')
    else:
        print('✅ 无待处理订单')
        
    total = sum(o.get('price',0) for o in data.get('orders',[]))
    print(f'💰 累计收入: ¥{total}')
" >> "$LOG" 2>&1

# === 8. 每日目标检查 ===
echo "" >> "$LOG"
echo "🎯 每日目标检查..." >> "$LOG"
python3 -c "
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')
import json
from pathlib import Path
f = Path('$BASE/daily_report/data/orders.json')
if f.exists():
    data = json.loads(f.read_text())
    today_orders = [o for o in data.get('orders',[]) if o.get('created_at','').startswith(today)]
    today_rev = sum(o.get('price',0) for o in today_orders)
    print(f'📈 今日收入: ¥{today_rev} ({len(today_orders)}单)')
    goal = 100
    if today_rev >= goal:
        print(f'🎉 达成日目标! 达成率 {today_rev/goal*100:.0f}%')
    else:
        print(f'💪 还差 ¥{goal-today_rev} 达到日目标')
        print(f'💡 建议: 重点推广 VIP会员(¥199) 或 三件套(¥79)')
" >> "$LOG" 2>&1

# === 总结 ===
echo "" >> "$LOG"
echo "✅ 每日运营完成" >> "$LOG"
echo "==========================================" >> "$LOG"
echo "" >> "$LOG"

# 显示最新报告路径
echo "📄 最新报告: $BASE/daily_report/reports/report_$DATE.html"
echo "📊 收益看板: http://localhost:8000/admin/revenue"
echo "📋 管理后台: http://localhost:8000/admin"
echo "🌐 线上网站: https://xiaxiaojun.com"
