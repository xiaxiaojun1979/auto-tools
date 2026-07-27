#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 每日自动运营报告生成器
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "daily_report" / "data"
REPORT_DIR = BASE_DIR / "daily_report" / "reports"
ORDERS_FILE = DATA_DIR / "orders.json"

PRODUCTS = {
    "file_tools": {"name": "文件批处理大师", "price": 49, "emoji": "1f4c1"},
    "content_gen": {"name": "内容自动生成器", "price": 29, "emoji": "270d"},
    "data_tools": {"name": "数据清洗工具包", "price": 39, "emoji": "1f9f9"},
    "bundle": {"name": "三件套捆绑包", "price": 79, "emoji": "1f389"},
}

def load_data():
    if not ORDERS_FILE.exists():
        return {"orders": [], "total_revenue": 0}
    with open(ORDERS_FILE, 'r') as f:
        return json.load(f)

def analyze():
    data = load_data()
    orders = data.get("orders", [])
    today = datetime.now().strftime("%Y-%m-%d")
    
    today_orders = [o for o in orders if o.get("created_at","").startswith(today)]
    month_orders = [o for o in orders if o.get("created_at","")[:7] == today[:7]]
    pending = [o for o in orders if o.get("status") == "pending"]
    
    ps = {}
    for pid, info in PRODUCTS.items():
        sales = [o for o in orders if o.get("product_id") == pid]
        ps[pid] = {
            "name": info["name"], "count": len(sales),
            "revenue": sum(o.get("price",0) for o in sales),
            "price": info["price"], "emoji": info["emoji"]
        }
    
    return {
        "date": today,
        "total_revenue": data.get("total_revenue", 0),
        "total_orders": len(orders),
        "today_revenue": sum(o.get("price",0) for o in today_orders),
        "today_orders": len(today_orders),
        "month_revenue": sum(o.get("price",0) for o in month_orders),
        "pending_count": len(pending),
        "pending_orders": pending,
        "product_stats": ps,
    }

def generate_tips(stats):
    tips = []
    if stats["total_orders"] == 0:
        tips.append("在朋友圈/微信群分享网站链接 https://xiaoxiaojun.zeabur.app")
        tips.append("在闲鱼发布「工作效率工具」相关商品")
        tips.append("小红书/B站发布工具使用教程引流")
        tips.append("设置首单优惠，吸引第一批客户")
        return tips
    
    sorted_p = sorted(stats["product_stats"].values(), key=lambda x: x["count"], reverse=True)
    if sorted_p and sorted_p[0]["count"] > 0:
        tips.append("畅销品：{} 已售 {} 件，重点推广".format(sorted_p[0]["name"], sorted_p[0]["count"]))
    
    if stats["today_orders"] > 0:
        tips.append("今日有 {} 单，推广有效！".format(stats["today_orders"]))
    tips.append("持续在闲鱼/小红书发布内容引流")
    tips.append("每3天检查后台，及时处理订单")
    return tips

def generate_html(stats, tips):
    date = stats["date"]
    sp = sorted(stats["product_stats"].values(), key=lambda x: x["revenue"], reverse=True)
    
    def tag(text, cls):
        return '<span style="display:inline-block;padding:2px 10px;border-radius:10px;font-size:0.8em;background:{};color:{}">{}</span>'.format(
            "#fff2f0" if cls=="hot" else "#f0f5ff",
            "#ff4d4f" if cls=="hot" else "#1890ff",
            text
        )
    
    rows = ""
    for p in sp:
        c = "hot" if p["count"] > 0 else "cold"
        rows += '<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f5f5f5">'
        rows += '<span>{} {} {}</span>'.format(
            chr(int(p["emoji"],16)) if p["emoji"].startswith("1") else "",
            p["name"],
            tag("{}件".format(p["count"]), c)
        )
        rows += '<span><strong>¥{}</strong></span></div>'.format(p["revenue"])
    
    tips_html = ""
    for t in tips:
        tips_html += '<div style="padding:8px 0;border-bottom:1px solid #f5f5f5;font-size:0.95em;color:#555">{}</div>'.format(t)
    
    pending_html = ""
    if stats["pending_count"] > 0:
        pending_html = '<div style="padding:8px 0">有 <strong>{}</strong> 笔订单待确认！<br>👉 <a href="https://xiaoxiaojun.zeabur.app/admin" style="color:#667eea">去后台处理</a></div>'.format(stats["pending_count"])
    else:
        pending_html = '<div style="padding:8px 0;color:#52c41a">暂无待处理订单 ✅</div>'
    
    html = """<!DOCTYPE html>
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
    <h1>AutoTools 运营报告</h1>
    <div style="opacity:0.85;font-size:0.95em">{date}</div>
  </div>
  <div class="stats">
    <div class="sc"><div class="n">¥{tr}</div><div class="l">累计收入</div></div>
    <div class="sc"><div class="n">{to}</div><div class="l">累计订单</div></div>
    <div class="sc"><div class="n">¥{tdr}</div><div class="l">今日收入</div></div>
    <div class="sc"><div class="n">{tdo}</div><div class="l">今日订单</div></div>
  </div>
  <div class="section">
    <h2>产品销售排行</h2>
    {rows}
  </div>
  <div class="section">
    <h2>优化建议</h2>
    {tips_html}
  </div>
  <div class="section">
    <h2>待处理事项</h2>
    {pending_html}
  </div>
  <div class="footer">
    <p>AutoTools 自动运营 · 每日自动生成</p>
    <p>后台: <a href="https://xiaoxiaojun.zeabur.app/admin" style="color:#667eea">xiaoxiaojun.zeabur.app/admin</a></p>
    <p>支付宝: 15156215580</p>
  </div>
</div>
</body>
</html>
""".format(
        date=date, tr=stats["total_revenue"], to=stats["total_orders"],
        tdr=stats["today_revenue"], tdo=stats["today_orders"],
        rows=rows, tips_html=tips_html, pending_html=pending_html
    )
    return html

def run():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    stats = analyze()
    tips = generate_tips(stats)
    html = generate_html(stats, tips)
    
    path = REPORT_DIR / "report_{}.html".format(stats["date"])
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    json_path = DATA_DIR / "daily_{}.json".format(stats["date"])
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("Report: {}".format(path))
    print("Revenue: ${}, Orders: {}".format(stats["total_revenue"], stats["total_orders"]))
    print("Today: ${}, {} orders".format(stats["today_revenue"], stats["today_orders"]))
    return stats

if __name__ == "__main__":
    run()
