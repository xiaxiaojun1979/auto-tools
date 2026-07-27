#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 每日自动运营报告生成器
动态加载products.json，支持所有产品
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "daily_report" / "data"
REPORT_DIR = BASE_DIR / "daily_report" / "reports"
ORDERS_FILE = DATA_DIR / "orders.json"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"


def load_products():
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def load_data():
    if not ORDERS_FILE.exists():
        return {"orders": [], "total_revenue": 0}
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"orders": [], "total_revenue": 0}


def analyze():
    data = load_data()
    orders = data.get("orders", [])
    total_revenue = data.get("total_revenue", 0)
    total_orders = len(orders)

    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in orders if o.get("created_at", "").startswith(today)]
    today_revenue = sum(o.get("price", 0) for o in today_orders)

    products = load_products()
    product_stats = {}
    for p in products:
        pid = p["id"]
        sold = [o for o in orders if o.get("product_id") == pid]
        product_stats[pid] = {
            "name": p["name"],
            "emoji": p.get("emoji", "📦"),
            "price": p["price"],
            "count": len(sold),
            "revenue": sum(o.get("price", 0) for o in sold)
        }

    pending_count = len([o for o in orders if o.get("status") == "pending"])
    week_orders = [o for o in orders
                   if o.get("created_at", "") >= (datetime.now().strftime("%Y-%m-%d") + " 00:00:00")]

    return {
        "date": today,
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "today_revenue": today_revenue,
        "today_orders": len(today_orders),
        "week_revenue": sum(o.get("price", 0) for o in week_orders),
        "pending_count": pending_count,
        "product_stats": product_stats
    }


def generate_tips(stats):
    tips = []

    if stats["today_revenue"] == 0:
        tips.append("⚠️ 今日尚无收入！立即在闲鱼/朋友圈发布推广")
        tips.append("💡 今日目标：至少完成1单（¥29-¥299）")
    elif stats["today_revenue"] < 100:
        tips.append(f"📈 今日收入 ¥{stats['today_revenue']}，还差 ¥{100-stats['today_revenue']} 达到日目标")
        tips.append(f"🔥 重点推广 VIP会员（¥199）或三件套（¥79），单笔价值高")
    else:
        tips.append(f"🎉 今日已完成日目标（¥100）！达成率 {round(stats['today_revenue']/100*100)}%")

    # 畅销品分析
    products = load_products()
    best = None
    for p in products:
        ps = stats["product_stats"].get(p["id"], {})
        if ps.get("count", 0) > 0:
            if not best or ps["revenue"] > best["revenue"]:
                best = {"name": p["name"], "count": ps["count"], "revenue": ps["revenue"]}

    if best:
        tips.append(f"🏆 畅销品：{best['name']}（{best['count']}单，¥{best['revenue']}）")
        tips.append(f"✅ 建议：加大该产品推广力度，在闲鱼/小红书多发帖")

    # 增收策略
    tips.append("💎 推广 VIP 会员（¥199）解锁全部工具，利润率最高")
    tips.append("📱 闲鱼每天发1条商品信息，坚持7天见效")
    tips.append("👥 朋友圈每3天分享1次客户好评或使用效果")
    tips.append("🎯 小红书发布工具使用教程，引流到网站下单")
    tips.append("🚀 推荐企业批量部署（¥999）和定制开发（¥499）等高价值服务")

    # 待处理
    if stats["pending_count"] > 0:
        tips.append(f"📋 有 {stats['pending_count']} 笔订单待确认！立即处理")

    return tips


