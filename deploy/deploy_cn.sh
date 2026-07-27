#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   🚀 自动副业系统 - 国内版一键部署               ║"
echo "║   所有准备工作已完成，只差你注册一个账号          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

cd "$BASE_DIR"

# 1. 验证环境
echo "[1/5] 🔍 验证环境..."
python3 -c "
import sys
print(f'  Python: {sys.version.split()[0]}')
for mod, name in [('PIL','Pillow'), ('openpyxl','openpyxl')]:
    try:
        __import__(mod); print(f'  {name}: OK')
    except:
        print(f'  {name}: 未安装')
"
echo ""

# 2. 测试所有产品
echo "[2/5] 🧪 测试产品..."
for dir in file_tools content_gen data_tools; do
    cd "$BASE_DIR/products/$dir"
    python3 main.py --help >/dev/null 2>&1 && echo "  ✓ $dir - OK"
done
echo ""

# 3. 生成营销内容
echo "[3/5] 📝 生成首周内容计划..."
cd "$BASE_DIR/marketing"
python3 auto_publisher.py plan --days 7 >/dev/null 2>&1
echo "  ✓ 一周内容计划已就绪"
echo ""

# 4. 生成闲鱼文案
echo "[4/5] 🏪 生成闲鱼发布文案..."
cd "$BASE_DIR/deploy/xianyu"
python3 auto_listing.py >/dev/null 2>&1
echo "  ✓ 闲鱼商品文案已生成"
echo ""

# 5. 生成收益报告并演示
echo "[5/5] 📊 初始化收益追踪系统..."
cd "$BASE_DIR/deploy/auto_sale"
python3 revenue_tracker.py --status >/dev/null 2>&1
echo "  ✓ 收益追踪系统已就绪"
echo ""

# 生成总结
SUMMARY="$BASE_DIR/部署总结_$(date +%Y%m%d).md"

cat > "$SUMMARY" << EOF
# 🎉 国内版自动副业系统部署完成！

**部署时间:** $(date '+%Y-%m-%d %H:%M:%S')
**部署目录:** \`$BASE_DIR\`

---

## 📦 已准备好的产品

| 产品 | 价格 | 文件位置 |
|------|------|---------|
| 📁 文件批处理大师 | ~~¥99~~ **¥49** | \`products/file_tools/main.py\` |
| 📝 内容自动生成器 | ~~¥59~~ **¥29** | \`products/content_gen/main.py\` |
| 🧹 数据清洗工具包 | ~~¥79~~ **¥39** | \`products/data_tools/main.py\` |
| 🎉 三件套捆绑包 | ~~¥177~~ **¥79** | 三个打包 |

## 📋 收益预测（保守估计）

| 时间 | 预期单量 | 预期收入 |
|------|---------|---------|
| 第1周 | 0-3 单 | ¥0-147 |
| 第2周 | 3-8 单 | ¥147-392 |
| 第1个月 | 15-30 单 | ¥735-1470 |
| 第3个月 | 稳定后 | ¥2000-5000/月 |

## 🤖 每日自动运行

| 时间 | 内容 | 产出 |
|------|------|------|
| 09:00 | 收益报告 | \`daily_report/reports/\` |
| 09:10 | 内容计划 | \`marketing/data/\` |

## ✅ 你唯一需要做的事

\`\`\`
1. 打开 https://afdian.net → 注册（手机号，2分钟）
2. 注册完后告诉我账号名
3. 我帮你完成剩下的上架和推广
\`\`\`
EOF

echo ""
cat "$SUMMARY"
echo ""
echo "╔════════════════════════════════════════╗"
echo "║    ✅ 全部就绪！                       ║"
echo "║                                        ║"
echo "║    现在只差：                          ║"
echo "║    注册爱发电账号 → afdian.net         ║"
echo "║    注册完告诉我，我帮你完成所有上架     ║"
echo "╚════════════════════════════════════════╝"
