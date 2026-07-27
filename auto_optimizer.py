#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 AutoTools 自动优化引擎
收益第一原则！每日自动优化策略，最大化收入
"""

import json, os, sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "daily_report" / "data"
REPORT_DIR = BASE_DIR / "daily_report" / "reports"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
ORDERS_FILE = DATA_DIR / "orders.json"


class AutoOptimizer:
    def __init__(self):
        self.products = self._load_products()
        self.orders = self._load_orders()
        self.now = datetime.now()
        self.today = self.now.strftime("%Y-%m-%d")

    def _load_products(self):
        try:
            with open(PRODUCTS_FILE) as f:
                return json.load(f)
        except:
            return []

    def _load_orders(self):
        try:
            with open(ORDERS_FILE) as f:
                return json.load(f)
        except:
            return {"orders": [], "total_revenue": 0}

    def analyze_revenue(self):
        """完整收益分析"""
        orders = self.orders.get("orders", [])
        total = self.orders.get("total_revenue", 0)

        # 时间维度
        today_orders = [o for o in orders if o.get("created_at", "").startswith(self.today)]
        week_start = (self.now - timedelta(days=self.now.weekday())).strftime("%Y-%m-%d")
        month_start = self.now.strftime("%Y-%m-01")

        today_rev = sum(o.get("price", 0) for o in today_orders)
        week_rev = sum(o.get("price", 0) for o in orders
                       if o.get("created_at", "") >= week_start)
        month_rev = sum(o.get("price", 0) for o in orders
                        if o.get("created_at", "") >= month_start)

        # 产品排行
        product_sales = {}
        for p in self.products:
            pid = p["id"]
            sold = [o for o in orders if o.get("product_id") == pid]
            product_sales[pid] = {
                "name": p["name"],
                "price": p["price"],
                "category": p.get("category", ""),
                "count": len(sold),
                "revenue": sum(o.get("price", 0) for o in sold)
            }

        # 7天趋势
        trend = []
        for i in range(6, -1, -1):
            day = (self.now - timedelta(days=i)).strftime("%Y-%m-%d")
            day_orders = [o for o in orders if o.get("created_at", "").startswith(day)]
            trend.append({
                "date": day,
                "revenue": sum(o.get("price", 0) for o in day_orders),
                "orders": len(day_orders)
            })

        # 分类分析
        cat_stats = {}
        for p in self.products:
            cat = p.get("category", "其他")
            if cat not in cat_stats:
                cat_stats[cat] = {"count": 0, "revenue": 0}
            pid = p["id"]
            sold = [o for o in orders if o.get("product_id") == pid]
            cat_stats[cat]["count"] += len(sold)
            cat_stats[cat]["revenue"] += sum(o.get("price", 0) for o in sold)

        return {
            "total_revenue": total,
            "total_orders": len(orders),
            "today": {"revenue": today_rev, "orders": len(today_orders)},
            "week": {"revenue": week_rev},
            "month": {"revenue": month_rev},
            "pending": len([o for o in orders if o.get("status") == "pending"]),
            "product_sales": product_sales,
            "category_stats": cat_stats,
            "trend": trend,
            "analysis_time": self.now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def generate_strategies(self, stats):
        """根据数据生成增收策略"""
        strategies = []
        today_rev = stats["today"]["revenue"]
        total_rev = stats["total_revenue"]

        # 1. 今日表现
        if today_rev == 0:
            strategies.append(("🔴", "紧急", "今日尚无收入！立即启动推广"))
            strategies.append(("💡", "行动", "在闲鱼发布1-2个商品，定价¥29-¥79"))
        elif today_rev < 100:
            strategies.append(("🟡", "提醒", f"今日收入¥{today_rev}，还差¥{100-today_rev}到日目标"))
            strategies.append(("💡", "行动", "推荐客户购买VIP会员(¥199)，单笔达日目标"))
        else:
            strategies.append(("🟢", "达成", f"今日收入¥{today_rev}，达成日目标🎉"))

        # 2. 畅销品策略
        best_product = None
        for pid, ps in stats["product_sales"].items():
            if ps["count"] > 0:
                if not best_product or ps["revenue"] > best_product["revenue"]:
                    best_product = ps

        if best_product:
            strategies.append(("🏆", "畅销", f"{best_product['name']}({best_product['count']}单/¥{best_product['revenue']})"))
            strategies.append(("📢", "推广", f"重点推广{best_product['name']}，闲鱼/小红书多发帖"))
        else:
            strategies.append(("📢", "推广", "暂无销售记录，建议从低价产品(¥19-¥29)开始推广"))

        # 3. 高利润产品推广
        high_value = [p for p in self.products if p["price"] >= 100]
        if high_value:
            strategies.append(("💎", "高利", f"高价值服务({len(high_value)}个): ¥{high_value[0]['price']}-¥{high_value[-1]['price']}"))
            strategies.append(("🎯", "推荐", "企业客户推荐定制开发(¥499)和企业部署(¥999)"))

        # 4. 平台策略
        strategies.append(("📱", "闲鱼", "每天发1条商品信息，用带图文案"))
        strategies.append(("👥", "朋友圈", "每3天分享一次客户好评"))
        strategies.append(("📕", "小红书", "发布工具使用教程引流"))
        strategies.append(("🤝", "知乎", "在相关问题下回答引流"))

        # 5. 定价策略
        cheap = [p for p in self.products if p["price"] <= 29]
        mid = [p for p in self.products if 29 < p["price"] <= 99]
        expensive = [p for p in self.products if p["price"] > 99]
        strategies.append(("💰", "定价", f"¥19-29({len(cheap)}个) ¥35-99({len(mid)}个) ¥199+({len(expensive)}个)"))
        strategies.append(("🎁", "捆绑", "推荐三件套(¥79)和VIP会员(¥199)，提升客单价"))

        return strategies

    def generate_report_html(self, stats, strategies):
        """生成HTML优化报告"""
        today_rev = stats["today"]["revenue"]
        today_orders = stats["today"]["orders"]
        total_rev = stats["total_revenue"]
        total_orders = stats["total_orders"]
        pending = stats["pending"]

        # 产品排行HTML
        sorted_products = sorted(
            stats["product_sales"].values(),
            key=lambda x: x["revenue"],
            reverse=True
        )

        product_rows = ""
        for i, ps in enumerate(sorted_products[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            count_badge = f'<span style="background:{"#ff4d4f" if ps["count"]>0 else "#f0f0f0"};color:white;padding:1px 8px;border-radius:8px;font-size:0.75em">{ps["count"]}单</span>'
            product_rows += f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #eee">
                <span>{medal} {ps["name"]} {count_badge}</span>
                <span style="font-weight:bold;color:#52c41a">¥{ps["revenue"]}</span>
            </div>"""

        # 策略HTML
        strategy_rows = ""
        for emoji, tag, text in strategies:
            strategy_rows += f"""
            <div style="display:flex;padding:8px 0;border-bottom:1px solid #f5f5f5;font-size:0.95em">
                <span style="margin-right:8px">{emoji}</span>
                <span style="background:#667eea;color:white;padding:0 8px;border-radius:4px;font-size:0.8em;margin-right:8px;white-space:nowrap">{tag}</span>
                <span style="color:#555">{text}</span>
            </div>"""

        # 趋势HTML
        trend_html = ""
        max_rev = max((t["revenue"] for t in stats["trend"]), default=1)
        for t in stats["trend"]:
            pct = t["revenue"] / max_rev * 100 if max_rev > 0 else 0
            bar_color = "#52c41a" if t["revenue"] > 0 else "#f0f0f0"
            trend_html += f"""
            <div style="display:flex;align-items:center;margin:4px 0">
                <span style="width:80px;font-size:0.8em;color:#999">{t["date"][5:]}</span>
                <div style="flex:1;height:20px;background:#f5f5f5;border-radius:10px;overflow:hidden">
                    <div style="height:100%;width:{pct}%;background:{bar_color};border-radius:10px;transition:width 0.3s"></div>
                </div>
                <span style="width:60px;text-align:right;font-size:0.85em;font-weight:bold">¥{t["revenue"]}</span>
            </div>"""

        # 分类统计
        cat_rows = ""
        for cat, cs in sorted(stats["category_stats"].items(), key=lambda x: x[1]["revenue"], reverse=True):
            cat_rows += f"""
            <div style="display:flex;justify-content:space-between;padding:4px 0;font-size:0.85em">
                <span>{cat}</span>
                <span>{cs["count"]}单 · ¥{cs["revenue"]}</span>
            </div>"""

        goal_pct = min(100, int(today_rev / 100 * 100)) if today_rev > 0 else 0
        goal_bar = "█" * (goal_pct // 10) + "░" * (10 - goal_pct // 10)

        products_count = len(self.products)
        total_value = sum(p["price"] for p in self.products)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AutoTools 优化报告 - {self.today}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f0f2f5; color:#1a1a2e; padding:20px; }}
.container {{ max-width:900px; margin:0 auto; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:30px; border-radius:16px; margin-bottom:20px; text-align:center; }}
.header h1 {{ font-size:1.6em; }}
.header .sub {{ opacity:0.8;font-size:0.9em;margin-top:4px; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:20px; }}
.card {{ background:white; border-radius:12px; padding:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
.card .num {{ font-size:1.8em; font-weight:bold; }}
.card .lbl {{ font-size:0.8em; color:#999; margin-top:2px; }}
.card.green .num {{ color:#52c41a; }}
.card.blue .num {{ color:#667eea; }}
.card.orange .num {{ color:#fa8c16; }}
.card.red .num {{ color:#ff4d4f; }}
.section {{ background:white; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
.section h2 {{ font-size:1.1em; margin-bottom:12px; border-bottom:2px solid #f0f0f0; padding-bottom:8px; color:#333; }}
.goal-bar {{ background:#f5f5f5; border-radius:12px; height:24px; overflow:hidden; margin:12px 0; }}
.goal-fill {{ height:100%; background:linear-gradient(90deg,#52c41a,#73d13d); border-radius:12px; transition:width 0.5s; text-align:center; line-height:24px; color:white; font-size:0.8em; }}
.footer {{ text-align:center; color:#999; font-size:0.8em; padding:20px; }}
.tag {{ display:inline-block; padding:0 6px; border-radius:4px; font-size:0.75em; margin:2px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🚀 AutoTools 自动优化报告</h1>
    <div class="sub">📅 {self.today} · {products_count}个产品在售 · 总价值¥{total_value}</div>
  </div>

  <div class="grid2">
    <div class="card green">
      <div class="num">¥{total_rev}</div>
      <div class="lbl">累计收入</div>
    </div>
    <div class="card blue">
      <div class="num">{total_orders}</div>
      <div class="lbl">累计订单</div>
    </div>
    <div class="card orange">
      <div class="num">¥{today_rev}</div>
      <div class="lbl">今日收入</div>
    </div>
    <div class="card red">
      <div class="num">{today_orders}</div>
      <div class="lbl">今日订单</div>
    </div>
  </div>

  <div class="section">
    <h2>🎯 日目标进度（¥100）</h2>
    <div style="display:flex;justify-content:space-between;font-size:0.85em;color:#999">
      <span>今日收入: ¥{today_rev}</span>
      <span>达成率: {goal_pct}%</span>
      <span>目标: ¥100</span>
    </div>
    <div class="goal-bar">
      <div class="goal-fill" style="width:{goal_pct}%">{'¥'+str(today_rev) if today_rev>0 else ''}</div>
    </div>
    {'<div style="color:#ff4d4f;font-size:0.85em;text-align:center;margin-top:4px">⚠️ 未达成日目标，需要加大推广力度</div>' if today_rev < 100 else '<div style="color:#52c41a;font-size:0.85em;text-align:center;margin-top:4px">✅ 恭喜达成日目标！继续保持 🎉</div>'}
  </div>

  <div class="section">
    <h2>📈 近7天趋势</h2>
    {trend_html}
  </div>

  <div class="section">
    <h2>🏆 产品排行（Top 10）</h2>
    {product_rows}
  </div>

  <div class="grid2">
    <div class="section" style="margin:0">
      <h2>📂 分类统计</h2>
      {cat_rows}
    </div>
    <div class="section" style="margin:0">
      <h2>📋 待处理</h2>
      {'<div style="color:#ff4d4f">有 <strong>' + str(pending) + '</strong> 笔订单待确认</div>' if pending > 0 else '<div style="color:#52c41a">✅ 无待处理</div>'}
      <div style="margin-top:12px;font-size:0.9em">
        <div>后台: <a href="http://localhost:8000/admin" style="color:#667eea">localhost:8000/admin</a></div>
        <div>密码: xxj63858930</div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>💡 今日优化策略</h2>
    {strategy_rows}
  </div>

  <div class="footer">
    <p>AutoTools 自动优化引擎 · 收益第一原则</p>
    <p>支付宝: 15156215580 | 每天自动运行 · 数据分析驱动决策</p>
  </div>
</div>
</body>
</html>"""
        return html

    def run(self):
        """执行完整优化流程"""
        # 分析
        stats = self.analyze_revenue()
        strategies = self.generate_strategies(stats)

        # 保存JSON
        report_dir = REPORT_DIR
        report_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = report_dir / f"optimize_{self.today}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"stats": stats, "strategies": strategies}, f, ensure_ascii=False, indent=2)

        # 生成HTML
        html = self.generate_report_html(stats, strategies)
        html_path = report_dir / f"optimize_{self.today}.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        # 输出摘要
        print(f"\n{'='*50}")
        print(f"  🚀 AutoTools 优化报告")
        print(f"  📅 {self.today} | {stats['analysis_time']}")
        print(f"{'='*50}")
        print(f"  💰 累计: ¥{stats['total_revenue']} | {stats['total_orders']}单")
        print(f"  📈 今日: ¥{stats['today']['revenue']} | {stats['today']['orders']}单")
        print(f"  📋 待处理: {stats['pending']}单")
        print(f"  📦 产品: {len(self.products)}个")
        print(f"\n  💡 Top策略:")
        for emoji, tag, text in strategies[:5]:
            print(f"    {emoji} [{tag}] {text}")
        print(f"\n  📄 报告: {html_path}")
        print(f"{'='*50}\n")

        return stats, strategies


if __name__ == "__main__":
    optimizer = AutoOptimizer()
    optimizer.run()
