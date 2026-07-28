#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 AutoTools 自动推广系统（核心引擎）
收益第一原则 - 全自动运行，无需人工干预

功能:
1. 网站内自动推广（弹窗、横幅、闪购）
2. 跨平台推广内容自动生成
3. 限时优惠自动发放
4. 推广效果追踪
5. 每日推广报告
"""

import json, random, os, threading, time
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "promotion" / "data"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
ORDERS_FILE = BASE_DIR / "daily_report" / "data" / "orders.json"
STATS_FILE = DATA_DIR / "promotion_stats.json"
SITE_URL = "https://xiaxiaojun.com"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ===== 推广配置 =====
PROMOTION_TYPES = [
    "flash_sale",    # 限时闪购
    "hot_product",   # 热销推荐
    "new_arrival",   # 新品上架
    "bundle_deal",   # 捆绑优惠
    "limited_time",  # 限时折扣
    "referral",      # 推荐有奖
    "vip_offer",     # VIP专享
]

# 推广文案模板
SLOGANS = [
    "🔥 限时特价！错过等明天！",
    "⚡ 今日闪购，手慢无！",
    "🎉 新用户专享8折优惠！",
    "💥 买二送一，限时活动中！",
    "🏆 热销爆款，大家都在买！",
    "🎯 效率翻倍，从今天开始！",
    "🚀 告别加班，就靠这个工具！",
    "💪 你的效率提升神器来了！",
    "✨ 一键搞定，省时省力！",
    "🎊 年终特惠，全年最低价！",
]

def load_products():
    try:
        with open(PRODUCTS_FILE) as f:
            return json.load(f)
    except:
        return []

def load_orders():
    try:
        with open(ORDERS_FILE) as f:
            return json.load(f)
    except:
        return {"orders": [], "total_revenue": 0}

def load_stats():
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE) as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}
    # Ensure all keys exist
    data.setdefault("total_views", 0)
    data.setdefault("total_clicks", 0)
    data.setdefault("total_promotions", 0)
    data.setdefault("promotion_revenue", 0)
    data.setdefault("daily_stats", {})
    data.setdefault("type_stats", {})
    return data

def save_stats(stats):
    try:
        STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'[WARN] save_stats failed: {e}')

def get_promotion_for_homepage():
    """
    生成首页推广数据（动态计算，每次刷新不同）
    返回: dict 包含促销信息
    """
    products = load_products()
    orders = load_orders()
    now = datetime.now()
    hour = now.hour
    
    if not products:
        return {"has_promo": False}
    
    # 1. 随机选择一个推广类型
    promo_type = random.choice(PROMOTION_TYPES)
    
    # 2. 计算限时倒计时
    # 整点开始，2小时后结束
    current_slot = (hour // 2) * 2
    end_hour = current_slot + 2
    end_time = now.replace(hour=end_hour, minute=0, second=0)
    if end_hour >= 24:
        end_time = end_time + timedelta(days=1)
        end_time = end_time.replace(hour=end_hour % 24)
    
    countdown_seconds = int((end_time - now).total_seconds())
    if countdown_seconds <= 0:
        countdown_seconds = 7200  # 默认2小时
    
    # 3. 选择推广产品
    if promo_type == "hot_product":
        # 按销量选热门
        sold_ids = {}
        for o in orders.get("orders", []):
            pid = o.get("product_id", "")
            if pid:
                sold_ids[pid] = sold_ids.get(pid, 0) + 1
        scored = sorted(products, key=lambda p: sold_ids.get(p["id"], 0), reverse=True)
        promo_products = scored[:4]
    elif promo_type == "new_arrival":
        # 选最后4个产品（假设是最新的）
        promo_products = products[-4:]
    elif promo_type == "flash_sale":
        # 随机选4个低价产品
        cheap = [p for p in products if p.get("price", 999) <= 19]
        promo_products = cheap[:4] if cheap else products[:4]
    else:
        # 随机选4个
        random.shuffle(products)
        promo_products = products[:4]
    
    # 4. 生成折扣信息
    flash_items = []
    for p in promo_products:
        price = p.get("price", 29)
        price_old = p.get("price_old", price * 2)
        if price_old <= price:
            price_old = price * 2
        
        discount_pct = int((1 - price / price_old) * 100)
        if discount_pct <= 0:
            discount_pct = random.randint(20, 50)
        
        flash_items.append({
            "id": p["id"],
            "name": p["name"],
            "emoji": p.get("emoji", "🛠️"),
            "desc": p.get("desc", "")[:40],
            "price": price,
            "price_old": price_old,
            "discount": f"-{discount_pct}%",
            "countdown": countdown_seconds,
            "features": p.get("features", [])[:2],
        })
    
    # 5. 选择slogan
    slogan = random.choice(SLOGANS)
    
    # 6. 生成底部推广语
    bottom_messages = [
        "💡 全部工具一次购买永久使用！支付宝/微信扫码支付",
        "🔥 {count}款精选工具，总有一款适合你！",
        "🎯 提升10倍工作效率，从现在开始！",
        "⚡ 已服务{count}位用户，好评如潮！",
    ]
    total_products = len(products)
    bottom = random.choice(bottom_messages).format(count=total_products)
    
    # 更新统计（安全执行）
    try:
        stats = load_stats()
        stats["total_promotions"] = stats.get("total_promotions", 0) + 1
        today = now.strftime("%Y-%m-%d")
        if today not in stats.setdefault("daily_stats", {}):
            stats["daily_stats"][today] = {"promotions": 0}
        stats["daily_stats"][today]["promotions"] = stats["daily_stats"][today].get("promotions", 0) + 1
        if promo_type not in stats.setdefault("type_stats", {}):
            stats["type_stats"][promo_type] = 0
        stats["type_stats"][promo_type] += 1
        save_stats(stats)
    except Exception as e:
        print(f"[WARN] Stats update failed: {e}")
    
    return {
        "has_promo": True,
        "type": promo_type,
        "slogan": slogan,
        "items": flash_items,
        "bottom_message": bottom,
        "countdown": countdown_seconds,
        "total_products": total_products,
        "site_url": SITE_URL,
    }

def get_share_content(product_id=None):
    """
    生成分享推广文案
    返回: dict 各平台文案
    """
    products = load_products()
    if product_id:
        product = None
        for p in products:
            if p["id"] == product_id:
                product = p
                break
    else:
        # 随机选一个
        product = random.choice(products) if products else None
    
    if not product:
        return {}
    
    name = product["name"]
    emoji = product.get("emoji", "🛠️")
    price = product["price"]
    price_old = product.get("price_old", price * 2)
    desc = product.get("desc", "")
    features = product.get("features", [])[:3]
    
    features_text = "\n".join([f"  ✅ {f}" for f in features])
    
    return {
        "朋友圈": f"{emoji} 发现一个超好用的工具「{name}」\n{desc[:50]}\n\n{features_text}\n\n💰 只要¥{price}（原价¥{price_old}）\n一次购买永久使用，终身免费更新！\n\n🔗 {SITE_URL}",
        "小红书": f"✨ 打工人必备！这个{name}也太好用了吧！\n\n💡 {desc[:60]}\n\n💰 价格：¥{price}（限时特惠）\n\n🌟 功能亮点：\n{features_text}\n\n🔗 直达链接：{SITE_URL}\n\n#效率工具 #办公必备 #自动化 #副业",
        "知乎": f"有什么实用的效率工具推荐？\n\n推荐一下最近在用的{name}，{desc[:60]}。支持{features[0] if features else '多种功能'}，价格只要¥{price}，性价比很高。\n\n链接：{SITE_URL}",
        "闲鱼": f"{emoji} {name}\n{desc[:80]}\n💰 ¥{price}（原价¥{price_old}）\n功能：{features_text}\n🔗 {SITE_URL}",
        "贴吧": f"分享一个实用的{name}，{desc[:60]}，价格只要¥{price}，需要的朋友可以看看\n{SITE_URL}",
        "B站": f"【{name}】{desc[:60]}\n价格：¥{price}\n功能：{features_text}\n链接：{SITE_URL}",
        "抖音脚本": f"🎬 开场：展示工具界面\n💡 这个{name}太实用了！\n💰 只要¥{price}\n👆 点击下方链接获取\n{SITE_URL}",
    }

def get_flash_sale():
    """
    获取当前限时闪购信息
    """
    products = load_products()
    now = datetime.now()
    
    if not products:
        return []
    
    # 每2小时轮换一组产品
    slot = (now.hour // 2) % 6
    products_per_slot = max(1, len(products) // 6)
    start = slot * products_per_slot
    end = start + products_per_slot
    slot_products = products[start:end]
    
    if not slot_products:
        slot_products = products[:4]
    if len(slot_products) > 4:
        slot_products = slot_products[:4]
    
    # 计算当前slot结束时间
    slot_end_hour = (slot + 1) * 2
    if slot_end_hour >= 24:
        slot_end_hour = 0
    end_time = now.replace(hour=slot_end_hour, minute=0, second=0)
    if end_time <= now:
        end_time = end_time + timedelta(days=1)
    
    flash = []
    for p in slot_products:
        price = p.get("price", 29)
        price_old = p.get("price_old", int(price * 1.5))
        if price_old <= price:
            price_old = price * 2
        
        flash.append({
            "id": p["id"],
            "name": p["name"],
            "emoji": p.get("emoji", "🛠️"),
            "desc": p.get("desc", "")[:60],
            "price": price,
            "price_old": price_old,
            "discount_pct": int((1 - price / price_old) * 100),
            "countdown_seconds": int((end_time - now).total_seconds()),
        })
    
    return flash

def get_bundle_deals():
    """获取捆绑优惠推荐"""
    products = load_products()
    if len(products) < 3:
        return []
    
    # 推荐最常一起买的组合
    bundles = []
    
    # 低价组合 (3个¥9的产品)
    cheap = [p for p in products if p.get("price", 999) <= 10][:3]
    if len(cheap) >= 3:
        total = sum(p["price"] for p in cheap)
        bundles.append({
            "name": "入门三件套",
            "emoji": "🎯",
            "products": [p["name"] for p in cheap],
            "original_price": total,
            "bundle_price": max(9, int(total * 0.6)),
            "savings": int(total * 0.4),
        })
    
    # 热门组合 (3个销量最高的)
    orders = load_orders()
    sold_ids = {}
    for o in orders.get("orders", []):
        pid = o.get("product_id", "")
        if pid:
            sold_ids[pid] = sold_ids.get(pid, 0) + 1
    
    scored = sorted(products, key=lambda p: sold_ids.get(p["id"], 0), reverse=True)
    top3 = scored[:3]
    if len(top3) >= 3:
        total = sum(p["price"] for p in top3)
        bundles.append({
            "name": "热门爆款组合",
            "emoji": "🏆",
            "products": [p["name"] for p in top3],
            "original_price": total,
            "bundle_price": max(19, int(total * 0.65)),
            "savings": int(total * 0.35),
        })
    
    return bundles

def get_promo_stats():
    """获取推广统计"""
    return load_stats()

def track_promo_click(promo_type):
    """追踪推广点击"""
    stats = load_stats()
    stats["total_clicks"] = stats.get("total_clicks", 0) + 1
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in stats["daily_stats"]:
        stats["daily_stats"][today] = {}
    stats["daily_stats"][today]["clicks"] = stats["daily_stats"][today].get("clicks", 0) + 1
    save_stats(stats)

def get_admin_promo_data():
    """获取管理后台推广数据"""
    products = load_products()
    orders = load_orders()
    stats = load_stats()
    
    # 计算推广ROI
    total_clicks = stats.get("total_clicks", 0)
    promo_revenue = stats.get("promotion_revenue", 0)
    roi = round(promo_revenue / max(1, total_clicks), 2) if total_clicks > 0 else 0
    
    # 按类型分析
    type_stats = stats.get("type_stats", {})
    
    # 今日数据
    today = datetime.now().strftime("%Y-%m-%d")
    today_data = stats.get("daily_stats", {}).get(today, {})
    
    # 当前闪购
    flash = get_flash_sale()
    
    # 捆绑优惠
    bundles = get_bundle_deals()
    
    return {
        "stats": stats,
        "roi": roi,
        "type_stats": type_stats,
        "today_data": today_data,
        "flash": flash,
        "bundles": bundles,
        "total_products": len(products),
        "site_url": SITE_URL,
    }

def record_order_from_promo(order_data, promo_source):
    """记录来自推广的订单"""
    stats = load_stats()
    stats["promotion_revenue"] = stats.get("promotion_revenue", 0) + order_data.get("price", 0)
    stats["total_promotions"] = stats.get("total_promotions", 0) + 1
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in stats.setdefault("daily_stats", {}):
        stats["daily_stats"][today] = {}
    stats["daily_stats"][today]["orders"] = stats["daily_stats"][today].get("orders", 0) + 1
    stats["daily_stats"][today]["revenue"] = stats["daily_stats"][today].get("revenue", 0) + order_data.get("price", 0)
    save_stats(stats)

# ===== 自动推广Scheduler =====
class PromotionScheduler:
    """自动推广调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """启动定时推广任务"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("  🚀 自动推广调度器已启动")
    
    def stop(self):
        self.running = False
    
    def _run(self):
        """后台运行循环"""
        last_hour = -1
        while self.running:
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            
            # 每小时检查一次（避免重复）
            if hour != last_hour:
                last_hour = hour
                self._do_hourly_tasks(hour)
            
            # 关键时段加强推广
            if hour in [8, 12, 18, 20, 21] and minute in [0, 30]:
                self._do_peak_promotion(hour, minute)
            
            # 检查收益目标
            if hour == 20 and minute == 0:
                self._do_evening_check()
            
            time.sleep(30)  # 每30秒检查一次
    
    def _do_hourly_tasks(self, hour):
        """每小时任务"""
        # 预热缓存
        _ = get_promotion_for_homepage()
        _ = get_flash_sale()
        print(f"  ⏰ [{hour:02d}:00] 推广数据已更新")
    
    def _do_peak_promotion(self, hour, minute):
        """高峰时段加强推广"""
        # 生成新的推广内容
        products = load_products()
        if products:
            # 轮换推广产品
            pid = products[hour % len(products)]["id"]
            content = get_share_content(pid)
            if content:
                print(f"  📢 [{hour:02d}:{minute:02d}] 高峰推广: 生成{len(content)}条文案")
    
    def _do_evening_check(self):
        """晚间检查收益"""
        orders = load_orders()
        today = datetime.now().strftime("%Y-%m-%d")
        today_orders = [o for o in orders.get("orders", []) if o.get("created_at", "").startswith(today)]
        today_rev = sum(o.get("price", 0) for o in today_orders)
        print(f"  📊 [{today}] 今日收益: ¥{today_rev} | 订单数: {len(today_orders)}")


# 全局实例
scheduler = PromotionScheduler()


# ===== 测试/CLI入口 =====
if __name__ == "__main__":
    print("=" * 50)
    print("  🚀 AutoTools 自动推广系统")
    print("=" * 50)
    
    print("\n📊 当前推广数据:")
    promo = get_promotion_for_homepage()
    if promo["has_promo"]:
        print(f"  类型: {promo['type']}")
        print(f"  标语: {promo['slogan']}")
        print(f"  产品数: {len(promo['items'])}")
        for item in promo['items']:
            print(f"    • {item['emoji']} {item['name']} ¥{item['price']} {item['discount']}")
    
    print("\n⚡ 当前闪购:")
    flash = get_flash_sale()
    for f in flash:
        print(f"  • {f['emoji']} {f['name']} ¥{f['price']} -{f['discount_pct']}%")
    
    print("\n📤 分享文案样例:")
    content = get_share_content()
    for platform, text in list(content.items())[:2]:
        print(f"\n  [{platform}]:")
        print(f"  {text[:100]}...")
    
    print("\n🏪 捆绑优惠:")
    bundles = get_bundle_deals()
    for b in bundles:
        print(f"  • {b['emoji']} {b['name']}: ¥{b['original_price']}→¥{b['bundle_price']} (省¥{b['savings']})")
    
    print("\n  ✅ 推广系统就绪")
    print(f"  🌐 网站: {SITE_URL}")
