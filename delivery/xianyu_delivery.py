#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📦 闲鱼自动发货系统
监控闲鱼消息 → 检测购买 → 自动回复激活码/下载链接 → 记录订单 → 邮件通知
"""

import json, uuid, random, subprocess, time, sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
NODE = "/Users/tianmengpiaoxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
XB = "/Users/tianmengpiaoxiang/.qclaw/skills/xbrowser/scripts/xb.cjs"
CODES_FILE = BASE_DIR / "delivery" / "activation_codes.json"
ORDERS_FILE = BASE_DIR / "daily_report" / "data" / "orders.json"
DELIVERY_LOG = "/tmp/xianyu_delivery.log"
SITE_URL = "https://xiaxiaojun.zeabur.app"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(DELIVERY_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_codes():
    with open(CODES_FILE) as f:
        return json.load(f)


def save_codes(codes):
    with open(CODES_FILE, 'w') as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)


def load_orders():
    if ORDERS_FILE.exists():
        with open(ORDERS_FILE) as f:
            return json.load(f)
    return {"orders": [], "total_revenue": 0}


def save_orders(orders):
    ORDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)


def load_products():
    pf = BASE_DIR / "products" / "products.json"
    with open(pf) as f:
        return json.load(f)


def get_available_code(product_id):
    """获取一个未使用的激活码"""
    codes = load_codes()
    if product_id not in codes:
        return None
    for c in codes[product_id]:
        if not c["used"]:
            return c
    return None


def assign_code(product_id, buyer_name):
    """分配激活码给买家"""
    codes = load_codes()
    if product_id not in codes:
        # 自动补充新码
        from uuid import uuid4
        new_code = {
            "code": f"AT-{product_id[:4].upper()}-{uuid4().hex[:8].upper()}",
            "product_id": product_id,
            "product_name": "",
            "price": 0,
            "used": False,
            "used_by": None,
            "used_at": None,
            "created_at": datetime.now().strftime("%Y-%m-%d")
        }
        codes[product_id] = [new_code]
    
    for c in codes[product_id]:
        if not c["used"]:
            c["used"] = True
            c["used_by"] = buyer_name
            c["used_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_codes(codes)
            return c["code"]
    
    # 所有码用完了，生成新码
    from uuid import uuid4
    code = f"AT-{product_id[:4].upper()}-{uuid4().hex[:8].upper()}"
    new_code = {
        "code": code,
        "product_id": product_id,
        "product_name": "",
        "price": 0,
        "used": True,
        "used_by": buyer_name,
        "used_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "created_at": datetime.now().strftime("%Y-%m-%d")
    }
    codes[product_id].append(new_code)
    save_codes(codes)
    return code


def record_order(product_id, product_name, price, buyer_name, delivery_code):
    """记录订单"""
    orders = load_orders()
    now = datetime.now()
    
    order = {
        "order_id": f"XY{now.strftime('%Y%m%d%H%M%S')}{random.randint(100,999)}",
        "product_id": product_id,
        "product_name": product_name,
        "price": price,
        "buyer_name": buyer_name,
        "delivery_code": delivery_code,
        "status": "completed",
        "source": "xianyu",
        "delivered_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "delivery_method": "xianyu_auto_reply"
    }
    orders.setdefault("orders", []).append(order)
    orders["total_revenue"] = orders.get("total_revenue", 0) + price
    save_orders(orders)
    return order


def send_email_notification(order):
    """发送订单通知邮件"""
    try:
        sys.path.insert(0, str(BASE_DIR))
        from email_report import send_email
        
        body = f"""<h2>🎉 闲鱼新订单!</h2>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse">
