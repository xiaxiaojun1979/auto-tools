#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 自动副业系统 - Flask Web 应用
动态加载产品列表，支持自动扩展
"""

import json, os, uuid, io, base64, qrcode, hashlib, hmac, time as time_module
import random
from datetime import datetime, timedelta
from pathlib import Path
from pathlib import Path
from functools import wraps
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
SITE_URL = "http://118.31.4.27"
ALIPAY_QR_URL = "alipays://platformapi/startapp?appId=20000123&actionType=toAccount&goBack=NO&source=qr&account="
SITE_NAME = "AutoTools 自动化工具集"

def generate_alipay_qr(amount, order_id):
    """生成支付宝支付二维码（含金额）"""
    try:
        # Alipay deep link with amount
        pay_url = f"{ALIPAY_QR_URL}{ALIPAY_ACCOUNT}&amount={amount}"
        # Add order reference
        pay_url += f"&memo=AutoTools-{order_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(pay_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{img_b64}"
    except Exception as e:
        print(f"  ⚠️ QR generation error: {e}")
        return None

def generate_wechat_qr(amount, order_id):
    """生成微信支付二维码"""
    try:
        pay_url = f"wxp://{ALIPAY_ACCOUNT}?amount={amount}&memo=AutoTools-{order_id}"
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(pay_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{img_b64}"
    except Exception as e:
        print(f"  ⚠️ WeChat QR error: {e}")
        return None

def auto_deliver_activation_code(product_id, product_name, buyer_email, price):
    """自动分配激活码并返回交付信息"""
    try:
        codes_file = BASE_DIR / "delivery" / "activation_codes.json"
        if not codes_file.exists():
            return None, "交付系统未初始化"
        
        with open(codes_file) as f:
            all_codes = json.load(f)
        
        # Find unused code for this product
        if product_id in all_codes:
            for c in all_codes[product_id]:
                if not c.get("used"):
                    c["used"] = True
                    c["used_by"] = buyer_email
                    c["used_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Save back
                    with open(codes_file, 'w') as f:
                        json.dump(all_codes, f, ensure_ascii=False, indent=2)
                    
                    download_url = f"{SITE_URL}/download/{c['code']}"
                    return {
                        "code": c["code"],
                        "download_url": download_url,
                        "product_name": product_name
                    }, None
        
        # No unused code, generate one on the fly
        import uuid
        new_code = f"AT-{product_id[:4].upper()}-{uuid.uuid4().hex[:8].upper()}"
        
        if product_id not in all_codes:
            all_codes[product_id] = []
        
        all_codes[product_id].append({
            "code": new_code,
            "product_id": product_id,
            "product_name": product_name,
            "price": price,
            "used": True,
            "used_by": buyer_email,
            "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": datetime.now().strftime("%Y-%m-%d")
        })
        
        with open(codes_file, 'w') as f:
            json.dump(all_codes, f, ensure_ascii=False, indent=2)
        
        download_url = f"{SITE_URL}/download/{new_code}"
        return {"code": new_code, "download_url": download_url, "product_name": product_name}, None
    except Exception as e:
        return None, str(e)

# ========== 支付校验码临时存储（付款后生成）==========
PENDING_VERIFICATIONS = {}

def generate_verify_code():
    """生成4位随机数字校验码"""
    return f"{random.randint(0, 9999):04d}"

# 支付网关
import sys
sys.path.insert(0, str(BASE_DIR))
import payment_gateway as pg
import alipay_payment as ap

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


def safe_call(func, fallback=None):
    """安全调用函数，失败时返回fallback"""
    try:
        return func()
    except Exception as e:
        print(f"[WARN] Function {func.__name__} failed: {e}")
        return fallback

@app.route("/")
def index():
    promo = safe_call(get_promotion_for_homepage, {"has_promo": False})
    flash = safe_call(get_flash_sale, [])
    if not flash:
        from datetime import datetime, timedelta
        flash = [{
            "id": "file_tools", "name": "文件批处理大师",
            "emoji": "📂", "desc": "批量重命名/格式转换/内容处理",
            "price": 19, "price_old": 38, "discount_pct": 50,
            "countdown_seconds": int((datetime.now() + timedelta(hours=2)).timestamp() - datetime.now().timestamp())
        }]
    bundles = safe_call(get_bundle_deals, [])
    return render_template("index.html",
        products=PRODUCTS,
        alipay=ALIPAY_ACCOUNT,
        promo=promo,
        flash=flash,
        bundles=bundles,
        site_url=SITE_URL)





@app.route("/xianyu")
def xianyu_publish():
    return render_template("xianyu_publish.html")


@app.route("/api/xianyu/products")
def api_xianyu_products():
    """返回闲鱼发布用的产品数据"""
    products = load_products()
    # Filter out services and high-price items
    xianyu_items = []
    for p in products:
        price = p.get("price", 0)
        cat = p.get("category", "")
        # Skip enterprise services
        if cat in ("enterprise", "service", "subscription"):
            if price > 200:
                continue
        xianyu_items.append({
            "id": p["id"],
            "name": p["name"],
            "price": price,
            "original_price": p.get("original_price", price),
            "emoji": p.get("emoji", "📦"),
            "desc": p.get("desc", ""),
            "features": p.get("features", []),
            "category": cat,
            "download_url": f"http://118.31.4.27/buy/{p['id']}"
        })
    return jsonify({"ok": True, "products": xianyu_items})

@app.route("/product/<pid>")
def product_detail(pid):
    p = get_product(pid)
    if not p:
        return "产品不存在", 404
    return render_template("product.html", product=p)


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


@app.route("/api/payment/qrcode", methods=["POST"])
def get_payment_qrcode():
    """生成支付二维码（自动选择支付网关或手动转账）"""
    try:
        req = request.get_json()
        pid = req.get("product_id", "")
        payment = req.get("payment", "alipay")
        product = get_product(pid)
        if not product:
            return jsonify({"ok": False, "msg": "产品不存在"}), 400
        
        amount = product["price"]
        order_id = gen_order_id()
        
        # 检查是否配置了支付宝当面付
        alipay_cfg = ap.load_config()
        if alipay_cfg.get("configured"):
            # 使用支付宝当面付
            result = ap.create_qrcode(amount, order_id, subject=product["name"])
            if result.get("ok"):
                # 存入待支付记录
                PENDING_VERIFICATIONS[order_id] = {
                    "product_id": pid,
                    "payment": "alipay",
                    "amount": amount,
                    "created_at": datetime.now(),
                    "status": "pending"
                }
                return jsonify({
                    "ok": True,
                    "qr": result["qrcode"],
                    "amount": amount,
                    "order_id": order_id,
                    "product_name": product["name"],
                    "gateway": "alipay_f2f",
                    "account": "支付宝当面付"
                })
            print(f"  ⚠️ 支付宝当面付失败: {result.get('msg')}")
        
        # 检查是否配置了PayJS支付网关
        gw_config = pg.load_config()
        if gw_config.get("gateway") == "payjs" and gw_config.get("payjs_mchid"):
            result = pg.create_native_qrcode(amount, order_id, attach=pid)
            if result.get("ok"):
                return jsonify({
                    "ok": True,
                    "qr": result["qrcode_url"],
                    "amount": amount,
                    "order_id": order_id,
                    "payjs_order_id": result["payjs_order_id"],
                    "product_name": product["name"],
                    "gateway": "payjs",
                    "account": "PayJS支付"
                })
            print(f"  ⚠️ PayJS创建订单失败: {result.get('msg')}")
        
        # 手动转账模式
        if payment == "alipay":
            qr = generate_alipay_qr(amount, order_id)
        else:
            qr = generate_wechat_qr(amount, order_id)
        
        if not qr:
            return jsonify({"ok": False, "msg": "二维码生成失败"}), 500
        
        return jsonify({
            "ok": True,
            "qr": qr,
            "amount": amount,
            "order_id": order_id,
            "product_name": product["name"],
            "gateway": "manual",
            "account": ALIPAY_ACCOUNT if payment == "alipay" else "微信扫码"
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": f"系统错误: {str(e)}"}), 500


@app.route("/api/order", methods=["POST"])
def submit_order():
    """验证校验码后创建订单并发送软件"""
    try:
        req = request.get_json()
        pid = req.get("product_id", "")
        email = req.get("email", "").strip()
        payment = req.get("payment", "支付宝")
        verify_code = req.get("verify_code", "").strip()
        product = get_product(pid)
        
        if not email or "@" not in email:
            return jsonify({"ok": False, "msg": "请输入正确的邮箱"}), 400
        if not product:
            return jsonify({"ok": False, "msg": "产品不存在"}), 400
        if not verify_code or len(verify_code) != 4 or not verify_code.isdigit():
            return jsonify({"ok": False, "msg": "校验码必须是4位数字"}), 400
        
        # 验证校验码：必须是付款后系统生成的
        found_order_id = None
        for oid, pend in list(PENDING_VERIFICATIONS.items()):
            if pend["code"] == verify_code and pend["product_id"] == pid and not pend.get("used", False):
                found_order_id = oid
                break
        
        if not found_order_id:
            return jsonify({"ok": False, "msg": "❌ 校验码无效或已过期，请联系客服"}), 400
        
        # 防滥用：同一邮箱每天最多3个产品
        data = load_orders()
        today = datetime.now().strftime("%Y-%m-%d")
        today_orders = [o for o in data["orders"] 
                       if o.get("buyer_email") == email and o["created_at"].startswith(today)]
        if len(today_orders) >= 3:
            return jsonify({"ok": False, "msg": "每个邮箱每天最多购买3个产品"}), 429
        
        # 防滥用：同一IP每天最多5次
        ip = request.remote_addr or "unknown"
        ip_orders = [o for o in data["orders"] 
                    if o.get("buyer_ip") == ip and o["created_at"].startswith(today)]
        if len(ip_orders) >= 5:
            return jsonify({"ok": False, "msg": "操作太频繁"}), 429
        
        # 存储交易号并标记已使用
        PENDING_VERIFICATIONS[found_order_id]["used"] = True
        PENDING_VERIFICATIONS[found_order_id]["email"] = email
        
        oid = gen_order_id()
        
        delivery_info, error = auto_deliver_activation_code(
            pid, product["name"], email, product["price"]
        )
        
        if error:
            return jsonify({"ok": False, "msg": f"交付失败: {error}"}), 500
        
        order = {
            "order_id": oid, "product_id": pid,
            "product_name": product["name"], "price": product["price"],
            "buyer_email": email, "payment": payment,
            "verify_code": verify_code,
            "buyer_ip": ip,
            "status": "delivered",
            "verified": True,
            "delivery_code": delivery_info["code"],
            "download_url": delivery_info["download_url"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "confirmed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "delivered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data["orders"].append(order)
        data["total_revenue"] += product["price"]
        save_orders(data)
        
        # 发送邮件
        try:
            from email_report import send_order_email
            send_order_email(oid, email, product["name"], delivery_info["code"], delivery_info["download_url"])
        except Exception as email_err:
            print(f"  ⚠️ 邮件发送失败: {email_err}")
        
        return jsonify({
            "ok": True,
            "order_id": oid,
            "verify_code": verify_code,
            "delivery_code": delivery_info["code"],
            "download_url": delivery_info["download_url"],
            "product_name": product["name"],
            "msg": "🎉 验证成功！邮件已发送到你的邮箱"
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": f"系统错误: {str(e)}"}), 500


@app.route("/api/order/pay-confirm", methods=["POST"])
def pay_confirm():
    """付款后生成4位数字校验码（无需交易号，信任模式）"""
    try:
        req = request.get_json()
        pid = req.get("product_id", "")
        payment = req.get("payment", "alipay")
        product = get_product(pid)
        
        if not product:
            return jsonify({"ok": False, "msg": "产品不存在"}), 400
        
        # 防滥用：同一IP每分钟最多5次
        ip = request.remote_addr or "unknown"
        now = datetime.now()
        recent_count = sum(
            1 for p in PENDING_VERIFICATIONS.values()
            if p.get("ip") == ip and (now - p.get("created_at", now)).total_seconds() < 120
        )
        if recent_count >= 5:
            return jsonify({"ok": False, "msg": "操作太频繁，请稍后再试"}), 429
        
        # 生成4位随机校验码
        code = generate_verify_code()
        order_id = gen_order_id()
        
        PENDING_VERIFICATIONS[order_id] = {
            "code": code,
            "product_id": pid,
            "payment": payment,
            "ip": ip,
            "created_at": now,
            "email": None,
            "used": False
        }
        
        # 清理超过30分钟的过期校验码
        expired = [oid for oid, pend in list(PENDING_VERIFICATIONS.items())
                   if (now - pend.get("created_at", now)).total_seconds() > 1800]
        for oid in expired:
            del PENDING_VERIFICATIONS[oid]
        
        print(f"\n  💳 校验码已生成: {code} (产品: {product['name']}, IP: {ip})")
        
        return jsonify({
            "ok": True,
            "verify_code": code,
            "order_id": order_id,
            "product_name": product["name"],
            "amount": product["price"],
            "msg": "✅ 支付成功！请使用校验码获取产品"
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "msg": f"系统错误: {str(e)}"}), 500


@app.route("/api/order/<oid>")
def query_order(oid):
    data = load_orders()
    for o in data["orders"]:
        if o["order_id"] == oid:
            return jsonify({"ok": True, "order": o})
    return jsonify({"ok": False, "msg": "订单不存在"}), 404



@app.route("/api/alipay/notify", methods=["POST"])
def alipay_notify():
    """支付宝支付异步通知"""
    try:
        data = request.form.to_dict()
        print(f"  📩 支付宝通知: {json.dumps(data, ensure_ascii=False)}")
        
        if ap.verify_notify(data):
            out_trade_no = data.get("out_trade_no", "")
            trade_no = data.get("trade_no", "")
            trade_status = data.get("trade_status", "")
            
            if trade_status == "TRADE_SUCCESS":
                # 支付成功，生成校验码
                if out_trade_no in PENDING_VERIFICATIONS:
                    code = generate_verify_code()
                    pid = PENDING_VERIFICATIONS[out_trade_no]["product_id"]
                    PENDING_VERIFICATIONS[out_trade_no]["code"] = code
                    PENDING_VERIFICATIONS[out_trade_no]["paid"] = True
                    PENDING_VERIFICATIONS[out_trade_no]["tx_id"] = trade_no
                    print(f"  ✅ 支付宝支付成功: {out_trade_no} 校验码={code}")
                
                return "success", 200
            return "fail", 400
        else:
            print(f"  ⚠️ 支付宝通知验签失败")
            return "fail", 400
    except Exception as e:
        print(f"  ⚠️ 支付宝通知处理异常: {e}")
        return "fail", 400


@app.route("/api/payment/check/<order_id>")
def check_payment(order_id):
    """轮询查询支付状态"""
    try:
        # 先检查是否有Alipay当面付记录
        pend = PENDING_VERIFICATIONS.get(order_id)
        if pend and pend.get("paid"):
            code = pend.get("code")
            return jsonify({
                "ok": True, "status": "paid",
                "verify_code": code,
                "msg": "支付成功！校验码已生成"
            })
        
        # 查询支付宝
        result = ap.query_payment(order_id)
        if result.get("ok") and result.get("paid"):
            if pend:
                code = generate_verify_code()
                pend["code"] = code
                pend["paid"] = True
                pend["tx_id"] = result.get("trade_no", "")
                return jsonify({
                    "ok": True, "status": "paid",
                    "verify_code": code,
                    "msg": "支付成功！校验码已生成"
                })
            return jsonify({"ok": True, "status": "paid", "msg": "已支付"})
        
        return jsonify({"ok": True, "status": "unpaid", "msg": "等待支付"})
    except Exception as e:
        return jsonify({"ok": False, "status": "error", "msg": str(e)}), 500


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



@app.route("/admin/revoke/<oid>", methods=["POST"])
@admin_required
def revoke_order(oid):
    """作废订单和激活码（用于未收到付款的订单）"""
    try:
        data = load_orders()
        for o in data["orders"]:
            if o["order_id"] == oid:
                # Mark as revoked
                o["status"] = "revoked"
                o["revoked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # We could also mark the activation code as usable again
                save_orders(data)
                return jsonify({"ok": True, "msg": f"订单 {oid} 已作废"})
        return jsonify({"ok": False, "msg": "订单不存在"}), 404
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/admin/orders/unverified")
@admin_required
def unverified_orders():
    """查看未验证交易号的订单"""
    data = load_orders()
    unverified = [o for o in reversed(data["orders"]) if not o.get("verified")]
    return jsonify({"ok": True, "orders": unverified, "count": len(unverified)})


@app.route("/api/delivery/send-email", methods=["POST"])
def verify_and_send_email():
    """验证校验码并发送交付邮件（备用入口）"""
    try:
        req = request.get_json()
        order_id = req.get("order_id", "")
        email = req.get("email", "").strip()
        verify_code = req.get("verify_code", "").strip()
        
        if not order_id or not email:
            return jsonify({"ok": False, "msg": "参数不完整"}), 400
        
        # Find the order
        data = load_orders()
        order = None
        for o in data["orders"]:
            if o["order_id"] == order_id:
                order = o
                break
        
        if not order:
            return jsonify({"ok": False, "msg": "订单不存在"}), 404
        
        # 验证校验码
        stored_vc = order.get("verify_code", "")
        if not stored_vc:
            return jsonify({"ok": False, "msg": "订单状态异常，请联系客服"}), 400
        
        if verify_code != stored_vc:
            return jsonify({"ok": False, "msg": "❌ 校验码不正确"}), 400
        
        # Mark as verified
        order["verified"] = True
        order["verified_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_orders(data)
        
        # Send email
        try:
            from email_report import send_order_email
            send_order_email(
                order_id, 
                email, 
                order["product_name"], 
                order["delivery_code"], 
                order["download_url"]
            )
        except Exception as email_err:
            print(f"  ⚠️ 邮件发送失败: {email_err}")
            return jsonify({
                "ok": True, "msg": "✅ 验证成功！邮件发送失败，请直接使用下载链接",
                "product_name": order["product_name"],
                "delivery_code": order["delivery_code"],
                "download_url": order["download_url"]
            })
        
        return jsonify({
            "ok": True,
            "product_name": order["product_name"],
            "delivery_code": order["delivery_code"],
            "download_url": order["download_url"],
            "msg": "✅ 验证成功！邮件已发送到你的邮箱"
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500

COMMIT_HASH = "27197a4"  # fix(zeabur): add error handling

@app.route("/buy/<pid>")
def buy_page(pid):
    product = get_product(pid)
    if not product:
        return "产品不存在", 404
    return render_template("buy.html", 
        pid=product["id"],
        name=product["name"], 
        price=product["price"],
        emoji=product.get("emoji", "📦"),
        alipay=ALIPAY_ACCOUNT,
        site_url=SITE_URL)

@app.route("/free", strict_slashes=False)
@app.route("/free/")
@app.route("/free/<tool_id>")
def free_tools(tool_id=None):
    """免费Web工具页面"""
    if tool_id:
        # Find the tool
        tool = get_product(tool_id)
        if not tool or not tool.get('has_free'):
            return render_template("free.html", tool=None, products=[p for p in PRODUCTS if p.get('has_free')], alipay=ALIPAY_ACCOUNT, site_url=SITE_URL)
        
        # Special interactive demo for file batch processor
        if tool_id == 'file_tools':
            return render_template("free_file_tools.html", tool=tool, products=PRODUCTS, alipay=ALIPAY_ACCOUNT, site_url=SITE_URL)
        
        return render_template("free.html", tool=tool, products=PRODUCTS, alipay=ALIPAY_ACCOUNT, site_url=SITE_URL)
    # List all free tools
    free_prods = [p for p in PRODUCTS if p.get('has_free')]
    return render_template("free.html", tool=None, products=free_prods, alipay=ALIPAY_ACCOUNT, site_url=SITE_URL)


@app.route("/api/track/conversion", methods=["POST"])
def track_conversion():
    """跟踪免费试用→购买转化"""
    try:
        data = request.get_json()
        if data:
            log_file = BASE_DIR / "daily_report" / "data" / "conversion_tracking.jsonl"
            with open(log_file, "a") as f:
                data["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return jsonify({"ok": True})
    except:
        return jsonify({"ok": False})


@app.route("/api/payment/check/<order_id>")
def check_payment_status(order_id):
    """查询支付状态（前端轮询用）"""
    try:
        config = pg.load_config()
        if config.get("gateway") == "payjs":
            # 从PENDING_VERIFICATIONS获取payjs_order_id
            from app import PENDING_VERIFICATIONS
            pend = PENDING_VERIFICATIONS.get(order_id)
            if pend and pend.get("payjs_order_id"):
                result = pg.check_payment(pend["payjs_order_id"])
                if result.get("ok") and result.get("paid"):
                    return jsonify({"ok": True, "status": "paid"})
                elif result.get("ok"):
                    return jsonify({"ok": True, "status": "unpaid"})
        return jsonify({"ok": True, "status": "unknown"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})

@app.route("/api/payment/notify", methods=["POST"])
def payment_notify():
    """PayJS支付通知回调"""
    try:
        data = request.form.to_dict()
        config = pg.load_config()
        if not data.get("sign"):
            return "fail"
        # 验证签名
        sign = data.pop("sign", "")
        expected = pg.get_sign(data, config.get("payjs_key", ""))
        if sign.upper() != expected:
            return "sign error"
        # 处理支付成功
        out_trade_no = data.get("out_trade_no", "")
        payjs_order_id = data.get("payjs_order_id", "")
        total_fee = data.get("total_fee", "0")
        
        print(f"  ✅ 支付通知: 订单={out_trade_no}, PayJS订单={payjs_order_id}, 金额={total_fee}")
        
        # 更新PENDING_VERIFICATIONS中的支付状态
        if out_trade_no in PENDING_VERIFICATIONS:
            PENDING_VERIFICATIONS[out_trade_no]["payjs_order_id"] = payjs_order_id
            PENDING_VERIFICATIONS[out_trade_no]["paid"] = True
        
        return "success"
    except Exception as e:
        print(f"  ⚠️ 支付通知处理异常: {e}")
        return "fail"

@app.route("/health")
def health_check():
    return jsonify({"status": "ok", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "products": len(PRODUCTS), "version": COMMIT_HASH, "commit": COMMIT_HASH})


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


# ===== 平台发布管理API =====
@app.route("/admin/conversion")
@admin_required
def admin_conversion():
    """免费工具转化数据看板"""
    log_file = BASE_DIR / "daily_report" / "data" / "conversion_tracking.jsonl"
    events = []
    if log_file.exists():
        with open(log_file) as f:
            for line in f:
                try:
                    events.append(json.loads(line.strip()))
                except:
                    pass
    
    # Stats
    total_free_uses = len(events)
    total_buy_clicks = sum(1 for e in events if e.get('event') == 'free_to_buy')
    rate = round(total_buy_clicks / total_free_uses * 100, 1) if total_free_uses > 0 else 0
    
    return jsonify({
        "total_free_uses": total_free_uses,
        "total_buy_clicks": total_buy_clicks,
        "conversion_rate": rate,
        "events": events[-100:]  # Last 100 events
    })


@app.route("/admin/publishing")
@admin_required
def admin_publishing():
    """发布管理看板"""
    try:
        from platform_publisher import get_publish_stats, get_publish_history, generate_toutiao_article, generate_baijiahao_article
        stats = get_publish_stats()
        history = get_publish_history(7)
        return render_template("publishing.html", stats=stats, history=history)
    except Exception as e:
        return render_template("publishing.html", 
                             stats={"total_publish": 0, "success": 0, "failed": 0, 
                                   "toutiao_published": 0, "baijiahao_published": 0, "last_publish": "无"},
                             history=[], error=str(e))


@app.route("/admin/publishing/publish", methods=["POST"])
@admin_required
def trigger_publish():
    """手动触发平台发布（仅文章生成，不打开浏览器）"""
    try:
        from platform_publisher import generate_toutiao_article, generate_baijiahao_article, save_article
        
        toutiao = generate_toutiao_article()
        save_article(toutiao, "toutiao")
        
        baijiahao = generate_baijiahao_article()
        save_article(baijiahao, "baijiahao")
        
        return jsonify({
            "ok": True,
            "toutiao": toutiao["title"],
            "baijiahao": baijiahao["title"],
            "msg": "文章已生成，晚上20:00自动发布将自动执行"
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@app.route("/admin/publishing/latest")
@admin_required
def get_latest_articles():
    """获取最新生成的文章"""
    try:
        from platform_publisher import load_latest_article
        toutiao = load_latest_article("toutiao")
        baijiahao = load_latest_article("baijiahao")
        return jsonify({
            "ok": True,
            "toutiao": toutiao,
            "baijiahao": baijiahao
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500



# ========== 闲鱼激活码交付系统 ==========

@app.route("/d")
@app.route("/d/<code>")
def delivery_page(code=None):
    """闲鱼激活码交付页面"""
    return render_template("delivery.html", code=code)


@app.route("/api/delivery/redeem", methods=["POST"])
def redeem_code():
    """验证激活码并返回下载信息"""
    try:
        data = request.get_json()
        code = data.get("code", "").strip().upper()
        
        # 读取激活码库
        codes_file = BASE_DIR / "delivery" / "activation_codes.json"
        if not codes_file.exists():
            return jsonify({"ok": False, "msg": "交付系统未初始化"})
        
        with open(codes_file) as f:
            all_codes = json.load(f)
        
        # 查找激活码
        found = None
        for pid, clist in all_codes.items():
            for c in clist:
                if c["code"] == code:
                    found = c
                    found["pid"] = pid
                    break
            if found:
                break
        
        if not found:
            return jsonify({"ok": False, "msg": "激活码无效，请检查输入"})
        
        if not found.get("used"):
            return jsonify({"ok": False, "msg": "该激活码尚未激活，请先在闲鱼完成购买"})
        
        # 获取产品信息
        products = load_products()
        product = next((p for p in products if p["id"] == found["pid"]), None)
        pname = product["name"] if product else found.get("product_name", "产品")
        emoji = product.get("emoji", "\U0001f4e6") if product else "\U0001f4e6"
        
        download_url = f"{SITE_URL}/download/{code}"
        
        # 记录到订单系统
        from datetime import datetime
        orders = load_orders()
        already_recorded = any(o.get("delivery_code") == code for o in orders.get("orders", []))
        if not already_recorded:
            now = dt.now()
            order = {
                "order_id": f"XY{now.strftime('%Y%m%d%H%M%S')}",
                "product_id": found["pid"],
                "product_name": pname,
                "price": product["price"] if product else 19,
                "delivery_code": code,
                "status": "completed",
                "source": "xianyu",
                "verified_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }
            orders.setdefault("orders", []).append(order)
            save_orders(orders)
        
        return jsonify({
            "ok": True,
            "product_name": f"{emoji} {pname}",
            "download_url": download_url,
            "code": code
        })
        
    except Exception as e:
        return jsonify({"ok": False, "msg": f"系统错误: {str(e)}"}), 500


@app.route("/api/delivery/download", methods=["POST"])
def record_delivery_download():
    """记录下载"""
    try:
        from datetime import datetime as dt
        data = request.get_json()
        code = data.get("code", "")
        log_file = BASE_DIR / "daily_report" / "data" / "downloads.log"
        with open(log_file, "a") as f:
            f.write(f"{dt.now().isoformat()} CODE:{code}\n")
        return jsonify({"ok": True})
    except:
        return jsonify({"ok": False})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"\n  🛠️ AutoTools 副业系统")
    print(f"  🌐 网站: http://localhost:{port}")
    print(f"  📋 后台: http://localhost:{port}/admin")
    print(f"  密码: {ADMIN_PASSWORD}")
    print(f"  产品数: {len(PRODUCTS)}")
    app.run(host="0.0.0.0", port=port, debug=False)

