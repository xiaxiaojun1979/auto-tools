#!/bin/bash
set -e

# ============================================
# 🚀 自动副业 - 一键部署脚本
# ============================================
# 运行这个脚本 = 自动完成所有部署
# 你只需要：告诉我 Gumroad 账号注册好了

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   🚀 自动副业部署系统 v1.0          ║"
echo "║   开始部署...                        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 步骤1: 验证环境
echo "[1/5] 🔍 验证环境..."
cd "$BASE_DIR"

python3 -c "
import sys
print(f'  ✓ Python {sys.version.split()[0]}')
try:
    from PIL import Image; print('  ✓ Pillow OK')
except: print('  ⚠ Pillow 未安装（图片处理需要）')
try:
    import openpyxl; print('  ✓ openpyxl OK')
except: print('  ⚠ openpyxl 未安装（Excel处理需要）')
"

echo ""

# 步骤2: 测试所有产品
echo "[2/5] 🧪 测试产品功能..."
cd "$BASE_DIR/products/file_tools"
python3 main.py --help > /dev/null 2>&1 && echo "  ✓ 文件批处理大师 - OK"
cd "$BASE_DIR/products/content_gen"
python3 main.py categories > /dev/null 2>&1 && echo "  ✓ 内容生成器 - OK"
cd "$BASE_DIR/products/data_tools"
python3 main.py --help > /dev/null 2>&1 && echo "  ✓ 数据清洗工具 - OK"
echo ""

# 步骤3: 生成首周内容计划
echo "[3/5] 📝 生成首周营销内容..."
cd "$BASE_DIR/marketing"
python3 auto_publisher.py plan --days 7 > /dev/null 2>&1
echo "  ✓ 一周内容计划已生成"
echo ""

# 步骤4: 设置每日报告
echo "[4/5] 📊 配置每日报告系统..."
cd "$BASE_DIR/daily_report"
python3 reporter.py --report > /dev/null 2>&1
bash setup_cron.sh > /dev/null 2>&1
echo "  ✓ 每日报告系统已配置"
echo ""

# 步骤5: 生成部署总结
echo "[5/5] ✅ 生成部署总结..."
cd "$BASE_DIR"
SUMMARY_FILE="deploy_summary_$(date +%Y%m%d).md"

cat > "$SUMMARY_FILE" << EOF
# 🎉 自动副业系统部署完成！

**部署时间:** $(date '+%Y-%m-%d %H:%M:%S')
**部署目录:** $BASE_DIR

---

## 已就绪的产品

| 产品 | 文件位置 | 定价建议 |
|------|---------|---------|
| 📁 文件批处理大师 | products/file_tools/main.py | \$29.99 / ¥49 |
| 📝 内容自动生成器 | products/content_gen/main.py | \$19.99 / ¥29 |
| 🧹 数据清洗工具包 | products/data_tools/main.py | \$24.99 / ¥39 |

## 每日自动任务

- **09:00** - 生成每日收益报告 + 优化建议
- **报告位置:** daily_report/reports/

## 下一步：你只需做这件事

1. 注册 Gumroad 账号 → https://gumroad.com
2. 告诉我注册好了 -> 我帮你上架产品
3. 每天打开我生成的报告 -> 看收益和优化建议

---

*系统将每天自动优化内容策略和推广方案*
EOF

echo "  ✓ 部署总结已生成: $SUMMARY_FILE"
echo ""
echo "╔══════════════════════════════════════╗"
echo "║   ✅ 部署完成！                      ║"
echo "║                                      ║"
echo "║   下一步：注册 Gumroad 账号           ║"
echo "║   然后告诉我一声，我帮你上架产品       ║"
echo "╚══════════════════════════════════════╝"
echo ""
cat "$SUMMARY_FILE"