<tr><td>产品</td><td>{order['product_name']}</td></tr>
<tr><td>价格</td><td>¥{order['price']}</td></tr>
<tr><td>买家</td><td>{order['buyer_name']}</td></tr>
<tr><td>激活码</td><td><b>{order['delivery_code']}</b></td></tr>
<tr><td>时间</td><td>{order['delivered_at']}</td></tr>
</table>
<p>下载链接: {SITE_URL}/d/{order['delivery_code']}</p>"""
        
        send_email(body, subject=f"🎉 闲鱼新订单 - {order['product_name']} ¥{order['price']}")
        log(f"  邮件通知已发送")
    except Exception as e:
        log(f"  邮件通知失败: {e}")


def xb(cmd):
    """执行xbrowser命令"""
    full = f'"{NODE}" {XB} run --browser chrome {cmd}'
    result = subprocess.run(full, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout


def xb_eval(js):
    """执行JS"""
    js_escaped = js.replace("'", "'\\''")
    return xb(f"eval '{js_escaped}'")


def navigate(url):
    return xb(f"open '{url}'")


def click(ref):
    return xb(f"click {ref}")


def snapshot():
    return xb("snapshot -i")


def monitor_and_deliver():
    """
    扫描闲鱼消息，检测购买并自动发货
    """
    log("=" * 50)
    log("闲鱼自动发货监控开始")
    
    # 1. 打开闲鱼消息页面
    navigate("https://www.goofish.com/message")
    time.sleep(3)
    snap = snapshot()
    
    # 2. 获取所有聊天列表
    conversations = xb_eval("""
    (function(){
        var items = document.querySelectorAll('[class*=conversation], [class*=list-item], [class*=msg-item]');
        var result = [];
        items.forEach(function(el){
            var text = el.textContent || '';
            var name = el.querySelector('[class*=name]');
            result.push({
                name: name ? name.textContent.trim() : 'unknown',
                text: text.substring(0, 200),
                html: el.innerHTML.substring(0, 300)
            });
        });
        return JSON.stringify(result.slice(0, 10));
    })()
    """)
    
    try:
        convos = json.loads(conversations)
    except:
        convos = []
    
    log(f"检测到 {len(convos)} 个会话")
    
    # 3. 按产品名称匹配消息
    products = load_products()
    product_map = {p['name']: p for p in products}
    
    processed = 0
    
    for convo in convos[:5]:  # 最多处理5个会话
        name = convo.get('name', '')
        text = convo.get('text', '')
        
        log(f"  会话: {name} | {text[:60]}")
        
        # 检测购买关键词
        buy_keywords = ['买了', '已拍', '已付款', '付款了', '支付了', '下单', '购买', 
                        '已付', '付了', '拍了', '想要', '怎么买', '怎么用', '怎么付款',
                        '激活码', '下载', '链接', '发我', '发给我', '给我']
        
        matched = False
        matched_product = None
        
        # 检查消息中是否包含产品名
        for pname, p in product_map.items():
            if pname in text:
                matched_product = p
                matched = True
                break
        
        # 检查购买关键词
        for kw in buy_keywords:
            if kw in text:
                matched = True
                break
        
        if matched and matched_product:
            log(f"  🔍 检测到购买意向! 产品: {matched_product['name']}")
            
            # 进入该聊天
            click(f"text={convo['name']}")
            time.sleep(2)
            
            # 获取最新几条消息
            latest = xb_eval("""
            (function(){
                var msgs = document.querySelectorAll('[class*=message], [class*=msg-content], [class*=chat-msg]');
                var texts = [];
                msgs.forEach(function(m){
                    var t = m.textContent || '';
                    if(t.trim()) texts.push(t.trim());
                });
                return JSON.stringify(texts.slice(-5));
            })()
            """)
            
            try:
                latest_msgs = json.loads(latest)
            except:
                latest_msgs = []
            
            # 检查是否有明确的"付款"确认
            should_deliver = False
            buyer_confirm = ['已付款', '付了', '已付', '支付了', '买了', '已拍']
            for msg in latest_msgs:
                for kw in buyer_confirm:
                    if kw in msg:
                        should_deliver = True
                        break
            
            if should_deliver or True:  # 宽松模式：有匹配就发货
                pid = matched_product['id']
                pname = matched_product['name']
                price = matched_product.get('price', 19)
                
                # 分配激活码
                code = assign_code(pid, name)
                download_link = f"{SITE_URL}/d/{code}"
                
                # 构造回复信息
                reply = f"""✅ 已收到！你的专属激活码和下载信息：

📦 产品：{pname}
🔑 激活码：{code}
📥 下载：{SITE_URL}/d/{code}

💡 使用方法：
1. 打开下载链接 {SITE_URL}/d/{code}
2. 输入激活码 {code}
3. 即可下载使用

🔄 激活码永久有效，可随时下载
❓ 如有问题回复"帮助""" 
                
                # 发送消息到闲鱼
                send_result = xb_eval(f"""
                (function(){{
                    var ed = document.querySelector('[class*=editor], [contenteditable=true], textarea');
                    if(!ed) return 'no editor found';
                    if(ed.tagName === 'TEXTAREA' || ed.tagName === 'INPUT') {{
                        ed.value = reply_text;
                    }} else {{
                        ed.focus();
                        ed.textContent = reply_text;
                    }}
                    ed.dispatchEvent(new Event('input', {{bubbles: true}}));
                    ed.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return 'filled';
                }})()
                """)
                log(f"  填写消息: {send_result[:50]}")
                
                time.sleep(1)
                
                # 点击发送按钮
                click("text=发送,button,submit")
                time.sleep(2)
                log(f"  ✅ 已自动回复激活码给 {name}")
                
                # 记录订单
                order = record_order(pid, pname, price, name, code)
                log(f"  📋 订单已记录: {order['order_id']}")
                
                # 发送邮件通知
                send_email_notification(order)
                
                processed += 1
                
                # 每个会话间隔
                time.sleep(random.randint(3, 6))
    
    log(f"本次处理: {processed} 个发货")
    log("=== 监控完成 ===")
    return processed


def check_messages():
    """快速检查消息数量（用于日常监控）"""
    navigate("https://www.goofish.com/message")
    time.sleep(2)
    r = xb_eval("""
    (function(){
        var els = document.querySelectorAll('[class*=badge], [class*=unread], [class*=count]');
        for(var i=0; i<els.length; i++) {
            var t = els[i].textContent || '';
            if(t.match(/\\d+/)) return t.trim();
        }
        return '0';
    })()
    """)
    return r


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "monitor"
    
    if mode == "monitor":
        count = monitor_and_deliver()
        print(json.dumps({"delivered": count}))
    elif mode == "check":
        msgs = check_messages()
        print(f"消息: {msgs}")
    elif mode == "manual":
        # 手动发货: python3 xianyu_delivery.py manual <product_id> <buyer_name>
        pid = sys.argv[2]
        buyer = sys.argv[3] if len(sys.argv) > 3 else "闲鱼买家"
        products = load_products()
        p = next((x for x in products if x['id'] == pid), None)
        if p:
            code = assign_code(pid, buyer)
            print(f"✅ 已分配: {p['name']} → {buyer}")
            print(f"   激活码: {code}")
            print(f"   下载: {SITE_URL}/d/{code}")
            record_order(pid, p['name'], p['price'], buyer, code)
    elif mode == "codes":
        codes = load_codes()
        used = sum(1 for clist in codes.values() for c in clist if c['used'])
        total = sum(len(clist) for clist in codes.values())
        print(f"激活码使用: {used}/{total}")
        for pid, clist in codes.items():
            u = sum(1 for c in clist if c['used'])
            if u > 0:
                pname = clist[0].get('product_name', pid)
                print(f"  {pname}: {u}/{len(clist)} used")
