#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 自动副业系统 - Flask Web 应用
"""

import json, os, uuid, smtplib, ssl
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, send_from_directory
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "daily_report" / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
ADMIN_PASSWORD = "xxj63858930"
ALIPAY_ACCOUNT = "15156215580"

PRODUCTS = [
    {"id": "file_tools", "emoji": "\U0001f4c1", "name": "文件批处理大师",
     "desc": "批量重命名、格式转换、智能分类 \u2014 一键处理成千上万文件",
     "features": ["批量重命名（支持正则/模板/序号）","智能文件分类（按类型/日期/大小）",
                  "批量格式转换（图片/文档/视频）","重复文件查找与清理","文件夹对比与同步"],
     "price": 49, "price_old": 69},
    {"id": "content_gen", "emoji": "\u270d\ufe0f", "name": "内容自动生成器",
     "desc": "AI驱动的文案/标题/摘要生成，提升内容创作效率",
     "features": ["文章标题智能生成","SEO关键词优化建议","摘要自动提取",
                  "多平台内容适配","批量内容生产"],
     "price": 29, "price_old": 49},
    {"id": "data_tools", "emoji": "\U0001f9f9", "name": "数据清洗工具包",
     "desc": "Excel/CSV数据处理利器，告别手动整理数据的烦恼",
     "features": ["智能缺失值填充","重复数据去重合并","异常值检测与修正",
                  "多表关联与合并","数据可视化报告生成"],
     "price": 39, "price_old": 59},
    {"id": "bundle", "emoji": "\U0001f389", "name": "三件套超值捆绑包",
     "desc": "一次性拥有全部三个工具，省\u00a598！",
     "features": ["全部三个工具完整版","终身免费更新","专享VIP售后群"],
     "price": 79, "price_old": 177, "is_bundle": True}
]

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
app.secret_key = "auto-business-sk-2026"

def init_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ORDERS_FILE.exists():
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"orders":[], "total_revenue":0}, f, ensure_ascii=False, indent=2)

def load_orders():
    if not ORDERS_FILE.exists():
        return {"orders": [], "total_revenue": 0}
    try:
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"orders": [], "total_revenue": 0}

def save_orders(data):
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def gen_order_id():
    return datetime.now().strftime("%Y%m%d%H%M%S") + uuid.uuid4().hex[:6].upper()

def get_product(pid):
    for p in PRODUCTS:
        if p["id"] == pid:
            return p
    return None

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/")
def index():
    return render_template("index.html", products=PRODUCTS, alipay=ALIPAY_ACCOUNT)

@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "\u5bc6\u7801\u9519\u8bef"
    return render_template("admin_login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    data = load_orders()
    orders = list(reversed(data["orders"]))
    stats = {
        "total": len(data["orders"]),
        "revenue": data["total_revenue"],
        "pending": len([o for o in data["orders"] if o["status"]=="pending"]),
        "confirmed": len([o for o in data["orders"] if o["status"]=="confirmed"]),
        "delivered": len([o for o in data["orders"] if o["status"]=="delivered"]),
    }
    return render_template("admin.html", orders=orders, stats=stats, products=PRODUCTS)

@app.route("/admin/confirm/<oid>", methods=["POST"])
@admin_required
def confirm_order(oid):
    data = load_orders()
    for o in data["orders"]:
        if o["order_id"] == oid:
            o["status"] = "confirmed"
            o["confirmed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    save_orders(data)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/deliver/<oid>", methods=["POST"])
@admin_required
def deliver_order(oid):
    data = load_orders()
    for o in data["orders"]:
        if o["order_id"] == oid:
            o["status"] = "delivered"
            o["delivered_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    save_orders(data)
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<oid>", methods=["POST"])
@admin_required
def delete_order(oid):
    data = load_orders()
    target = None
    for o in data["orders"]:
        if o["order_id"] == oid:
            target = o; break
    if target:
        data["total_revenue"] -= target["price"]
        data["orders"].remove(target)
    save_orders(data)
    return redirect(url_for("admin_dashboard"))

@app.route("/api/order", methods=["POST"])
def submit_order():
    try:
        req = request.json
        pid = req.get("product_id","")
        email = req.get("email","").strip()
        payment = req.get("payment","\u652f\u4ed8\u5b9d")
        product = get_product(pid)
        if not email or "@" not in email:
            return jsonify({"ok":False,"msg":"\u8bf7\u8f93\u5165\u6b63\u786e\u7684\u90ae\u7bb1"}), 400
        if not product:
            return jsonify({"ok":False,"msg":"\u4ea7\u54c1\u4e0d\u5b58\u5728"}), 400
        oid = gen_order_id()
        order = {
            "order_id": oid, "product_id": pid,
            "product_name": product["name"], "price": product["price"],
            "buyer_email": email, "payment": payment,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confirmed_at": None, "delivered_at": None
        }
        data = load_orders()
        data["orders"].append(order)
        data["total_revenue"] += product["price"]
        save_orders(data)
        return jsonify({"ok":True,"order_id":oid,"msg":"\u8ba2\u5355\u63d0\u4ea4\u6210\u529f\uff01\u786e\u8ba4\u6536\u6b3e\u540e\u5c06\u53d1\u9001\u4ea7\u54c1\u5230\u4f60\u7684\u90ae\u7bb1"})
    except Exception as e:
        return jsonify({"ok":False,"msg":f"\u7cfb\u7edf\u9519\u8bef: {str(e)}"}), 500

@app.route("/api/order/<oid>")
def query_order(oid):
    data = load_orders()
    for o in data["orders"]:
        if o["order_id"] == oid:
            return jsonify({"ok":True,"order":o})
    return jsonify({"ok":False,"msg":"\u8ba2\u5355\u4e0d\u5b58\u5728"}), 404

@app.route("/api/stats")
def get_stats():
    try:
        data = load_orders()
        ps = {}
        for p in PRODUCTS:
            s = [o for o in data["orders"] if o["product_id"]==p["id"]]
            ps[p["id"]] = {"name":p["name"],"count":len(s),"revenue":sum(o["price"] for o in s)}
        return jsonify({
            "ok":True, "total_orders": len(data["orders"]),
            "total_revenue": data["total_revenue"],
            "pending": len([o for o in data["orders"] if o["status"]=="pending"]),
            "product_sales": ps
        })
    except Exception as e:
        return jsonify({"ok":False, "error": str(e)}), 500

@app.route("/assets/<path:filename>")
def serve_asset(filename):
    return send_from_directory(str(BASE_DIR / "website" / "assets"), filename)






@app.route("/admin/marketing")
@admin_required
def view_marketing():
    """查看推广文案"""
    marketing_dir = BASE_DIR / "marketing" / "data"
    posts = []
    if marketing_dir.exists():
        files = sorted(marketing_dir.glob("posts_*.json"), reverse=True)
        if files:
            import json
            with open(files[0], 'r') as f:
                posts = json.load(f)
    
    return render_template("marketing.html", posts=posts)

@app.route("/admin/reports")
@admin_required
def view_reports():
    """查看每日报告列表"""
    report_dir = BASE_DIR / "daily_report" / "reports"
    reports = sorted(report_dir.glob("report_*.html"), reverse=True)
    return render_template("reports.html", reports=reports[:30])

@app.route("/admin/report/<filename>")
@admin_required
def view_report(filename):
    """查看具体报告"""
    from flask import send_from_directory
    report_dir = BASE_DIR / "daily_report" / "reports"
    return send_from_directory(str(report_dir), filename)

@app.route("/download")
def download_code():
    """下载完整项目代码"""
    from flask import send_file
    import subprocess
    zip_path = "/tmp/autotools_deploy.zip"
    if not os.path.exists(zip_path):
        subprocess.run(["zip", "-r", zip_path, ".", 
            "-x", ".git/*", "cloudflared", "ngrok", "__pycache__/*", "*.pyc", "daily_report/data/*", ".gitignore"],
            cwd="/Users/tianmengpiaoxiang/auto_business")
    return send_file(zip_path, as_attachment=True, download_name="autotools_deploy.zip")

# 初始化数据目录（gunicorn 导入时执行）
init_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  AutoTools \u526f\u4e1a\u7cfb\u7edf\n  \U0001f310 \u7f51\u7ad9: http://localhost:{port}\n  \U0001f4cb \u540e\u53f0: http://localhost:{port}/admin\n  \u5bc6\u7801: {ADMIN_PASSWORD}\n")
    # In production, use: waitress-serve --port=$PORT app:app
    app.run(host="0.0.0.0", port=port, debug=False)
