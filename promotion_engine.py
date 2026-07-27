#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📢 AutoTools 推广引擎
自动生成推广内容+限时优惠+效果追踪
收益第一原则！
"""

import json, random, os
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "promotion" / "data"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
ORDERS_FILE = BASE_DIR / "daily_report" / "data" / "orders.json"

# 推广平台配置
PLATFORMS = {
    "xianyu": {
        "name": "闲鱼",
        "max_len": 500,
        "style": "简洁实用",
        "tags": ["效率工具", "办公软件", "Python工具", "自动化"]
    },
    "wechat": {
        "name": "朋友圈",
        "max_len": 200,
        "style": "亲切自然"
    },
    "xiaohongshu": {
        "name": "小红书",
        "max_len": 1000,
        "style": "种草分享",
        "tags": ["效率神器", "办公必备", "数码好物"]
    },
    "tieba": {
        "name": "贴吧",
        "max_len": 400,
        "style": "实用推荐"
    },
    "zhihu": {
        "name": "知乎",
        "max_len": 600,
        "style": "专业分享"
    },
    "douyin": {
        "name": "抖音",
        "max_len": 200,
        "style": "短视频脚本"
    }
}

# 推广话术模板
PROMOTION_ANGLES = [
    "省钱", "效率", "副业", "职场", "学生", "自媒体",
    "创业", "办公", "学习", "生活", "技术", "设计"
]

# 限时折扣配置
DISCOUNT_CONFIG = {
    "new_user": {"discount": 0.8, "label": "新人专享8折"},
    "limited_time": {"discount": 0.85, "label": "限时85折"},
    "bundle": {"discount": 0.7, "label": "捆绑包7折"},
    "vip": {"discount": 0.75, "label": "VIP会员75折"},
    "referral": {"discount": 0.9, "label": "推荐返利10%"}
}


class PromotionEngine:
    def __init__(self):
        self.products = self._load_products()
        self.orders = self._load_orders()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.stats = self._init_stats()

    def _load_products(self):
        try:
            with open(PRODUCTS_FILE) as f:
                return json.load(f)
        except:
            return []

    def _load_orders(self):
        try:
            with open(ORDERS_FILE) as f:
                return json.load(f)
        except:
            return {"orders": [], "total_revenue": 0}

    def _init_stats(self):
        """初始化推广统计"""
        stats_file = DATA_DIR / "promotion_stats.json"
        if stats_file.exists():
            with open(stats_file) as f:
                return json.load(f)
        return {
            "total_posts": 0,
            "total_clicks": 0,
            "total_orders_from_promotion": 0,
            "revenue_from_promotion": 0,
            "daily_stats": {},
            "platform_stats": {}
        }

    def _save_stats(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DATA_DIR / "promotion_stats.json", 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def _pick_hot_products(self, count=3):
        """选择热门产品推广"""
        if not self.products:
            return []
        
        # 优先选有销售记录的
        orders = self.orders.get("orders", [])
        sold_ids = {}
        for o in orders:
            pid = o.get("product_id", "")
            if pid:
                sold_ids[pid] = sold_ids.get(pid, 0) + 1
        
        # 按销量排序
        scored = []
        for p in self.products:
            score = sold_ids.get(p["id"], 0)
            # 高价值产品加权
            if p["price"] >= 199:
                score += 2
            elif p["price"] >= 99:
                score += 1
            scored.append((score, p))
        
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:count]]

    def _pick_best_angle(self, product):
        """为产品选择最佳推广角度"""
        name = product["name"]
        category = product.get("category", "")
        price = product["price"]
        
        # 根据类别选角度
        angle_map = {
            "ai": "用AI提升效率，告别重复劳动",
            "video": "短视频创作者必备工具",
            "media": "自媒体运营神器，效率翻倍",
            "office": "办公效率提升10倍的工具",
            "image": "设计师必收藏的效率工具",
            "security": "保护隐私安全，这个工具太实用了",
            "system": "电脑必备工具，免费替代付费软件",
            "web": "网络工作者必备效率工具",
            "vip": "一次付费，解锁全部工具！",
            "bundle": "超值捆绑包，省下几百块",
        }
        
        angle = angle_map.get(category, f"这个{name}太好用了")
        return angle

    def generate_product_card(self, product):
        """生成产品推广卡片（文本版）"""
        emoji = product.get("emoji", "🛠️")
        name = product["name"]
        desc = product.get("desc", "")
        price = product["price"]
        price_old = product.get("price_old", price)
        features = product.get("features", [])[:3]
        category = product.get("category", "")
        
        discount = int((1 - price/price_old) * 100) if price_old > price else 0
        
        card = f"""{emoji} 【{name}】
