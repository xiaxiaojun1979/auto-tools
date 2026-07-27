#!/usr/bin/env python3
"""
国内版收益追踪器
记录支付宝/微信渠道的每一笔收入，自动生成报告和优化建议
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import random

class RevenueTracker:
    """收益追踪器"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / "daily_report" / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir = Path(__file__).parent.parent.parent / "daily_report" / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_dir / "revenue_cn.json"
        self._init_db()

    def _init_db(self):
        if not self.db_file.exists():
            default = {
                "total_revenue": 0,
                "total_sales": 0,
                "daily_logs": [],
                "platforms": {
                    "爱发电": {"enabled": True, "revenue": 0, "sales": 0},
                    "闲鱼": {"enabled": True, "revenue": 0, "sales": 0},
                    "微信直售": {"enabled": True, "revenue": 0, "sales": 0}
                },
                "products": {
                    "文件批处理大师": {"price": 49, "sales": 0, "revenue": 0},
                    "内容自动生成器": {"price": 29, "sales": 0, "revenue": 0},
                    "数据清洗工具包": {"price": 39, "sales": 0, "revenue": 0},
                    "三件套捆绑包": {"price": 79, "sales": 0, "revenue": 0}
                }
            }
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(default, f, ensure_ascii=False, indent=2)

    def record_sale(self, amount, product, platform="爱发电"):
        """记录一笔收入"""
        with open(self.db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        today = datetime.now().strftime("%Y-%m-%d")
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
            "product": product,
            "amount": amount,
            "platform": platform
        })
        today_log["total"] += amount
        data["total_revenue"] += amount
        data["total_sales"] += 1

        # 更新产品统计
        if product in data["products"]:
            data["products"][product]["sales"] += 1
            data["products"][product]["revenue"] += amount

        # 更新平台统计
        if platform in data["platforms"]:
            data["platforms"][platform]["revenue"] += amount
            data["platforms"][platform]["sales"] += 1

        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[💰] 记录收入: ¥{amount:.2f} - {product}（来自{platform}）")

    def generate_report(self):
        """生成中文收益报告"""
        with open(self.db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        today = datetime.now().strftime("%Y-%m-%d")
        today_name = datetime.now().strftime("%Y年%m月%d日")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # 今日数据
        today_log = None
        for log in data["daily_logs"]:
            if log["date"] == today:
                today_log = log
                break

        # 昨日数据
        yesterday_log = None
        for log in data["daily_logs"]:
            if log["date"] == yesterday:
                yesterday_log = log
                break

        today_total = today_log["total"] if today_log else 0
        yesterday_total = yesterday_log["total"] if yesterday_log else 0

        # 本周数据
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
        week_data = [l for l in data["daily_logs"] if l["date"] >= week_start]
        week_total = sum(l["total"] for l in week_data)

        # 趋势
        change = today_total - yesterday_total
        if today_total > yesterday_total:
            trend = "📈 上升"
            trend_icon = "🔥"
        elif today_total < yesterday_total:
            trend = "📉 下降"
            trend_icon = "💪"
        else:
            trend = "➡️ 持平"
            trend_icon = ""

        # 产品排名
        products_sorted = sorted(data["products"].items(), key=lambda x: x[1]["revenue"], reverse=True)

        # 平台统计
        platforms_active = {k: v for k, v in data["platforms"].items() if v["enabled"]}

        # 优化建议
        suggestions = self._generate_suggestions(data)

        report = f"""
╔══════════════════════════════════════════════════╗
║           📊 每日收益报告（¥ CNY）               ║
║           {today_name}                        ║
╚══════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 今日收入：¥{today_total:.2f}
📈 对比昨日：{trend}（¥{change:+.2f}）{trend_icon}
📊 本周累计：¥{week_total:.2f} | {sum(l['total'] for l in week_data) / max(len(week_data),1):.0f}/天
🏆 历史总计：¥{data['total_revenue']:.2f}（共{data['total_sales']}单）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 产品收益排名："""
        for i, (name, info) in enumerate(products_sorted, 1):
            bar = "█" * max(1, int(info["revenue"] / max(data["total_revenue"], 1) * 15))
            report += f"\n  {i}. {name:<10} ¥{info['revenue']:<6.0f} {info['sales']}单 {bar}"

        report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 各渠道收入："""
        for name, info in platforms_active.items():
            report += f"\n  • {name}：¥{info['revenue']:.2f}（{info['sales']}单）"

        report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 今日优化建议："""
        for s in suggestions:
            report += f"\n  ✅ {s}"

        report += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 明日待办：
  □ 检查各平台是否有新订单需要处理
  □ 用内容生成器产出一批新帖子
  □ 查看用户反馈，优化产品
  □ 考虑发布新产品或更新现有产品

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 小提示：每天花15分钟回复评论和私信，
   能显著提升转化率！
"""

        report_path = self.report_dir / f"收益报告_{today}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(report)
        print(f"[✓] 报告已保存: {report_path}")
        return report

    def _generate_suggestions(self, data):
        """生成优化建议"""
        suggestions = []

        if data["total_sales"] == 0:
            suggestions += [
                "还没有开张！今天重点行动：",
                "① 在爱发电上架产品（注册账号后告诉我）",
                "② 在闲鱼发布至少2个商品",
                "③ 发一条小红书/朋友圈介绍工具",
                "④ 定价先用¥29-49的低价策略破零"
            ]
        elif data["total_sales"] < 10:
            suggestions += [
                f"已有{data['total_sales']}单！继续加油！",
                "分析一下买家最常问的问题，更新到产品描述里",
                "把卖得最好的产品做个限时折扣",
                "在知乎上回答相关问题时植入产品",
                "考虑建一个用户群，做复购"
            ]
        else:
            suggestions += [
                f"累计{data['total_sales']}单，¥{data['total_revenue']:.0f}，非常棒！",
                "分析复购率，考虑推出高级版/Pro版",
                "收集用户反馈，迭代产品功能",
                "尝试涨价5-10元测试需求弹性",
                "开发新产品线，复用已有的推广渠道"
            ]

        # 按星期几给特殊建议
        weekday = datetime.now().weekday()
        weekly_tips = {
            0: "周一适合发干货/教程类内容",
            1: "周二可以发用户好评截图做信任背书",
            2: "周中适合发产品对比/测评",
            3: "周四发限时优惠，促进周末转化",
            4: "周五发轻松/好用工具推荐",
            5: "周末流量高，多发帖子",
            6: "周日做一周复盘，规划下周内容"
        }
        suggestions.append(f"📅 {weekly_tips.get(weekday, '保持日常更新')}")

        return suggestions[:6]

    def show_products_status(self):
        """显示各产品状态"""
        with open(self.db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n📦 产品状态一览：")
        print(f"{'产品名称':<16} {'价格':<8} {'销量':<8} {'收入':<10} {'上架状态'}")
        print("-"*60)
        for name, info in data["products"].items():
            status = "✅ 可上架" if info["sales"] == 0 else "🟢 已开单"
            print(f"{name:<16} ¥{info['price']:<5} {info['sales']:<8} ¥{info['revenue']:<8.0f} {status}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="📊 国内版收益追踪器")
    parser.add_argument("--record", nargs=3, metavar=("金额", "产品", "平台"),
                        help="记录一笔收入")
    parser.add_argument("--report", action="store_true", help="生成收益报告")
    parser.add_argument("--status", action="store_true", help="查看产品状态")
    parser.add_argument("--demo", action="store_true", help="模拟一条收入演示效果")

    args = parser.parse_args()
    tracker = RevenueTracker()

    if args.record:
        amount, product, platform = args.record
        tracker.record_sale(float(amount), product, platform)

    if args.report:
        tracker.generate_report()

    if args.status:
        tracker.show_products_status()

    if args.demo:
        print("\n[🎬] 模拟收入记录演示...")
        tracker.record_sale(49, "文件批处理大师", "爱发电")
        tracker.record_sale(79, "三件套捆绑包", "微信直售")
        print()
        tracker.generate_report()

    if not any([args.record, args.report, args.status, args.demo]):
        parser.print_help()


if __name__ == "__main__":
    main()
