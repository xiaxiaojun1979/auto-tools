#!/usr/bin/env python3
"""
闲鱼自动发布文案生成器
自动生成吸引人的闲鱼商品描述 + 标签
"""

import json
from pathlib import Path
from datetime import datetime
import random

class XianyuListingGenerator:
    def __init__(self):
        # 闲鱼热门标签
        self.tags_pool = [
            "#电脑技巧", "#效率工具", "#办公软件", "#Python学习",
            "#副业项目", "#自媒体工具", "#懒人必备", "#数码好物",
            "#打工人必备", "#职场效率", "#自动化办公", "#资源分享"
        ]

    def generate_listing(self, product_name, price, description, features):
        """生成闲鱼商品描述"""

        # 吸引眼球的标题模板
        titles = [
            f"🔥{product_name}｜{description[:15]}",
            f"【省时神器】{product_name} 告别重复劳动",
            f"💻程序员出品｜{product_name}｜效率翻倍",
            f"🎯{product_name}｜{features[0]}｜自动完成"
        ]

        # 正文模板
        body_templates = [
            f"""🎯 {product_name}

💡 你是否也在重复以下工作？
{chr(10).join(['• ' + f for f in features[:4]])}

🛠 这个工具一键帮你搞定所有重复操作！

✨ 核心优势：
✅ 纯本地运行，数据安全
✅ 无需联网，不限使用次数
✅ 简单易用，复制即用
✅ 跨平台支持（Mac/Win/Linux）

📦 购买即得：
• 完整源码文件
• 详细使用教程
• 终身免费更新

💰 限时特价：¥{price}

🚀 一次购买，永久使用，解放你的时间！

#效率工具 #自动化办公 #副业 #Python"""
        ]

        return {
            "title": random.choice(titles),
            "body": random.choice(body_templates),
            "tags": " ".join(random.sample(self.tags_pool, 4)),
            "price": price,
            "category": "电脑/其他"
        }

    def export_all(self):
        """生成所有产品的闲鱼文案"""
        products = [
            {
                "name": "文件批处理大师",
                "price": 49,
                "desc": "一键批量重命名/压缩图片/格式转换/去重",
                "features": [
                    "手动一个一个重命名几百个文件？",
                    "手动压缩大量图片到指定大小？",
                    "手动查找硬盘里的重复文件？",
                    "手动转换图片格式？",
                    "文件整理花掉大把时间？"
                ]
            },
            {
                "name": "内容自动生成器",
                "price": 29,
                "desc": "自动生成小红书/抖音文案",
                "features": [
                    "每天想不出发什么内容？",
                    "写一篇文案要折腾半小时？",
                    "标题/开头/正文不会写？",
                    "找不到合适的标签？"
                ]
            },
            {
                "name": "数据清洗工具包",
                "price": 39,
                "desc": "一键清洗Excel/CSV数据",
                "features": [
                    "手动一条条去重几千行数据？",
                    "手动格式化手机号和日期？",
                    "手动检查数据有没有错误？",
                    "手动做数据统计分析？"
                ]
            }
        ]

        results = []
        for p in products:
            listing = self.generate_listing(p["name"], p["price"], p["desc"], p["features"])
            results.append({"product": p["name"], "listing": listing})
            print(f"\n{'='*50}")
            print(f"  产品：{p['name']} - ¥{p['price']}")
            print(f"{'='*50}")
            print(f"  标题：{listing['title']}")
            print(f"\n  正文：{listing['body']}")
            print(f"\n  标签：{listing['tags']}")
            print(f"{'='*50}")

        # 保存
        out_path = Path(__file__).parent / f"xianyu_listings_{datetime.now().strftime('%Y%m%d')}.json"
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[✓] 闲鱼文案已保存: {out_path}")

        return results


if __name__ == "__main__":
    gen = XianyuListingGenerator()
    gen.export_all()