def generate_html(stats, tips):
    date = stats["date"]
    tr = stats["total_revenue"]
    to = stats["total_orders"]
    tdr = stats["today_revenue"]
    tdo = stats["today_orders"]

    # 产品排行
    sp = sorted(stats["product_stats"].values(), key=lambda x: x["revenue"], reverse=True)

    def tag(text, cls):
        bg = "#fff2f0" if cls == "hot" else "#f0f5ff"
        fg = "#ff4d4f" if cls == "hot" else "#1890ff"
        return f'<span style="display:inline-block;padding:2px 10px;border-radius:10px;font-size:0.8em;background:{bg};color:{fg}">{text}</span>'

    rows = ""
    for n, p in enumerate(sp, 1):
        c = "hot" if p["count"] > 0 else "cold"
        medal = "🥇" if n == 1 else "🥈" if n == 2 else "🥉" if n == 3 else f"{n}."
        rows += f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f5f5f5">'
        rows += f'<span>{medal} {p["emoji"]} {p["name"]} {tag("{}" + str(p["count"]) + "件", c)}</span>'
        rows += f'<span><strong>¥{p["revenue"]}</strong></span></div>'

    tips_html = ""
    for t in tips:
        tips_html += f'<div style="padding:8px 0;border-bottom:1px solid #f5f5f5;font-size:0.95em;color:#555">{t}</div>'

    pending_html = ""
    if stats["pending_count"] > 0:
        pending_html = f'<div style="padding:12px 0;background:#fff2f0;border-radius:8px;text-align:center">有 <strong>{stats["pending_count"]}</strong> 笔订单待确认！<br>👉 <a href="https://xiaxiaojun.zeabur.app/admin" style="color:#667eea;font-weight:600">去后台处理 →</a></div>'
    else:
        pending_html = '<div style="padding:12px 0;color:#52c41a;text-align:center">暂无待处理订单 ✅</div>'

    # 产品总数
    total_products = len(load_products())

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>每日运营报告 - {date}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f5f7fa; color:#1a1a2e; padding:20px; }}
.container {{ max-width:800px; margin:0 auto; }}
.header {{ background:linear-gradient(135deg,#667eea,#764ba2); color:white; padding:30px; border-radius:16px; margin-bottom:20px; text-align:center; }}
.header h1 {{ font-size:1.8em; margin-bottom:5px; }}
.stats {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px; margin-bottom:20px; }}
.sc {{ background:white; border-radius:12px; padding:20px; text-align:center; box-shadow:0 2px 10px rgba(0,0,0,0.06); }}
.sc .n {{ font-size:2em; font-weight:bold; color:#667eea; }}
.sc .l {{ font-size:0.85em; color:#999; margin-top:4px; }}
.section {{ background:white; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 2px 10px rgba(0,0,0,0.06); }}
.section h2 {{ font-size:1.2em; margin-bottom:16px; border-bottom:2px solid #f0f0f0; padding-bottom:8px; }}
.footer {{ text-align:center; color:#999; font-size:0.8em; padding:20px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📊 AutoTools 运营报告</h1>
    <div style="opacity:0.85;font-size:0.95em">{date} · {total_products}个产品</div>
  </div>
  <div class="stats">
    <div class="sc"><div class="n">¥{tr}</div><div class="l">累计收入</div></div>
    <div class="sc"><div class="n">{to}</div><div class="l">累计订单</div></div>
    <div class="sc"><div class="n">¥{tdr}</div><div class="l">今日收入</div></div>
    <div class="sc"><div class="n">{tdo}</div><div class="l">今日订单</div></div>
  </div>
  <div class="section">
    <h2>📦 产品销售排行</h2>
    {rows}
  </div>
  <div class="section">
    <h2>💡 优化建议</h2>
    {tips_html}
  </div>
  <div class="section">
    <h2>📋 待处理事项</h2>
    {pending_html}
  </div>
  <div class="footer">
    <p>AutoTools 自动运营 · 每日自动生成 · 收益第一原则</p>
    <p>后台: <a href="https://xiaxiaojun.zeabur.app/admin" style="color:#667eea">xiaxiaojun.zeabur.app/admin</a></p>
    <p>支付宝: 15156215580 | {total_products}个产品在售 | 日目标¥100</p>
  </div>
</div>
</body>
</html>"""
    return html


def run():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # 收益分析
    try:
        from revenue.tracker import RevenueTracker
        rt = RevenueTracker()
        rt.save_report()
    except Exception as e:
        print(f"Revenue report: {e}")

    stats = analyze()
    tips = generate_tips(stats)
    html = generate_html(stats, tips)

    path = REPORT_DIR / f"report_{stats['date']}.html"
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

    json_path = DATA_DIR / f"daily_{stats['date']}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"✅ Report: {path}")
    print(f"💰 Revenue: ¥{stats['total_revenue']}, Orders: {stats['total_orders']}")
    print(f"📈 Today: ¥{stats['today_revenue']}, {stats['today_orders']} orders")
    return stats


if __name__ == "__main__":
    run()
