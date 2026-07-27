#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 推广内容生成器
生成适用于各平台的推广文案
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "marketing" / "data"

PRODUCT_INTROS = {
    "file_tools": {
        "name": "文件批处理大师",
        "tagline": "一键批量处理成千上万文件，告别重复劳动",
        "use_cases": ["设计稿批量重命名", "文档格式转换", "照片智能分类"],
        "price": 49
    },
    "content_gen": {
        "name": "内容自动生成器",
        "tagline": "AI帮你写标题、摘要、文案，效率翻倍",
        "use_cases": ["自媒体文章标题", "SEO关键词优化", "社交媒体文案"],
        "price": 29
    },
    "data_tools": {
        "name": "数据清洗工具包",
        "tagline": "Excel/CSV数据一键清理，告别手动整理",
        "use_cases": ["销售报表清洗", "客户数据去重", "异常值检测"],
        "price": 39
    },
    "bundle": {
        "name": "三件套捆绑包",
        "tagline": "一次拥有全部工具，省98元！",
        "use_cases": ["办公效率全套解决方案"],
        "price": 79
    }
}

PLATFORMS = {
    "xianyu": {
        "name": "闲鱼",
        "emoji": "",
        "max_len": 500,
        "style": "简洁实用",
        "tags": ["效率工具", "办公软件", "Python工具", "自动化"]
    },
    "wechat": {
        "name": "朋友圈",
        "emoji": "",
        "max_len": 200,
        "style": "亲切自然",
        "tags": []
    },
    "xiaohongshu": {
        "name": "小红书",
        "emoji": "",
        "max_len": 1000,
        "style": "种草分享",
        "tags": ["效率神器", "办公必备", "数码好物"]
    }
}

def generate_post(platform, product_id):
    product = PRODUCT_INTROS[product_id]
    plat = PLATFORMS[platform]
    
    if platform == "xianyu":
        post = """【{}】{}
{}
适用场景：
{}
价格：仅¥{}，一次购买永久使用
搜索：{}""".format(
            product["name"], product["tagline"],
            "------------------------",
            "\n".join("• " + u for u in product["use_cases"]),
            product["price"],
            " ".join(plat["tags"])
        )
    elif platform == "wechat":
        post = """最近发现一个超好用的工具，{}，{}。只要¥{}，一次购买永久使用，太划算了！需要的小伙伴私信我～""".format(
            product["name"], product["tagline"],
            product["price"]
        )
    elif platform == "xiaohongshu":
        post = """{} 我的天！{}竟然只要¥{}？！

一直为每天重复的文件处理发愁，直到发现这个神器！
{}具体能做什么：
{}
一次购买终身使用，真的太良心了🔥

#{} #{} #效率工具""".format(
            product["emoji"] if product.get("emoji","") else "✨",
            product["name"], product["price"],
            product["tagline"],
            "\n".join("✅ " + u for u in product["use_cases"]),
            "效率神器", "办公必备"
        )
    else:
        post = "{} - {}，仅需¥{}".format(product["name"], product["tagline"], product["price"])
    
    return post

def generate_all():
    posts = {}
    for platform in PLATFORMS:
        posts[platform] = {}
        for pid in PRODUCT_INTROS:
            posts[platform][pid] = generate_post(platform, pid)
    return posts

def save():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    posts = generate_all()
    
    path = DATA_DIR / "posts_{}.json".format(datetime.now().strftime("%Y%m%d"))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    # Print a sample
    print("✅ 推广文案已生成!")
    print()
    for platform in PLATFORMS:
        for pid in PRODUCT_INTROS:
            print("【{} - {}】".format(PLATFORMS[platform]["name"], PRODUCT_INTROS[pid]["name"]))
            print(posts[platform][pid][:200] + "...")
            print()
    return posts

if __name__ == "__main__":
    save()
