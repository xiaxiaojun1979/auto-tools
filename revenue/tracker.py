#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💰 AutoTools 收益跟踪引擎
核心目标：追踪收入 → 分析趋势 → 优化策略 → 增加收益
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "daily_report" / "data"
REPORT_DIR = BASE_DIR / "daily_report" / "reports"
REVENUE_DIR = BASE_DIR / "revenue"

# 收益目标
REVENUE_GOALS = {
    "daily": 100,      # 日目标 ¥100
    "weekly": 700,     # 周目标 ¥700
    "monthly": 3000,   # 月目标 ¥3000
    "yearly": 36000,   # 年目标 ¥36000
}

class RevenueTracker:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.revenue_dir = REVENUE_DIR
        self.revenue_dir.mkdir(parents=True, exist_ok=True)
    
    def load_orders(self):
        f = self.data_dir / "orders.json"
        if not f.exists():
            return {"orders": [], "total_revenue": 0}
        with open(f) as fh:
            return json.load(fh)
    
    def analyze(self):
        """完整收益分析"""
        data = self.load_orders()
        orders = data.get("orders", [])
        total = data.get("total_revenue", 0)
        
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        week_start = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        month_start = now.strftime("%Y-%m-01")
        
        # 时间维度统计
        today_orders = [o for o in orders if o.get("created_at","").startswith(today)]
        week_orders = [o for o in orders if o.get("created_at","") >= week_start]
        month_orders = [o for o in orders if o.get("created_at","") >= month_start]
        
        today_rev = sum(o.get("price",0) for o in today_orders)
        week_rev = sum(o.get("price",0) for o in week_orders)
        month_rev = sum(o.get("price",0) for o in month_orders)
        
        # 产品收益排行
        product_rev = defaultdict(lambda: {"count": 0, "revenue": 0})
        for o in orders:
            pid = o.get("product_id", "unknown")
            product_rev[pid]["count"] += 1
            product_rev[pid]["revenue"] += o.get("price", 0)
        
        # 收益趋势（最近7天）
        trend = []
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            day_orders = [o for o in orders if o.get("created_at","").startswith(day)]
            trend.append({
                "date": day,
                "revenue": sum(o.get("price",0) for o in day_orders),
                "orders": len(day_orders)
            })
        
        # 目标达成率
        goals = {
            "daily": {"target": REVENUE_GOALS["daily"], "actual": today_rev, 
                     "rate": round(today_rev / REVENUE_GOALS["daily"] * 100, 1)},
            "weekly": {"target": REVENUE_GOALS["weekly"], "actual": week_rev,
                      "rate": round(week_rev / REVENUE_GOALS["weekly"] * 100, 1)},
            "monthly": {"target": REVENUE_GOALS["monthly"], "actual": month_rev,
                       "rate": round(month_rev / REVENUE_GOALS["monthly"] * 100, 1)},
        }
        
        return {
            "total": total,
            "total_orders": len(orders),
            "today": today_rev,
            "today_orders": len(today_orders),
            "week": week_rev,
            "month": month_rev,
            "trend": trend,
            "goals": goals,
            "product_revenue": dict(product_rev),
            "pending": len([o for o in orders if o.get("status") == "pending"]),
        }
    
    def generate_optimization_plan(self, stats):
        """根据收益数据生成优化方案"""
        plans = []
        
        # 1. 收益目标分析
        for period, info in stats["goals"].items():
            if info["actual"] == 0:
                plans.append("【{}目标】尚未有收入，需要立即启动推广！¥{}/天".format(
                    period, info["target"]))
            elif info["rate"] < 50:
                plans.append("【{}目标】达成率{}%，需要加大推广力度".format(
                    period, info["rate"]))
            elif info["rate"] < 100:
                plans.append("【{}目标】达成率{}%，接近目标，继续加油！".format(
                    period, info["rate"]))
            else:
                plans.append("【{}目标】已超额完成！达成率{}% 🎉".format(
                    period, info["rate"]))
        
        # 2. 产品策略
        if stats["total_orders"] > 0:
            best_product = max(stats["product_revenue"].items(), 
                              key=lambda x: x[1]["revenue"])
            plans.append("【畅销品】{} 收入¥{}，建议重点推广".format(
                best_product[0], best_product[1]["revenue"]))
        
        # 3. 增收建议
        plans.append("【增收建议】推广 VIP 会员（¥199），利润率最高")
        plans.append("【增收建议】推出企业定制服务，单价 ¥500+")
        plans.append("【增收建议】闲鱼每天发1条商品信息，坚持7天")
        plans.append("【增收建议】朋友圈每3天分享1次客户好评")
        
        # 4. 激励目标
        if stats["today"] == 0:
            plans.append("【今日目标】至少完成1单（¥29-¥199）")
        elif stats["today"] < 100:
            plans.append("【今日目标】还差 ¥{} 达到日目标 ¥100".format(
                100 - stats["today"]))
        
        return plans
    
    def save_report(self):
        """保存收益报告"""
        stats = self.analyze()
        plans = self.generate_optimization_plan(stats)
        
        report = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "stats": stats,
            "plans": plans,
            "goals": REVENUE_GOALS,
        }
        
        path = self.revenue_dir / "revenue_report.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return report
    
    def print_summary(self):
        report = self.save_report()
        s = report["stats"]
        
        print("=" * 50)
        print("  💰 AutoTools 收益报告")
        print("  {}".format(report["date"]))
        print("=" * 50)
        print()
        print("  累计收益: ¥{} ({}单)".format(s["total"], s["total_orders"]))
        print("  今日收益: ¥{} ({}单)".format(s["today"], s["today_orders"]))
        print("  本周收益: ¥{}".format(s["week"]))
        print("  本月收益: ¥{}".format(s["month"]))
        print()
        print("  📊 目标达成率:")
        for p, g in s["goals"].items():
            bar = "█" * int(g["rate"] / 10) + "░" * (10 - int(g["rate"] / 10))
            print("    {}: {:>7} {:<12} {}%".format(
                p[:3], "¥{}/{}".format(g["actual"], g["target"]), 
                bar, g["rate"]))
        print()
        print("  💡 优化方案:")
        for p in report["plans"]:
            print("    {}".format(p))
        print()
        
        return report

if __name__ == "__main__":
    RevenueTracker().print_summary()
