#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 AutoPromotion - 自动推广引擎
网站内自动推广 + 跨平台推广任务 + 分享裂变
收益第一原则！
"""

import json, random, os
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "promotion" / "data"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
ORDERS_FILE = BASE_DIR / "daily_report" / "data" / "orders.json"

DAYS_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# 推广时段（根据用户活跃度）
PROMO_SLOTS = [
    ("07:30", "08:30", "早上通勤", "high"),
    ("11:30", "13:00", "午休时间", "high"),
    ("17:30", "19:00", "下班通勤", "high"),
    ("20:00", "22:00", "晚间黄金档", "peak"),
    ("12:00", "13:00", "午间刷手机", "medium"),
    ("15:00", "16:00", "下午摸鱼", "medium"),
    ("22:00", "23:00", "睡前刷手机", "medium"),
]

# 推广平台配置
PROMO_PLATFORMS = {
    "xianyu": {
        "name": "闲鱼",
        "type": "marketplace",
        "best_time": "20:00-22:00",
        "content_type": "商品描述",
        "daily_limit": 3,
        "tags": ["效率工具", "办公软件", "自动化"],
        "desc": "每天发2-3条商品信息，带图文"
    },
    "xiaohongshu": {
        "name": "小红书",
        "type": "social",
        "best_time": "12:00-13:00, 20:00-22:00",
        "content_type": "种草笔记",
        "daily_limit": 1,
        "tags": ["效率神器", "办公必备"],
        "desc": "发工具使用教程，引流到网站"
    },
    "wechat": {
        "name": "朋友圈",
        "type": "social",
        "best_time": "12:00-13:00, 20:00-21:00",
        "content_type": "短文案",
        "daily_limit": 1,
        "desc": "分享客户好评/使用效果"
    },
    "zhihu": {
        "name": "知乎",
        "type": "qa",
        "best_time": "20:00-22:00",
        "content_type": "回答",
        "daily_limit": 1,
        "tags": ["效率工具", "办公自动化"],
        "desc": "回答相关工具推荐问题"
    },
    "tieba": {
        "name": "百度贴吧",
        "type": "forum",
        "best_time": "10:00-11:00, 15:00-16:00",
        "content_type": "帖子",
        "daily_limit": 2,
        "desc": "在相关贴吧发推荐帖"
    },
    "douban": {
        "name": "豆瓣",
        "type": "community",
        "best_time": "20:00-22:00",
        "content_type": "日记/广播",
        "daily_limit": 1,
        "desc": "发效率工具相关广播"
    },
    "jianshu": {
        "name": "简书",
        "type": "writing",
        "best_time": "20:00-22:00",
        "content_type": "文章",
        "daily_limit": 1,
        "desc": "写效率工具推荐文章"
    },
    "bilibili": {
        "name": "B站",
        "type": "video",
        "best_time": "18:00-22:00",
        "content_type": "视频/专栏",
        "daily_limit": 1,
        "desc": "发工具使用教程视频"
    }
}


class AutoPromoter:
    def __init__(self):
        self.products = self._load_products()
        self.orders = self._load_orders()
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.weekday = datetime.now().weekday()

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

    def generate_on_site_promotions(self):
        """生成网站内推广元素"""
        now = datetime.now()
        
        # 1. 限时闪购（每2小时轮换）
        flash_hour = (now.hour // 2) * 2
        flash_products = self.products[flash_hour % max(1, len(self.products)-4):flash_hour % max(1, len(self.products)-4)+4]
        if len(flash_products) < 4:
            flash_products = self.products[:4]
        
        flash_sales = []
        for p in flash_products:
            flash_sales.append({
                "name": p["name"],
                "emoji": p.get("emoji", "🛠️"),
                "price": p["price"],
                "original_price": p.get("price_old", p["price"]),
                "discount": f"-{int((1-p['price']/p.get('price_old',p['price']))*100)}%",
                "end_time": (now + timedelta(hours=2)).strftime("%H:%M"),
                "id": p["id"]
            })
        
        # 2. 热销推荐
        orders = self.orders.get("orders", [])
        sold_ids = {}
        for o in orders:
            pid = o.get("product_id", "")
            if pid:
                sold_ids[pid] = sold_ids.get(pid, 0) + 1
        
        # 按销量排序
        scored = [(sold_ids.get(p["id"], 0), p) for p in self.products]
        scored.sort(key=lambda x: -x[0])
        hot_products = [p for _, p in scored[:6]]
        
        # 3. 今日优惠
        today_deals = []
        for p in self.products:
            if p.get("price", 999) <= 19:  # ¥19以下推荐
                today_deals.append({
                    "name": p["name"],
                    "emoji": p.get("emoji", "🛠️"),
                    "price": p["price"],
                    "original_price": p.get("price_old", p["price"]),
                    "id": p["id"]
                })
        
        # 4. 捆绑推荐（买了这个的人也买了）
        bundle_recommendations = []
        if orders:
            # 找出最常一起购买的产品组合
            recent_orders = [o.get("product_id") for o in orders[-20:]]
            if recent_orders:
                from collections import Counter
                common = Counter(recent_orders).most_common(3)
                for pid, _ in common:
                    for p in self.products:
                        if p["id"] == pid:
                            bundle_recommendations.append(p)
                            break
        
        return {
            "flash_sales": flash_sales,
            "hot_products": hot_products,
            "today_deals": today_deals,
            "bundle_recommendations": bundle_recommendations[:3],
            "product_count": len(self.products),
            "min_price": min(p["price"] for p in self.products) if self.products else 0,
            "promo_tag": "限时特惠" if now.hour < 12 else "今日热卖" if now.hour < 18 else "晚间特卖"
        }

    def generate_promo_tasks(self):
        """生成今日推广任务清单"""
        now = datetime.now()
        today_name = DAYS_CN[self.weekday]
        
        tasks = []
        
        # 选择今日主推产品（每天轮换）
        day_of_year = now.timetuple().tm_yday
        main_product_idx = day_of_year % max(1, len(self.products))
        main_product = self.products[main_product_idx]
        
        # 选择辅推产品
        second_idx = (main_product_idx + 3) % max(1, len(self.products))
        second_product = self.products[second_idx]
        
        for platform_key, platform_info in PROMO_PLATFORMS.items():
            is_weekend = self.weekday >= 5
            
            # 周末减少推送量
            if is_weekend and platform_info["daily_limit"] <= 1:
                continue
            
            # 选择适合这个平台的产品
            if platform_info["type"] == "marketplace":
                # 闲鱼推低价引流品
                promo_product = main_product if main_product["price"] > 19 else second_product
            elif platform_info["type"] == "social":
                # 社交平台推热门品
                promo_product = main_product
            elif platform_info["type"] == "qa":
                # 知乎推专业工具
                promo_product = second_product
            else:
                promo_product = main_product
            
            # 生成最佳发布时间
            best_time = platform_info.get("best_time", "20:00")
            
            tasks.append({
                "platform": platform_key,
                "platform_name": platform_info["name"],
                "product": promo_product["name"],
                "product_emoji": promo_product.get("emoji", "🛠️"),
                "product_price": promo_product["price"],
                "best_time": best_time,
                "content_type": platform_info.get("content_type", "推广"),
                "daily_limit": platform_info.get("daily_limit", 1),
                "description": platform_info.get("desc", ""),
                "tags": platform_info.get("tags", []),
                "completed": False,
                "priority": "high" if platform_info["type"] == "marketplace" else "medium"
            })
        
        # 按优先级排序
        tasks.sort(key=lambda t: 0 if t["priority"] == "high" else 1)
        
        return {
            "date": self.today,
            "weekday": today_name,
            "main_product": main_product["name"],
            "main_product_price": main_product["price"],
            "main_product_emoji": main_product.get("emoji", ""),
            "secondary_product": second_product["name"],
            "total_tasks": len(tasks),
            "tasks": tasks,
            "optimal_slots": [
                {"time": slot[0]+"-"+slot[1], "name": slot[2], "intensity": slot[3]}
                for slot in PROMO_SLOTS
            ]
        }

    def generate_share_content(self, product):
        """生成分享文案"""
        name = product["name"]
        emoji = product.get("emoji", "🛠️")
        price = product["price"]
        desc = product.get("desc", "")
        
        share_texts = {
            "wechat": f"{emoji} 发现一个好用的工具「{name}」，{desc[:30]}，只要¥{price}！一次购买永久使用👉 https://xiaxiaojun.zeabur.app/",
            "wechat_timeline": f"{emoji} {name} - ¥{price}\n{desc[:40]}\n一次购买永久使用，太值了！",
            "qq": f"推荐一个效率工具：{name}，{desc[:30]}，仅需¥{price}，一次购买永久更新！",
            "weibo": f"【{name}】{desc[:50]} 限时特价¥{price}（原价¥{product.get('price_old', price)}）一次购买永久使用！",
            "copy": f"{emoji} 【{name}】\n{desc}\n💰 特价 ¥{price}（原价¥{product.get('price_old', price)}）\n🔗 https://xiaxiaojun.zeabur.app/"
        }
        
        return share_texts

    def generate_share_links(self):
        """生成分享链接"""
        links = []
        base_url = "https://xiaxiaojun.zeabur.app/"
        
        # 为每个产品生成分享信息
        for p in self.products[:10]:  # 前10个产品
            share_texts = self.generate_share_content(p)
            links.append({
                "product": p["name"],
                "emoji": p.get("emoji", ""),
                "price": p["price"],
                "url": base_url,
                "share_texts": share_texts,
                "share_link": f"{base_url}?ref=share_{p['id']}"
            })
        
        return links

    def print_daily_plan(self):
        """打印今日推广计划"""
        tasks = self.generate_promo_tasks()
        promo = self.generate_on_site_promotions()
        links = self.generate_share_links()
        
        print(f"\n{'='*55}")
        print(f"  🚀 AutoPromotion 今日推广计划")
        print(f"  📅 {self.today} ({tasks['weekday']})")
        print(f"{'='*55}")
        
        print(f"\n  🎯 今日主推: {tasks['main_product_emoji']} {tasks['main_product']} (¥{tasks['main_product_price']})")
        print(f"  辅推: {tasks['secondary_product']}")
        
        print(f"\n  ⏰ 最佳推广时段:")
        for slot in tasks['optimal_slots'][:4]:
            icon = "🔴" if slot['intensity'] == 'peak' else "🟡" if slot['intensity'] == 'high' else "🟢"
            print(f"    {icon} {slot['time']} {slot['name']}")
        
        print(f"\n  📋 今日任务 ({tasks['total_tasks']}项):")
        for t in tasks['tasks'][:5]:
            print(f"    ✅ [{t['platform_name']}] {t['product_emoji']} {t['product']}")
            print(f"       ⏰ 最佳时间: {t['best_time']} | {t['content_type']}")
        
        print(f"\n  🔥 网站内推广:")
        print(f"    ⚡ 闪购: {len(promo['flash_sales'])}个产品限时特价")
        print(f"    🏆 热销: {len(promo['hot_products'])}个推荐")
        print(f"    💥 今日特惠: {len(promo['today_deals'])}个¥19以下产品")
        
        print(f"\n  📤 一键分享 ({len(links)}个产品):")
        for link in links[:3]:
            print(f"    📱 {link['emoji']} {link['product']} ¥{link['price']}")
            print(f"       {link['url']}")
        
        print(f"\n{'='*55}")
        print(f"  💡 推广建议:")
        print(f"  1. 优先完成闲鱼任务（转化率最高的平台）")
        print(f"  2. 黄金时段(20:00-22:00)集中发帖")
        print(f"  3. 每发一帖记录效果，优化后续内容")
        print(f"  4. 坚持7天，必有转化")
        print(f"{'='*55}\n")
        
        return tasks, promo


def run():
    promoter = AutoPromoter()
    return promoter.print_daily_plan()


if __name__ == "__main__":
    run()
