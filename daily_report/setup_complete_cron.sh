#!/bin/bash
# ============================================
# AutoTools 完整定时任务设置
# 收益第一原则！
# ============================================

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$BASE_DIR/daily_report"
DATA_DIR="$LOG_DIR/data"

mkdir -p "$DATA_DIR"

# 备份现有cron
crontab -l > /tmp/cron_backup_$(date +%Y%m%d).txt 2>/dev/null

# 清除旧的AutoTools相关cron
(crontab -l 2>/dev/null | grep -v -E "(reporter\.py|evening_workflow\.py|xianyu_daily_ops\.py|system_maintenance\.py)") | crontab -

# 添加新的cron任务
(
crontab -l 2>/dev/null
echo ""
echo "# === AutoTools 自动化系统 ==="
echo "# 每天早上9:00 - 发送运营报告"
echo "0 9 * * * cd $BASE_DIR && python3 daily_report/reporter.py --auto >> $LOG_DIR/cron.log 2>&1"
echo ""
echo "# 每天晚上20:00 - 热门分析+新工具开发+平台发布+邮件报告"
echo "0 20 * * * cd $BASE_DIR && python3 evening_workflow.py >> $LOG_DIR/evening_cron.log 2>&1"
echo ""
echo "# 每2小时 - 系统维护检查"
echo "0 */2 * * * cd $BASE_DIR && python3 system_maintenance.py >> $LOG_DIR/maintenance_cron.log 2>&1"
echo ""
echo "# 每天早上8:00 - 闲鱼商品擦亮+消息检查"
echo "0 8 * * * cd $BASE_DIR && python3 xianyu_daily_ops.py maintenance >> $LOG_DIR/xianyu_cron.log 2>&1"
echo ""
echo "# 每天中午12:00 - 闲鱼商品擦亮"
echo "0 12 * * * cd $BASE_DIR && python3 xianyu_daily_ops.py maintenance >> $LOG_DIR/xianyu_cron.log 2>&1"
echo ""
echo "# 每天晚上22:00 - 闲鱼商品擦亮"
echo "0 22 * * * cd $BASE_DIR && python3 xianyu_daily_ops.py maintenance >> $LOG_DIR/xianyu_cron.log 2>&1"
echo ""
echo "# 每天凌晨3:00 - 生成推广内容"
echo "0 3 * * * cd $BASE_DIR && python3 promotion_engine.py >> $LOG_DIR/promotion_cron.log 2>&1"
echo ""
echo "# 每30分钟 - 检查本地服务器是否运行"
echo "*/30 * * * * cd $BASE_DIR && (pgrep -f 'python3.*app.py' > /dev/null || (python3 app.py >> /tmp/autotools_server.log 2>&1 &))"
) | crontab -

echo ""
echo "============================================"
echo " ✅ AutoTools 完整定时任务已设置"
echo "============================================"
echo ""
echo " 📅 每天早上 9:00  - 运营报告"
echo " 📅 每天晚上 20:00 - 热门分析+开发+发布+邮件"
echo " 📅 每 2 小时     - 系统维护"
echo " 📅 每天 8/12/22 点 - 闲鱼商品擦亮"
echo " 📅 每天凌晨 3:00  - 生成推广内容"
echo " 📅 每 30 分钟    - 服务器保活"
echo ""
echo " 📧 报告发送到: 35538112@qq.com"
echo ""
echo "日志位置:"
echo "   $LOG_DIR/cron.log"
echo "   $LOG_DIR/evening_cron.log"
echo "   $LOG_DIR/maintenance_cron.log"
echo "   $LOG_DIR/xianyu_cron.log"
echo "============================================"

# 显示当前cron
echo ""
echo "当前定时任务列表:"
crontab -l
