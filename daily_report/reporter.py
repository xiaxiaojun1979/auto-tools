#!/usr/bin/env python3
"""
每日收益报告系统 - Daily Revenue Reporter
每天自动生成收益报告 + 优化建议
"""

import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
import random
import subprocess


class DailyReporter:
    """每日报告生成器"""

    def __init__(self):
        self.report_dir = Path(__file__).parent / "reports"
        self.report_dir.mkdir(exist_ok=True)
        self.data_dir = Path(__file__).parent.parent / "marketing" / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 收益数据（等你关联Gumroad后自动读取）
        self.revenue_file = self.data_dir / "revenue_log.json"
        self._init_revenue_log()

    def _init_revenue_log(self):
        if not self.revenue_file.exists():
            with open(self.revenue_file, 'w', encoding='utf-8') as f:
                json.dump({"daily_logs": [], "total_revenue": 0, "total_sales": 0}, f, ensure_ascii=False, indent=2)

    def _load_revenue(self):
        with open(self.revenue_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_revenue(self, data):
        with open(self.revenue_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record_sale(self, amount, product_name, source="gumroad"):
        """记录一笔收入"""
        data = self._load_revenue()
        today = datetime.now().strftime("%Y-%m-%d")

        # 查找今天的记录
        today_log = None
        for log in data["daily_logs"]:
            if log["date"] == today:
                today_log = log
                break

        if not today_log:
            today_log = {"date": today, "sales": [], "total": 0}
            data["daily_logs"].append(today_log)

        today_log["sales"].append({
            "time": datetime.now().strftime("%H:%M"),
            "product": product_name,
            "amount": amount,
            "source": source
        })
        today_log["total"] += amount
        data["total_revenue"] += amount
        data["total_sales"] += 1
        self._save_revenue(data)
        print(f"[💰] 记录收入: ¥{amount} - {product_name}")

    def generate_report(self):
        """生成今日报告"""
        data = self._load_revenue()
        today = datetime.now().strftime("%Y-%m-%d")
        today_name = datetime.now().strftime("%Y年%m月%d日")

        # 今日数据
        today_log = None
        for log in data["daily_logs"]:
            if log["date"] == today:
                today_log = log
                break

        # 昨日数据
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_log = None
        for log in data["daily_logs"]:
            if log["date"] == yesterday:
                yesterday_log = log
                break

        # 本周数据
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        week_data = [l for l in data["daily_logs"] if l["date"] >= week_start]

        # ====== 生成报告 ======
        today_total = today_log["total"] if today_log else 0
        yesterday_total = yesterday_log["total"] if yesterday_log else 0
        week_total = sum(l["total"] for l in week_data)
        total_revenue = data["total_revenue"]
        total_sales = data["total_sales"]

        # 趋势
        trend = "📈 上升" if today_total > yesterday_total else "📉 下降" if today_total < yesterday_total else "➡️ 持平"
        change = today_total - yesterday_total

        # 热门产品
        product_sales = {}
        for log in data["daily_logs"]:
            for sale in log["sales"]:
                p = sale["product"]
                product_sales[p] = product_sales.get(p, 0) + sale["amount"]

        top_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:3]

        # 优化建议
        suggestions = self._generate_suggestions(data)

        report = f"""
╔══════════════════════════════════════════════════╗
║           📊 每日收益报告                        ║
║           {today_name}                        ║
╚══════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 今日收入: ¥{today_total:.2f}
📈 对比昨日: {trend} (¥{change:+.2f})
📊 本周累计: ¥{week_total:.2f}
🏆 历史总计: ¥{total_revenue:.2f} ({total_sales} 笔)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 热销产品 TOP 3:"""
        for i, (p, amt) in enumerate(top_products, 1):
            report += f"\n   {i}. {p} - ¥{amt:.2f}"

        report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 今日优化建议:
"""
        for s in suggestions:
            report += f"  ✅ {s}\n"

        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 明日待办:
  □ 检查 Gumroad 销售数据
  □ 生成一批新帖子内容
  □ 查看用户反馈，优化产品描述
  □ 考虑发布新产品或更新现有产品

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        # 保存报告
        report_path = self.report_dir / f"report_{today}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        # 也保存一份 HTML 版本
        html_report = report.replace('\n', '<br>\n')
        html_path = self.report_dir / f"report_{today}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(f"<html><body style='font-family:monospace;'>{html_report}</body></html>")

        print(f"\n{'='*50}")
        print(report)
        print(f"[✓] 报告已保存: {report_path}")

        return report

    def generate_weekly_review(self):
        """生成本周回顾"""
        data = self._load_revenue()

        # 过去7天
        week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_data = [l for l in data["daily_logs"] if l["date"] >= week_start]

        if not week_data:
            print("[!] 本周暂无数据")
            return

        total = sum(l["total"] for l in week_data)
        sales_count = sum(len(l["sales"]) for l in week_data)
        avg_per_day = total / len(week_data)

        print(f"\n{'='*50}")
        print(f"  📅 本周回顾 ({week_start} ~ {datetime.now().strftime('%Y-%m-%d')})")
        print(f"{'='*50}")
        print(f"  总收入: ¥{total:.2f}")
        print(f"  总单数: {sales_count}")
        print(f"  日均: ¥{avg_per_day:.2f}")

        # 每日趋势
        print(f"\n  每日趋势:")
        for log in sorted(week_data, key=lambda x: x["date"]):
            bar = "█" * int(log["total"] / (total / len(week_data)) * 20) if total > 0 else ""
            print(f"    {log['date']}: ¥{log['total']:<8.2f} {bar}")

        print(f"{'='*50}")

    def _generate_suggestions(self, data):
        """生成优化建议"""
        suggestions = []

        total_sales = data["total_sales"]
        total_revenue = data["total_revenue"]

        if total_sales == 0:
            suggestions.extend([
                "还没有销售记录，检查Gumroad产品是否已发布",
                "生成10条推广帖子，发布到小红书/朋友圈",
                "优化产品描述，突出能解决的具体问题",
                "考虑在闲鱼上同步发布链接"
            ])
        elif total_sales < 5:
            suggestions.extend([
                f"已有 {total_sales} 单成交，继续保持！",
                "检查用户评价，看是否有改进空间",
                "增加推广渠道，尝试多平台分发",
                "考虑推出限时折扣或捆绑包"
            ])
        else:
            suggestions.extend([
                f"累计 {total_sales} 单，¥{total_revenue:.2f}，趋势良好！",
                "分析哪些产品卖得最好，加大推广力度",
                "开发新产品线，复用成功模式",
                "考虑提价测试需求弹性",
                "建立客户邮件列表，做复购"
            ])

        # 随机补充建议
        extra = [
            "尝试A/B测试不同的产品标题和描述",
            "关注竞品定价，保持竞争力",
            "在知乎/小红书发布使用教程引流",
            "把用户常见问题整理成FAQ，减少咨询",
            "制作短视频展示工具使用效果"
        ]
        if len(suggestions) < 4:
            suggestions.append(random.choice(extra))

        return suggestions[:5]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="📊 每日收益报告系统")
    parser.add_argument("--record", nargs=3, metavar=("AMOUNT", "PRODUCT", "SOURCE"),
                        help="记录一笔收入: 金额 产品名 来源")
    parser.add_argument("--report", action="store_true", help="生成今日报告")
    parser.add_argument("--weekly", action="store_true", help="生成周报")
    parser.add_argument("--auto", action="store_true", help="自动模式：报告 + 营销计划")

    args = parser.parse_args()
    reporter = DailyReporter()

    if args.record:
        amount, product, source = args.record
        reporter.record_sale(float(amount), product, source)

    if args.report or args.auto:
        reporter.generate_report()

    if args.weekly:
        reporter.generate_weekly_review()

    if args.auto:
        # 同时生成下周营销计划
        print("\n[🔄] 自动生成下周营销计划...")
        mkt_path = Path(__file__).parent.parent / "marketing" / "auto_publisher.py"
        subprocess.run(["python3", str(mkt_path), "plan", "--days", "7"])

    if not any([args.record, args.report, args.weekly, args.auto]):
        parser.print_help()


if __name__ == "__main__":
    main()
