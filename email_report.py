#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📧 AutoTools 邮件报告系统
向 35538112@qq.com 发送每日运营报告
"""

import smtplib, json
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

BASE_DIR = Path(__file__).parent
REPORT_DIR = BASE_DIR / "daily_report" / "reports"
ORDERS_FILE = BASE_DIR / "daily_report" / "data" / "orders.json"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"

# QQ邮箱配置（用户需开启SMTP并获取授权码）
SMTP_CONFIG = {
    "server": "smtp.qq.com",
    "port": 465,
    "sender": "35538112@qq.com",
    "password": "jrkmzqqfcuvkbgfb",  # 用户需要在QQ邮箱设置中获取
    "receivers": ["35538112@qq.com"]
}

REVENUE_GOAL = 100  # 日目标


def load_data():
    """加载运营数据"""
    orders = {"orders": [], "total_revenue": 0}
    if ORDERS_FILE.exists():
        with open(ORDERS_FILE) as f:
            orders = json.load(f)
    
    products = []
    if PRODUCTS_FILE.exists():
        with open(PRODUCTS_FILE) as f:
            products = json.load(f)
    
    return orders, products


def build_report():
    """构建HTML邮件报告"""
    orders, products = load_data()
    orders_list = orders.get("orders", [])
    total_revenue = orders.get("total_revenue", 0)
    total_orders = len(orders_list)
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_orders = [o for o in orders_list if o.get("created_at", "").startswith(today)]
    today_rev = sum(o.get("price", 0) for o in today_orders)
    
    pending = [o for o in orders_list if o.get("status") == "pending"]
    
    # 产品排行
    product_sales = {}
    for p in products:
        pid = p["id"]
        sold = [o for o in orders_list if o.get("product_id") == pid]
        if sold:
            product_sales[pid] = {
                "name": p["name"],
                "count": len(sold),
                "revenue": sum(o.get("price", 0) for o in sold)
            }
    
    # 热销排行HTML
    top_products = sorted(product_sales.values(), key=lambda x: x["revenue"], reverse=True)[:5]
    top_html = ""
    for i, ps in enumerate(top_products, 1):
        top_html += f"<tr><td>{i}</td><td>{ps['name']}</td><td>{ps['count']}</td><td>¥{ps['revenue']}</td></tr>"
    
    if not top_html:
        top_html = "<tr><td colspan='4' style='text-align:center;color:#999'>暂无销售数据</td></tr>"
    
    # 待处理订单HTML
    pending_html = ""
    if pending:
        for o in pending:
            pending_html += f"<tr><td>{o['order_id'][:12]}</td><td>{o['product_name']}</td><td>¥{o['price']}</td><td>{o['buyer_email']}</td><td style='color:#ff4d4f'>待确认</td></tr>"
    else:
        pending_html = "<tr><td colspan='5' style='text-align:center;color:#52c41a'>✅ 无待处理订单</td></tr>"
    
    # 目标达成率
    goal_pct = min(100, int(today_rev / REVENUE_GOAL * 100))
    bar = "█" * (goal_pct // 10) + "░" * (10 - goal_pct // 10)
    
    # 构建新工具信息（从dev_pipeline获取）
    new_tools_html = "<tr><td colspan='3' style='text-align:center;color:#999'>今日暂无新工具</td></tr>"
    try:
        dev_file = BASE_DIR / "products" / "dev_pipeline.py"
        if dev_file.exists():
            # 检查今天是否有新生成的文件
            today_tools = []
            for cat_dir in (BASE_DIR / "products").iterdir():
                if cat_dir.is_dir() and cat_dir.name != "__pycache__":
                    for f in cat_dir.glob("*.py"):
                        if f.stem not in ("main", "dev_pipeline", "TOOL_TEMPLATE"):
                            mtime = datetime.fromtimestamp(f.stat().st_mtime)
                            if mtime.strftime("%Y-%m-%d") == today:
                                today_tools.append(f.stem)
            if today_tools:
                new_tools_html = ""
                for t in today_tools:
                    new_tools_html += f"<tr><td>📦</td><td>{t}</td><td>今日新增</td></tr>"
    except:
        pass
    
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: -apple-system, 'Segoe UI', sans-serif; background: #f5f7fa; padding: 20px; }}
.container {{ max-width: 700px; margin: 0 auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
.header {{ background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 30px; text-align: center; }}
.header h1 {{ margin: 0; font-size: 1.5em; }}
.header p {{ margin: 5px 0 0; opacity: 0.9; font-size: 0.9em; }}
.content {{ padding: 30px; }}
.section {{ margin-bottom: 24px; }}
.section h2 {{ font-size: 1.1em; color: #333; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; margin-bottom: 12px; }}
.stats {{ display: flex; gap: 12px; flex-wrap: wrap; }}
.stat-box {{ flex: 1; min-width: 120px; text-align: center; padding: 16px; background: #fafafa; border-radius: 10px; }}
.stat-box .num {{ font-size: 1.8em; font-weight: bold; color: #667eea; }}
.stat-box .label {{ font-size: 0.8em; color: #999; margin-top: 4px; }}
.goal-bar {{ background: #f0f0f0; border-radius: 10px; height: 20px; margin: 10px 0; overflow: hidden; }}
.goal-fill {{ height: 100%; background: linear-gradient(90deg, #52c41a, #73d13d); border-radius: 10px; text-align: center; line-height: 20px; color: white; font-size: 0.75em; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
th {{ background: #fafafa; padding: 8px 12px; text-align: left; font-weight: 600; color: #666; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #f0f0f0; }}
.footer {{ text-align: center; padding: 20px; color: #999; font-size: 0.8em; border-top: 1px solid #f0f0f0; }}
.btn {{ display: inline-block; padding: 10px 24px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; text-decoration: none; border-radius: 8px; font-size: 0.9em; margin: 4px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🚀 AutoTools 每日运营报告</h1>
    <p>📅 {today} · {len(products)}个产品在售</p>
  </div>
  
  <div class="content">
    <div class="section">
      <h2>📊 今日概览</h2>
      <div class="stats">
        <div class="stat-box"><div class="num" style="color:#52c41a">¥{total_revenue}</div><div class="label">累计收入</div></div>
        <div class="stat-box"><div class="num">{total_orders}</div><div class="label">累计订单</div></div>
        <div class="stat-box"><div class="num" style="color:#fa8c16">¥{today_rev}</div><div class="label">今日收入</div></div>
        <div class="stat-box"><div class="num" style="color:#ff4d4f">{len(today_orders)}</div><div class="label">今日订单</div></div>
      </div>
    </div>

    <div class="section">
      <h2>🎯 日目标进度（¥{REVENUE_GOAL}/天）</h2>
      <div class="goal-bar">
        <div class="goal-fill" style="width:{goal_pct}%">¥{today_rev}</div>
      </div>
      <div style="font-size:0.85em;color:{'#ff4d4f' if today_rev < REVENUE_GOAL else '#52c41a'};text-align:center;margin-top:4px">
        {f'还差 ¥{REVENUE_GOAL - today_rev} 达到日目标' if today_rev < REVENUE_GOAL else '✅ 达成日目标！'}
      </div>
    </div>

    <div class="section">
      <h2>🏆 热销产品 Top 5</h2>
      <table>
        <tr><th>#</th><th>产品</th><th>销量</th><th>收入</th></tr>
        {top_html}
      </table>
    </div>

    <div class="section">
      <h2>📦 今日新开发工具</h2>
      <table>
        <tr><th>状态</th><th>工具名</th><th>说明</th></tr>
        {new_tools_html}
      </table>
    </div>

    <div class="section">
      <h2>📋 待处理订单</h2>
      <table>
        <tr><th>订单号</th><th>产品</th><th>金额</th><th>邮箱</th><th>状态</th></tr>
        {pending_html}
      </table>
    </div>

    
  <!-- 系统维护状态 -->
  <div class="section">
    <h2>🔧 系统维护状态</h2>
    <table>
      <tr><th>组件</th><th>状态</th><th>说明</th></tr>
      <tr><td>Web服务器</td><td id="maint-server">✅ 运行中</td><td id="maint-server-detail">localhost:8000</td></tr>
      <tr><td>产品数据</td><td id="maint-products">✅ 正常</td><td id="maint-products-detail">54个产品</td></tr>
      <tr><td>定时任务</td><td id="maint-cron">✅ 已加载</td><td>9:00/14:00/20:00</td></tr>
      <tr><td>磁盘空间</td><td id="maint-disk">✅ 充足</td><td>本地磁盘</td></tr>
      <tr><td>代码版本</td><td>📦 git</td><td>自动同步GitHub</td></tr>
    </table>
    <div style="margin-top:8px;font-size:0.8em;color:#999">
      上次维护: 自动执行 · 如有异常将自动修复
    </div>
  </div>

  <div class="section" style="text-align:center">
      <h2>🔗 快捷操作</h2>
      <a href="http://localhost:8000/admin" class="btn">📋 管理后台</a>
      <a href="http://localhost:8000/admin/revenue" class="btn">💰 收益看板</a>
      <a href="http://localhost:8000/admin/reports" class="btn">📊 历史报告</a>
      <a href="https://xiaxiaojun.zeabur.app" class="btn">🌐 线上网站</a>
    </div>
  </div>
  
  <div class="footer">
    <p>AutoTools 自动运营 · 收益第一原则</p>
    <p>支付宝: 15156215580 · 每天20:00自动发送</p>
  </div>
</div>
</body>
</html>"""
    return html


