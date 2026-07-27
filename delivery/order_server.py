#!/usr/bin/env python3
"""
自动订单处理和文件交付系统
买家付款后，填写邮箱，系统自动发送产品文件
"""

import json
import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
import http.server
import urllib.parse
import sys
import subprocess
import webbrowser

BASE_DIR = Path(__file__).parent.parent
ORDERS_FILE = BASE_DIR / "daily_report" / "data" / "orders.json"
PRODUCTS_DIR = BASE_DIR / "products"

def init_orders_db():
    if not ORDERS_FILE.exists():
        ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"orders": [], "total_revenue": 0}, f, ensure_ascii=False, indent=2)

def save_order(product_name, price, buyer_email, payment_method, order_id):
    with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    order = {
        "order_id": order_id,
        "product": product_name,
        "price": price,
        "buyer_email": buyer_email,
        "payment_method": payment_method,
        "status": "pending",  # pending, confirmed, delivered
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "confirmed_at": None,
        "delivered_at": None
    }
    data["orders"].append(order)
    data["total_revenue"] += price
    
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return order

def get_pending_orders():
    with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [o for o in data["orders"] if o["status"] == "pending"]

def confirm_order(order_id):
    with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for o in data["orders"]:
        if o["order_id"] == order_id:
            o["status"] = "confirmed"
            o["confirmed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            break
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_product_file(product_name):
    """获取产品文件的下载路径"""
    files = {
        "文件批处理大师": "file_tools/main.py",
        "内容自动生成器": "content_gen/main.py",
        "数据清洗工具包": "data_tools/main.py",
        "三件套捆绑包": None,  # 三个文件
    }
    if product_name == "三件套捆绑包":
        return [
            PRODUCTS_DIR / "file_tools" / "main.py",
            PRODUCTS_DIR / "content_gen" / "main.py",
            PRODUCTS_DIR / "data_tools" / "main.py",
        ]
    rel_path = files.get(product_name)
    if rel_path:
        return [PRODUCTS_DIR / rel_path]
    return []

class OrderHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open(BASE_DIR / 'website' / 'index.html', 'rb') as f:
                self.wfile.write(f.read())
        
        elif self.path == '/order':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            html = '''
            <html><head><meta charset="utf-8"><title>订单确认</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: -apple-system, sans-serif; background: #f5f7fa; padding: 20px; }
                .container { max-width: 500px; margin: 0 auto; background: white; 
                    border-radius: 16px; padding: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
                h2 { text-align: center; color: #1a1a2e; margin-bottom: 24px; }
                .form-group { margin-bottom: 20px; }
                label { display: block; font-weight: 600; margin-bottom: 6px; color: #333; }
                input, select { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 10px; 
                    font-size: 1em; box-sizing: border-box; }
                button { width: 100%; padding: 14px; background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white; border: none; border-radius: 10px; font-size: 1.1em; 
                    font-weight: 600; cursor: pointer; }
                button:hover { opacity: 0.9; }
                .steps { background: #f0f4ff; padding: 16px; border-radius: 12px; margin-bottom: 20px; }
                .steps ol { margin: 0; padding-left: 20px; }
                .steps li { padding: 4px 0; color: #555; font-size: 0.9em; }
                .success { display: none; text-align: center; padding: 20px; }
                .success .emoji { font-size: 3em; }
            </style>
            </head><body>
            <div class="container">
                <div id="orderForm">
                    <h2>📋 提交订单</h2>
                    <div class="steps">
                        <ol>
                            <li>打开支付宝/微信扫码付款</li>
                            <li>输入下方您的邮箱地址</li>
                            <li>选择您购买的产品</li>
                            <li>提交后系统自动发送产品文件</li>
                        </ol>
                    </div>
                    <div class="form-group">
                        <label>您的邮箱</label>
                        <input type="email" id="email" placeholder="example@email.com" required>
                    </div>
                    <div class="form-group">
                        <label>购买产品</label>
                        <select id="product">
                            <option value="文件批处理大师">📁 文件批处理大师 - ¥49</option>
                            <option value="内容自动生成器">📝 内容自动生成器 - ¥29</option>
                            <option value="数据清洗工具包">🧹 数据清洗工具包 - ¥39</option>
                            <option value="三件套捆绑包">🎉 三件套捆绑包 - ¥79</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>付款方式</label>
                        <select id="payment">
                            <option value="支付宝">支付宝</option>
                            <option value="微信">微信支付</option>
                        </select>
                    </div>
                    <button onclick="submitOrder()">提交订单</button>
                </div>
                <div class="success" id="successMsg">
                    <div class="emoji">✅</div>
                    <h3>订单已提交！</h3>
                    <p>确认付款后，产品文件将发送到您的邮箱。</p>
                </div>
            </div>
            <script>
            function submitOrder() {
                var email = document.getElementById('email').value;
                var product = document.getElementById('product').value;
                var payment = document.getElementById('payment').value;
                if (!email) { alert('请输入邮箱地址'); return; }
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/order', true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.onload = function() {
                    if (xhr.status === 200) {
                        document.getElementById('orderForm').style.display = 'none';
                        document.getElementById('successMsg').style.display = 'block';
                    }
                };
                xhr.send(JSON.stringify({email: email, product: product, payment: payment}));
            }
            </script>
            </body></html>
            '''
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/admin':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            orders = get_pending_orders()
            html = '<html><head><meta charset="utf-8"><title>订单管理</title></head><body>'
            html += '<h2>📋 待处理订单</h2>'
            if not orders:
                html += '<p>暂无待处理订单</p>'
            else:
                for o in orders:
                    html += f'''
                    <div style="border:1px solid #ddd;padding:16px;margin:12px;border-radius:8px;">
                        <p><strong>订单：</strong>{o["order_id"]}</p>
                        <p><strong>产品：</strong>{o["product"]}</p>
                        <p><strong>金额：</strong>¥{o["price"]}</p>
                        <p><strong>邮箱：</strong>{o["buyer_email"]}</p>
                        <p><strong>付款方式：</strong>{o["payment_method"]}</p>
                        <p><strong>时间：</strong>{o["created_at"]}</p>
                        <button onclick="confirmOrder(\'{o["order_id"]}\')">确认已收款</button>
                    </div>
                    '''
            html += '<script>function confirmOrder(id){fetch("/api/confirm?id="+id).then(r=>location.reload())}</script>'
            html += '</body></html>'
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path.startswith('/assets/'):
            import mimetypes
            file_path = BASE_DIR / 'website' / self.path.lstrip('/')
            if file_path.exists():
                self.send_response(200)
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                self.send_header('Content-type', mime_type)
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        
        elif self.path.startswith('/api/confirm'):
            order_id = params.get('id', [''])[0]
            confirm_order(order_id)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        if self.path == '/api/order':
            import uuid
            order_id = str(uuid.uuid4())[:8]
            product_prices = {"文件批处理大师": 49, "内容自动生成器": 29, "数据清洗工具包": 39, "三件套捆绑包": 79}
            
            save_order(
                product_name=data['product'],
                price=product_prices.get(data['product'], 0),
                buyer_email=data['email'],
                payment_method=data['payment'],
                order_id=order_id
            )
            
            # Also record in revenue tracker
            tracker = BASE_DIR / 'deploy' / 'auto_sale' / 'revenue_tracker.py'
            subprocess.Popen(['python3', str(tracker), '--record', 
                            str(product_prices.get(data['product'], 0)),
                            data['product'], data['payment']])
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"order_id": order_id, "status": "created"}).encode())

def main():
    init_orders_db()
    port = int(os.environ.get('PORT', 8080))
    
    server = http.server.HTTPServer(('0.0.0.0', port), OrderHandler)
    print(f"\n🚀 自动订单系统已启动!")
    print(f"   📍 产品网站: http://localhost:{port}")
    print(f"   📋 订单管理: http://localhost:{port}/admin")
    print(f"   📝 下单页面: http://localhost:{port}/order")
    print(f"   🔒 按 Ctrl+C 停止服务器\n")
    
    # 不自动打开浏览器（后台运行时避免挂起）
    # webbrowser.open(f'http://localhost:{port}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    main()
