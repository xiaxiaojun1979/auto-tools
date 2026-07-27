#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 AutoDelivery - 自动交付系统
用户付款后自动生成下载链接并发送到邮箱
"""

import json, uuid, smtplib
from pathlib import Path
from datetime import datetime, timedelta
from email.mime.text import MIMEText

BASE_DIR = Path(__file__).parent.parent
DELIVERY_DIR = BASE_DIR / "delivery"
PRODUCTS_STORAGE = DELIVERY_DIR / "files"
LINKS_FILE = DELIVERY_DIR / "download_links.json"
CONFIG_FILE = DELIVERY_DIR / "delivery_config.json"


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def load_links():
    if LINKS_FILE.exists():
        with open(LINKS_FILE) as f:
            return json.load(f)
    return {}


def save_links(links):
    with open(LINKS_FILE, 'w') as f:
        json.dump(links, f, ensure_ascii=False, indent=2)


def generate_download_link(order_id, product_id, buyer_email, expires_days=30):
    """生成唯一下载链接"""
    token = uuid.uuid4().hex[:16].upper()
    now = datetime.now()
    
    link_info = {
        "order_id": order_id,
        "product_id": product_id,
        "buyer_email": buyer_email,
        "token": token,
        "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": (now + timedelta(days=expires_days)).strftime("%Y-%m-%d %H:%M:%S"),
        "download_count": 0,
        "max_downloads": 10
    }
    
    links = load_links()
    links[token] = link_info
    save_links(links)
    
    download_url = f"http://localhost:8000/download/{token}"
    return download_url, link_info


def validate_token(token):
    """验证下载链接是否有效"""
    links = load_links()
    if token not in links:
        return None, "链接无效"
    
    info = links[token]
    now = datetime.now()
    expires = datetime.strptime(info["expires_at"], "%Y-%m-%d %H:%M:%S")
    
    if now > expires:
        return None, "链接已过期"
    
    if info["download_count"] >= info["max_downloads"]:
        return None, "下载次数已达上限"
    
    return info, None


def record_download(token):
    """记录下载次数"""
    links = load_links()
    if token in links:
        links[token]["download_count"] += 1
        save_links(links)


def get_product_downloads(product_id):
    """获取产品下载文件列表"""
    product_dir = PRODUCTS_STORAGE / product_id
    if not product_dir.exists():
        return []
    
    files = []
    for f in product_dir.iterdir():
        if f.is_file() and f.suffix != ".json":
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "path": str(f.relative_to(PRODUCTS_STORAGE))
            })
    return files


def send_delivery_email(order_id, product_name, buyer_email, download_url):
    """发送交付邮件"""
    try:
        sender = "35538112@qq.com"
        
        # Try to load SMTP config
        password = None
        config_file = BASE_DIR / "email_config.json"
        if config_file.exists():
            with open(config_file) as f:
                cfg = json.load(f)
                password = cfg.get("password")
        
        if not password:
            # Try from email_report.py
            pass
        
        if password:
            subject = f"✅ AutoTools - {product_name} 已就绪"
            body = f"""<html><body>
<h2>✅ 感谢你的购买！</h2>
<p>产品：<strong>{product_name}</strong></p>
<p>订单号：{order_id}</p>
<p>你的产品已准备就绪，点击下方链接下载：</p>
<p><a href="{download_url}" style="display:inline-block;padding:12px 24px;background:#667eea;color:white;text-decoration:none;border-radius:8px;font-size:16px">📥 立即下载</a></p>
<p>链接有效期：30天，最多下载10次</p>
<p>如有问题请联系：35538112@qq.com</p>
<hr>
<p style="color:#999">AutoTools 自动交付系统</p>
</body></html>"""
            
            msg = MIMEText(body, 'html', 'utf-8')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = buyer_email
            
            server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=15)
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, [buyer_email], msg.as_string())
            server.quit()
            return True, "邮件已发送"
        else:
            return False, "SMTP未配置"
    except Exception as e:
        return False, str(e)


def auto_deliver(order):
    """自动交付 - 付款确认后自动执行"""
    order_id = order["order_id"]
    product_id = order["product_id"]
    product_name = order["product_name"]
    buyer_email = order["buyer_email"]
    price = order["price"]
    
    config = load_config()
    
    # 生成下载链接
    download_url, link_info = generate_download_link(
        order_id, product_id, buyer_email
    )
    
    # 发送邮件
    success, msg = send_delivery_email(
        order_id, product_name, buyer_email, download_url
    )
    
    return {
        "delivered": success,
        "download_url": download_url,
        "message": msg
    }