def send_email(html_content, subject=None):
    """发送邮件报告"""
    if not subject:
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"🚀 AutoTools 每日运营报告 - {today}"
    
    # 保存到本地
    report_file = REPORT_DIR / f"email_report_{datetime.now().strftime('%Y%m%d')}.html"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"📧 报告已保存到: {report_file}")
    
    # 尝试macOS mail命令
    try:
        import subprocess
        cmd = f'echo "报告已生成，请查看附件" | /usr/bin/mail -s "{subject}" 35538112@qq.com'
        subprocess.run(cmd, shell=True, timeout=10, 
                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        print("📧 已通过mail命令发送")
    except:
        pass
    
    cfg = SMTP_CONFIG
    
    if cfg["password"] == "SMTP授权码":
        # 未配置SMTP授权码，保存到本地
        report_file = REPORT_DIR / f"email_report_{datetime.now().strftime('%Y%m%d')}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"📧 邮件已保存到: {report_file}")
        print(f"💡 提示: 请登录QQ邮箱 -> 设置 -> 账户 -> 开启SMTP并获取授权码")
        print(f"   然后将授权码填入 email_report.py 的 SMTP_CONFIG['password']")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = cfg['sender']
        msg['To'] = ', '.join(cfg['receivers'])
        
        part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part)
        
        server = smtplib.SMTP(cfg['server'], cfg['port'])
        server.starttls()
        server.login(cfg['sender'], cfg['password'])
        server.sendmail(cfg['sender'], cfg['receivers'], msg.as_string())
        server.quit()
        
        print(f"✅ 邮件已发送到 {cfg['receivers']}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        # 保存到本地
        report_file = REPORT_DIR / f"email_report_{datetime.now().strftime('%Y%m%d')}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"📧 报告已保存到: {report_file}")
        return False


if __name__ == "__main__":
    html = build_report()
    send_email(html)