━━━━━━━━━━━━━━━
💡 {desc}
💰 特价 ¥{price} {'（省¥' + str(price_old-price) + '）' if discount > 0 else ''}
{'🔥 限时' + str(discount) + '%OFF' if discount > 0 else '✅ 一次购买永久使用'}
"""
        if features:
            card += "📌 核心功能：\n"
            for f in features:
                card += f"  ✅ {f}\n"
        
        card += f"\n🔗 https://xiaoxiaojun.zeabur.app\n💳 支付宝: 15156215580"
        
        return card

    def generate_platform_post(self, platform, product):
        """为指定平台生成推广文案"""
        name = product["name"]
        desc = product.get("desc", "")
        price = product["price"]
        price_old = product.get("price_old", price)
        emoji = product.get("emoji", "✨")
        features = product.get("features", [])[:3]
        category = product.get("category", "")
        discount = int((1 - price/price_old) * 100) if price_old > price else 0
        angle = self._pick_best_angle(product)
        
        plat = PLATFORMS.get(platform, {})
        plat_name = plat.get("name", platform)
        tags = plat.get("tags", [])
        
        post = f"【{name}】🔥 {angle}\n\n"
        post += f"{emoji} {desc}\n\n"
        post += f"💰 限时特价 ¥{price}（原价¥{price_old}，省¥{price_old-price}）\n"
        
        if features:
            post += f"\n✅ 功能亮点：\n"
            for f in features:
                post += f"  • {f}\n"
        
        post += f"\n💡 一次购买，永久使用，终身免费更新！"
        post += f"\n🔗 https://xiaoxiaojun.zeabur.app"
        post += f"\n💳 支持支付宝/微信支付"
        
        # 平台特定结尾
        if platform == "xiaohongshu":
            post += f"\n\n#效率神器 #办公必备 #{' '.join('#'+t for t in tags[:2])}"
        elif platform == "xianyu":
            post += f"\n\n{' '.join(tags)}"
        elif platform == "douyin":
            post = f"""【短视频脚本 - {name}】
🎬 标题：{angle}

📝 文案：
你是不是还在为{name[:6]}烦恼？
今天推荐这个神器，{desc[:30]}
价格只要¥{price}，一次购买永久使用！

👇 点击链接了解更多
https://xiaoxiaojun.zeabur.app

🎵 推荐BGM：轻快/科技感"""
        
        return post

    def generate_daily_posts(self):
        """生成每日推广内容"""
        hot_products = self._pick_hot_products(5)
        if not hot_products:
            hot_products = self.products[:5]
        
        posts = {}
        for platform in PLATFORMS:
            posts[platform] = {}
            for product in hot_products:
                posts[platform][product["id"]] = self.generate_platform_post(platform, product)
        
        # 保存
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = DATA_DIR / f"posts_{self.today}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        # 更新统计
        if self.today not in self.stats["daily_stats"]:
            self.stats["daily_stats"][self.today] = {"posts_generated": 0}
        self.stats["daily_stats"][self.today]["posts_generated"] = len(hot_products) * len(PLATFORMS)
        self.stats["total_posts"] += len(hot_products) * len(PLATFORMS)
        self._save_stats()
        
        return posts, hot_products

    def create_discount_code(self, product_id, discount_type="limited_time"):
        """创建限时优惠码"""
        if discount_type not in DISCOUNT_CONFIG:
            discount_type = "limited_time"
        
        config = DISCOUNT_CONFIG[discount_type]
        product = None
        for p in self.products:
            if p["id"] == product_id:
                product = p
                break
        
        if not product:
            return None
        
        # 生成优惠码
        code = f"AUTO{datetime.now().strftime('%m%d')}{random.randint(100,999)}"
        
        discount_info = {
            "code": code,
            "product_id": product_id,
            "product_name": product["name"],
            "original_price": product["price"],
            "discounted_price": round(product["price"] * config["discount"]),
            "discount_label": config["label"],
            "type": discount_type,
            "created": self.today,
            "expires": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "used": False
        }
        
        # 保存优惠码
        codes_file = DATA_DIR / "discount_codes.json"
        codes = []
        if codes_file.exists():
            with open(codes_file) as f:
                codes = json.load(f)
        codes.append(discount_info)
        with open(codes_file, 'w', encoding='utf-8') as f:
            json.dump(codes, f, ensure_ascii=False, indent=2)
        
        return discount_info

    def generate_promotion_summary(self):
        """生成推广总结"""
        posts, hot = self.generate_daily_posts()
        
        # 创建限时优惠
        discounts = []
        for p in hot[:3]:
            discount = self.create_discount_code(p["id"], "limited_time")
            if discount:
                discounts.append(discount)
        
        return {
            "date": self.today,
            "hot_products": [{"name": p["name"], "price": p["price"]} for p in hot],
            "platforms": list(PLATFORMS.keys()),
            "total_posts": len(PLATFORMS) * len(hot),
            "discounts": discounts,
            "stats": self.stats
        }

    def print_summary(self):
        """打印推广摘要"""
        summary = self.generate_promotion_summary()
        
        print(f"\n{'='*50}")
        print(f"  📢 AutoTools 推广引擎")
        print(f"  📅 {self.today}")
        print(f"{'='*50}\n")
        
        print(f"  🔥 今日推广产品 ({len(summary['hot_products'])}个):")
        for p in summary['hot_products']:
            print(f"    • {p['name']} (¥{p['price']})")
        
        print(f"\n  📱 覆盖平台 ({len(summary['platforms'])}个):")
        for p in summary['platforms']:
            print(f"    • {PLATFORMS[p]['name']}")
        
        print(f"\n  🎫 限时优惠: {len(summary['discounts'])}个")
        for d in summary['discounts']:
            print(f"    • {d['code']}: {d['product_name']} ¥{d['original_price']}→¥{d['discounted_price']}")
        
        print(f"\n  📊 累计推广: {summary['stats']['total_posts']} 条内容")
        print(f"\n  💡 推广建议:")
        print(f"    1. 闲鱼每天发1-2条，用不同角度")
        print(f"    2. 朋友圈分享客户好评+使用效果")
        print(f"    3. 小红书发工具教程类内容引流")
        print(f"    4. 知乎回答相关问题植入产品")
        print(f"    5. 使用限时优惠码提升转化率")
        
        print(f"\n{'='*50}\n")
        return summary


def run():
    engine = PromotionEngine()
    return engine.print_summary()


if __name__ == "__main__":
    run()
