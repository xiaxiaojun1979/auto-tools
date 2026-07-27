#!/usr/bin/env python3
"""
🤖 自动优化引擎 - 每天自动运行，优化副业收益
Auto Optimization Engine - Daily Revenue Optimization
"""

import json
import smtplib
import ssl
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime, timedelta
import random
import subprocess
import sys

BASE_DIR = Path(__file__).parent

class AutoOptimizer:
    """自动优化引擎"""

    def __init__(self):
        self.report_dir = BASE_DIR / "daily_report" / "reports"
        self.report_dir.mkdir(exist_ok=True)
        self.data_dir = BASE_DIR / "daily_report" / "data"
        self.data_dir.mkdir(exist_ok=True)

    def load_orders(self):
        """加载订单数据"""
        orders_file = self.data_dir / "orders.json"
        if not orders_file.exists():
            return {"orders": [], "total_revenue": 0}
        with open(orders_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_performance(self):
        """分析当前业绩"""
        data = self.load_orders()
        orders = data["orders"]
        total_revenue = data["total_revenue"]

        # 本周订单
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_orders = [o for o in orders if o["created_at"] >= week_start.strftime("%Y-%m-%d")]
        
        # 本月订单
        month_start = datetime.now().replace(day=1)
        month_orders = [o for o in orders if o["created_at"] >= month_start.strftime("%Y-%m-%d")]

        # 产品销量统计
        product_sales = {}
        for o in orders:
            p = o["product"]
            if p not in product_sales:
                product_sales[p] = {"count": 0, "revenue": 0}
            product_sales[p]["count"] += 1
            product_sales[p]["revenue"] += o["price"]

        return {
            "total_orders": len(orders),
            "total_revenue": total_revenue,
            "week_orders": len(week_orders),
            "week_revenue": sum(o["price"] for o in week_orders),
            "month_orders": len(month_orders),
            "month_revenue": sum(o["price"] for o in month_orders),
            "product_sales": product_sales,
            "pending_orders": [o for o in orders if o["status"] == "pending"]
        }

    def generate_today_tasks(self, analysis):
        """根据分析生成今日待办"""
        tasks = []
        
        # 待处理订单
        pending = analysis["pending_orders"]
        if pending:
            tasks.append(f"📋 待确认收款 {len(pending)} 单，请访问 /admin 处理")
        
        # 根据销量生成任务
        if analysis["total_orders"] == 0:
            tasks.append("📢 还没有订单！去闲鱼/朋友圈发布推广信息")
            tasks.append("✍️ 生成一批新帖子，今日至少发2条")
            tasks.append("💡 检查产品定价是否合理，考虑限时折扣")
        elif analysis["total_orders"] < 5:
            tasks.append(f"🎉 已有 {analysis['total_orders']} 单！继续加大推广")
            tasks.append("📝 分析买家来源，重点投入效果好的渠道")
        else:
            tasks.append(f"🔥 累计 {analysis['total_orders']} 单，¥{analysis['total_revenue']:.0f}，继续保持！")
            tasks.append("📊 检查哪款产品最好卖，考虑推出Pro版")
        
        # 每日固定任务
        tasks.append("🔄 检查订单管理后台，确认到账情况")
        tasks.append("📊 查看今日收益报告")
        
        return tasks

    def generate_optimization_report(self):
        """生成完整优化报告"""
        analysis = self.analyze_performance()
        today = datetime.now().strftime("%Y-%m-%d")
        today_cn = datetime.now().strftime("%Y年%m月%d日")
        
        # 产品排名
        products_sorted = sorted(
            analysis["product_sales"].items(),
            key=lambda x: x[1]["revenue"],
            reverse=True
        )
        
        # 待处理
        pending = analysis["pending_orders"]
        
        # 每日建议
        tips_pool = [
            "在知乎搜索相关问题时植入你的产品链接",
            "把用户的常见问题整理成FAQ，减少咨询成本",
            "录一个2分钟的产品使用视频，发到视频号/B站",
            "整理用户好评截图，做成信任背书发朋友圈",
            "给已购用户发邮件，请求评价和推荐",
            "尝试在不同时段发帖，找出流量最好的时间",
            "关注竞品动态，调整自己的卖点描述",
            "把产品案例做成小红书图文笔记",
            "建立潜在客户微信群，定期分享干货",
            "在豆瓣相关小组分享使用经验",
            "制作产品对比图，突出你的优势",
            "写一篇3000字的工具使用教程（长尾SEO）"
        ]
        
        daily_tip = random.choice(tips_pool)
        
        # 今日任务
        tasks = self.generate_today_tasks(analysis)
        
        report = f"""╔══════════════════════════════════════════════════╗
║         🤖 自动副业优化报告                      ║
║         {today_cn}                         ║
╚══════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 业绩概览
───────────────────────────────
  • 累计订单: {analysis['total_orders']} 单
  • 累计收入: ¥{analysis['total_revenue']:.0f}
  • 本周订单: {analysis['week_orders']} 单
  • 本周收入: ¥{analysis['week_revenue']:.0f}
  • 本月订单: {analysis['month_orders']} 单
  • 本月收入: ¥{analysis['month_revenue']:.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 产品销售排名
───────────────────────────────
"""
        for i, (name, info) in enumerate(products_sorted, 1):
            report += f"  {i}. {name} - {info['count']}单 / ¥{info['revenue']:.0f}\n"
        
        if not products_sorted:
            report += "  （暂无销售数据）\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 待处理订单
───────────────────────────────
"""
        if pending:
            for o in pending:
                report += f"  ⏳ {o['product']} - ¥{o['price']} - {o['buyer_email']}\n"
        else:
            report += "  ✅ 暂无待处理订单\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 今日待办
───────────────────────────────
"""
        for t in tasks:
            report += f"  □ {t}\n"
        
        report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 今日优化建议
───────────────────────────────
  ✅ {daily_tip}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔗 快捷入口
───────────────────────────────
  • 产品网站: http://localhost:8080
  • 订单管理: http://localhost:8080/admin
  • 收益报告: {self.report_dir}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # 保存报告
        report_path = self.report_dir / f"优化报告_{today}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(report)
        print(f"[✓] 优化报告已保存: {report_path}")
        
        return report

    def run_daily(self):
        """每日自动运行"""
        print(f"\n{'='*50}")
        print(f"  🤖 自动优化引擎启动 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*50}")
        
        # 1. 生成优化报告
        self.generate_optimization_report()
        
        # 2. 检查待处理订单
        analysis = self.analyze_performance()
        if analysis["pending_orders"]:
            print(f"\n⚠️  有 {len(analysis['pending_orders'])} 个订单待确认！")
            print(f"   请访问 http://localhost:8080/admin 处理")
        
        # 3. 生成新的营销内容（如果计划快用完了）
        self._check_and_generate_content()
        
        print(f"\n{'='*50}")
        print(f"  ✅ 今日优化完成！")
        print(f"{'='*50}")
    
    def _check_and_generate_content(self):
        """检查营销计划，不足时自动生成"""
        plan_files = sorted(BASE_DIR.glob("marketing/data/plan_*.json"), reverse=True)
        if plan_files:
            with open(plan_files[0], 'r', encoding='utf-8') as f:
                plan = json.load(f)
            future_posts = [p for p in plan if p.get("scheduled_date", "") >= datetime.now().strftime("%Y-%m-%d")]
            if len(future_posts) < 3:
                print("\n[📝] 营销内容不足，自动生成新计划...")
                subprocess.run(["python3", str(BASE_DIR / "marketing" / "auto_publisher.py"), "plan", "--days", "7"])
            else:
                print(f"\n[✓] 营销计划充足（剩余 {len(future_posts)} 条内容）")
        else:
            print("\n[📝] 尚无营销计划，自动生成...")
            subprocess.run(["python3", str(BASE_DIR / "marketing" / "auto_publisher.py"), "plan", "--days", "7"])


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🤖 自动优化引擎")
    parser.add_argument("--daily", action="store_true", help="运行每日优化")
    parser.add_argument("--report", action="store_true", help="仅生成优化报告")
    parser.add_argument("--status", action="store_true", help="查看系统状态")
    
    args = parser.parse_args()
    optimizer = AutoOptimizer()
    
    if args.daily:
        optimizer.run_daily()
    elif args.report:
        optimizer.generate_optimization_report()
    elif args.status:
        analysis = optimizer.analyze_performance()
        print(f"\n📊 系统状态")
        print(f"  {'='*40}")
        print(f"  累计订单: {analysis['total_orders']}")
        print(f"  累计收入: ¥{analysis['total_revenue']:.0f}")
        print(f"  本周订单: {analysis['week_orders']}")
        print(f"  待处理: {len(analysis['pending_orders'])}")
        print(f"  {'='*40}")
        print(f"  网站: http://localhost:8080")
        print(f"  后台: http://localhost:8080/admin")
        print(f"  报告: {optimizer.report_dir}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
