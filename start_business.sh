#!/bin/bash
# AutoTools 每日运营系统启动脚本
# 这个脚本在 launchd 中每天 09:00 执行

BASE="/Users/tianmengpiaoxiang/auto_business"
LOG="$BASE/daily_report/daily_run.log"

echo "===== $(date) =====" >> "$LOG"
echo "🚀 启动每日运营系统..." >> "$LOG"

# 1. 生成运营报告
echo "📊 生成每日报告..." >> "$LOG"
cd "$BASE" && python3 daily_report/reporter.py >> "$LOG" 2>&1

# 2. 检查服务器状态
echo "🔍 检查服务器状态..." >> "$LOG"
python3 -c "
import socket
s = socket.socket(); s.settimeout(5)
try:
    s.connect(('xiaoxiaojun.zeabur.app', 443))
    print('✅ Zeabur 服务器在线')
except:
    print('⚠️ Zeabur 服务器异常')
s.close()
" >> "$LOG" 2>&1

# 3. 检查待处理订单
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
            print(f'  {o[\"product_name\"]} - ¥{o[\"price\"]} - {o[\"buyer_email\"]}')
    else:
        print('✅ 无待处理订单')
" >> "$LOG" 2>&1

# 4. 收益分析
echo "💰 分析收益数据..." >> "$LOG"
cd "$BASE" && python3 revenue/tracker.py >> "$LOG" 2>&1

# 5. 汇总
echo "✅ 每日运营完成" >> "$LOG"
echo "" >> "$LOG"

# 显示最新报告
echo "📄 最新报告: $BASE/daily_report/reports/report_$(date +%Y-%m-%d).html"
