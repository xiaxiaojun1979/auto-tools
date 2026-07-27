#!/bin/bash
# 设置每日自动报告
REPORTER_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_JOB="0 9 * * * cd $REPORTER_DIR && python3 reporter.py --auto >> $REPORTER_DIR/cron.log 2>&1"

# 检查是否已有这个cron任务
(crontab -l 2>/dev/null | grep -v "reporter.py") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "[✓] 每日报告定时任务已设置"
echo "    每天早上9:00自动运行"
echo "    日志: $REPORTER_DIR/cron.log"
