#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 自动副业系统 - Flask Web 应用
动态加载产品列表，支持自动扩展
"""

import json, os, uuid
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify,
    redirect, url_for, session, send_from_directory, send_file
)


BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "daily_report" / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
ADMIN_PASSWORD = "xxj63858930"
ALIPAY_ACCOUNT = "15156215580"
SITE_URL = "https://xiaxiaojun.zeabur.app"
# 自动推广系统
import sys
PROMO_DIR = BASE_DIR / "promotion"
sys.path.insert(0, str(BASE_DIR))
from promotion.auto_promotion_system import (
    get_promotion_for_homepage, get_flash_sale, get_bundle_deals,
    get_share_content, get_admin_promo_data, get_promo_stats,
    track_promo_click, scheduler as promo_scheduler
)

def load_products():
    """从products.json动态加载产品列表"""
    # 尝试多个路径（兼容本地和Zeabur部署）
    possible_paths = [PRODUCTS_FILE, BASE_DIR / "products" / "products.json", Path("products") / "products.json"]
    
    for path in possible_paths:
        try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                    print(f"Loaded {len(products)} products from {path}")
                    return products
        except Exception as e:
            print(f"  Tried {path}: {e}")
    
    print("Warning: Could not load products.json, using fallback")
    # 回退到硬编码的基础产品
    return [
            {"id": "file_tools", "emoji": "📁", "name": "文件批处理大师",
             "desc": "批量重命名、格式转换、智能分类 — 一键处理成千上万文件",
             "features": ["批量重命名（支持正则/模板/序号）","智能文件分类（按类型/日期/大小）",
                          "批量格式转换（图片/文档/视频）","重复文件查找与清理","文件夹对比与同步"],
             "price": 49, "price_old": 69},
            {"id": "content_gen", "emoji": "✍️", "name": "内容自动生成器",
             "desc": "AI驱动的文案/标题/摘要生成，提升内容创作效率",
             "features": ["文章标题智能生成","SEO关键词优化建议","摘要自动提取",
                          "多平台内容适配","批量内容生产"],
             "price": 29, "price_old": 49},
            {"id": "data_tools", "emoji": "🧹", "name": "数据清洗工具包",
             "desc": "Excel/CSV数据处理利器，告别手动整理数据的烦恼",
             "features": ["智能缺失值填充","重复数据去重合并","异常值检测与修正",
                          "多表关联与合并","数据可视化报告生成"],
             "price": 39, "price_old": 59},
            {"id": "bundle", "emoji": "🎉", "name": "三件套超值捆绑包",
             "desc": "一次性拥有全部三个工具，省¥98！",
             "features": ["全部三个工具完整版","终身免费更新","专享VIP售后群"],
             "price": 79, "price_old": 177, "is_bundle": True},
        ]


def load_services():
    """从产品列表中提取服务类产品"""
    return [p for p in load_products() if p.get("category") in ("service", "subscription", "enterprise")]


PRODUCTS = []
SERVICES = []


def refresh_products():
    """刷新产品缓存"""
    global PRODUCTS, SERVICES
    PRODUCTS = load_products()
    SERVICES = load_services()


# 初始化产品
refresh_products()

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"), static_folder=str(BASE_DIR / "static"))
app.secret_key = "auto-business-sk-2026"


def init_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ORDERS_FILE.exists():
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"orders": [], "total_revenue": 0}, f, ensure_ascii=False, indent=2)


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
    promo = get_promotion_for_homepage()
    flash = get_flash_sale()
    bundles = get_bundle_deals()
    return render_template("index.html",
        products=PRODUCTS,
        alipay=ALIPAY_ACCOUNT,
        promo=promo,
        flash=flash,
        bundles=bundles,
        site_url=SITE_URL)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "密码错误"
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
        "pending": len([o for o in data["orders"] if o["status"] == "pending"]),
        "confirmed": len([o for o in data["orders"] if o["status"] == "confirmed"]),
        "delivered": len([o for o in data["orders"] if o["status"] == "delivered"]),
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
    
    # 自动交付：付款确认后发送下载链接
    try:
        from delivery.auto_delivery import auto_deliver
        for o in data["orders"]:
            if o["order_id"] == oid:
                result = auto_deliver(o)
                print(f"  📦 Auto-delivery: {result['message']}")
                if result.get("download_url"):
                    o["download_url"] = result["download_url"]
                break
    except Exception as e:
        print(f"  ⚠️ Auto-delivery failed: {e}")
    
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
            target = o
            break
    if target:
        data["total_revenue"] -= target["price"]
        data["orders"].remove(target)
    save_orders(data)
    return redirect(url_for("admin_dashboard"))


@app.route("/api/order", methods=["POST"])
def submit_order():
    try:
        req = request.json
        pid = req.get("product_id", "")
        email = req.get("email", "").strip()
        payment = req.get("payment", "支付宝")
        product = get_product(pid)
        if not email or "@" not in email:
            return jsonify({"ok": False, "msg": "请输入正确的邮箱"}), 400
        if not product:
            return jsonify({"ok": False, "msg": "产品不存在"}), 400
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
        return jsonify({"ok": True, "order_id": oid, "msg": "订单提交成功！确认收款后将发送产品到你的邮箱"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"系统错误: {str(e)}"}), 500


@app.route("/api/order/<oid>")
def query_order(oid):
    data = load_orders()
    for o in data["orders"]:
        if o["order_id"] == oid:
            return jsonify({"ok": True, "order": o})
    return jsonify({"ok": False, "msg": "订单不存在"}), 404


@app.route("/api/stats")
def get_stats():
    try:
        data = load_orders()
        ps = {}
        for p in PRODUCTS:
            s = [o for o in data["orders"] if o["product_id"] == p["id"]]
            ps[p["id"]] = {"name": p["name"], "count": len(s), "revenue": sum(o["price"] for o in s)}
        return jsonify({
            "ok": True, "total_orders": len(data["orders"]),
            "total_revenue": data["total_revenue"],
            "pending": len([o for o in data["orders"] if o["status"] == "pending"]),
            "product_sales": ps
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/assets/<path:filename>")
def serve_asset(filename):
    return send_from_directory(str(BASE_DIR / "website" / "assets"), filename)


@app.route("/admin/revenue")
@admin_required
def revenue_dashboard():
    """收益看板"""
    from revenue.tracker import RevenueTracker
    tracker = RevenueTracker()
    report = tracker.save_report()
    return render_template("revenue.html", report=report, services=SERVICES)


@app.route("/admin/promotion")
@admin_required
def view_promotion():
    return redirect(url_for("view_marketing"))


@app.route("/admin/promotion/manage")
@admin_required
def manage_promotion():
    from promotion_engine import PromotionEngine, PLATFORMS
    engine = PromotionEngine()
    summary = engine.generate_promotion_summary()
    
    posts = {}
    posts_file = BASE_DIR / "promotion" / "data" / f"posts_{datetime.now().strftime('%Y-%m-%d')}.json"
    if posts_file.exists():
        with open(posts_file) as f:
            posts = json.load(f)
    
    codes = []
    codes_file = BASE_DIR / "promotion" / "data" / "discount_codes.json"
    if codes_file.exists():
        with open(codes_file) as f:
            codes = json.load(f)
    
    return render_template("promotion.html", 
                         summary=summary, 
                         posts=posts, 
                         codes=codes,
                         platforms=PLATFORMS)


@app.route("/admin/promotion/generate", methods=["POST"])
@admin_required
def generate_promo():
    from promotion_engine import PromotionEngine
    engine = PromotionEngine()
    engine.generate_daily_posts()
    return redirect(url_for("manage_promotion"))


@app.route("/admin/promotion/discount/<pid>", methods=["POST"])
@admin_required
def create_discount(pid):
    from promotion_engine import PromotionEngine
    engine = PromotionEngine()
    engine.create_discount_code(pid, "limited_time")
    return redirect(url_for("manage_promotion"))


@app.route("/admin/marketing")
@admin_required
def view_marketing():
    """查看推广文案（自动生成）"""
    # 自动生成所有产品的推广文案
    products = load_products()
    all_posts = {}
    for p in products:
        content = get_share_content(p["id"])
        if content:
            all_posts[p["id"]] = {"name": p["name"], "emoji": p.get("emoji", ""), "platforms": content}
    
    # 也获取已有的数据
    marketing_dir = BASE_DIR / "marketing" / "data"
    existing = {}
    if marketing_dir.exists():
        files = sorted(marketing_dir.glob("posts_*.json"), reverse=True)
        if files:
            with open(files[0], 'r') as f:
                existing = json.load(f)
    
    return render_template("marketing.html", posts=all_posts, existing=existing, site_url=SITE_URL)


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
    report_dir = BASE_DIR / "daily_report" / "reports"
    return send_from_directory(str(report_dir), filename)


@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "products": len(PRODUCTS), "version": "2.0"})


@app.route("/api/products")
def api_products():
    """返回所有产品列表API"""
    return jsonify({"ok": True, "products": PRODUCTS})


@app.route("/api/products/reload", methods=["POST"])
@admin_required
def reload_products():
    """重新加载产品列表"""
    refresh_products()
    return jsonify({"ok": True, "count": len(PRODUCTS), "msg": f"已重新加载 {len(PRODUCTS)} 个产品"})


@app.route("/download/<token>")
def download_product(token):
    """产品下载页面"""
    try:
        from delivery.auto_delivery import validate_token, record_download, PRODUCTS_STORAGE
        info, error = validate_token(token)
        if not info:
            return f"<h2>❌ {error}</h2><p>请联系商家获取新链接: 35538112@qq.com</p>", 404
        
        product_id = info["product_id"]
        product_dir = PRODUCTS_STORAGE / product_id
        
        # 获取该产品的README
        readme_content = ""
        readme_file = product_dir / "README.md"
        if readme_file.exists():
            readme_content = readme_file.read_text()
        
        # 获取产品信息
        product_info = {}
        info_file = product_dir / "info.json"
        if info_file.exists():
            with open(info_file) as f:
                product_info = json.load(f)
        
        # 记录下载
        record_download(token)
        
        return render_template("download.html",
                             info=info,
                             product=product_info,
                             readme=readme_content,
                             token=token)
    except Exception as e:
        return f"<h2>❌ 系统错误</h2><p>{str(e)}</p>", 500


@app.route("/api/download/<token>/file")
def download_file(token):
    """实际文件下载"""
    try:
        from delivery.auto_delivery import validate_token, record_download, PRODUCTS_STORAGE
        info, error = validate_token(token)
        if not info:
            return jsonify({"ok": False, "msg": error}), 404
        
        product_id = info["product_id"]
        product_dir = PRODUCTS_STORAGE / product_id
        
        # 返回产品的README作为下载文件（实际中这里返回真实文件）
        record_download(token)
        
        readme_file = product_dir / "README.md"
        if readme_file.exists():
            return send_file(
                str(readme_file),
                as_attachment=True,
                download_name=f"{product_id}_使用说明.txt"
            )
        
        # 尝试打包目录
        import subprocess
        zip_path = f"/tmp/{product_id}_{token[:8]}.zip"
        subprocess.run(["zip", "-r", zip_path, "."], 
                      capture_output=True, cwd=str(product_dir))
        if os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, 
                           download_name=f"{product_id}.zip")
        
        return jsonify({"ok": False, "msg": "文件未找到"}), 404
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/download")
def download_code():
    """下载完整项目代码"""
    zip_path = "/tmp/autotools_deploy.zip"
    if not os.path.exists(zip_path):
        import subprocess
        subprocess.run(["zip", "-r", zip_path, ".",
                        "-x", ".git/*", "cloudflared", "ngrok", "__pycache__/*", "*.pyc",
                        "daily_report/data/*", ".gitignore"],
                       cwd=str(BASE_DIR))
    return send_file(zip_path, as_attachment=True, download_name="autotools_deploy.zip")


# ===== 自动推广API =====
@app.route("/api/promo/flash")
def api_flash_sale():
    """获取当前闪购"""
    return jsonify({"ok": True, "data": get_flash_sale()})

@app.route("/api/promo/share/<pid>")
def api_share_content(pid):
    """获取产品分享文案"""
    content = get_share_content(pid)
    return jsonify({"ok": True, "data": content})

@app.route("/api/promo/stats")
@admin_required
def api_promo_stats():
    """推广统计"""
    return jsonify({"ok": True, "data": get_admin_promo_data()})

@app.route("/api/promo/click", methods=["POST"])
def api_track_click():
    """追踪推广点击"""
    data = request.get_json() or {}
    track_promo_click(data.get("type", "unknown"))
    return jsonify({"ok": True})

# 初始化数据目录
init_data()

# 启动自动推广调度器（只在主进程启动）
if not os.environ.get("WERKZEUG_RUN_MAIN") and not os.environ.get("GUNICORN_CMD_ARGS"):
    promo_scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  🛠️ AutoTools 副业系统")
    print(f"  🌐 网站: http://localhost:{port}")
    print(f"  📋 后台: http://localhost:{port}/admin")
    print(f"  密码: {ADMIN_PASSWORD}")
    print(f"  产品数: {len(PRODUCTS)}")
    app.run(host="0.0.0.0", port=port, debug=False)
