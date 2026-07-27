#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 推广内容生成器
动态加载products.json，生成适用于各平台的推广文案
"""

import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "marketing" / "data"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"


def load_all_products():
    """从products.json加载所有产品"""
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


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
        "style": "亲切自然",
        "tags": []
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
        "style": "实用推荐",
        "tags": ["工具推荐", "效率提升"]
    },
    "zhihu": {
        "name": "知乎",
        "max_len": 600,
        "style": "专业分享",
        "tags": ["效率工具", "办公自动化"]
    }
}


def generate_post(platform, product):
    """为指定平台和产品生成推广文案"""
    pid = product["id"]
    name = product["name"]
    desc = product.get("desc", "")
    price = product.get("price", 0)
    price_old = product.get("price_old", price)
    emoji = product.get("emoji", "✨")
    features = product.get("features", [])
    category = product.get("category", "")
    is_bundle = product.get("is_bundle", False)
    is_vip = product.get("is_vip", False)
    use_cases = features[:3] if features else [desc[:20]]

    discount = round((1 - price / price_old) * 100) if price_old > price else 0

    tagline = f"限时{discount}%OFF" if discount > 0 else "一次购买永久使用"

    if platform == "xianyu":
        tags = PLATFORMS["xianyu"]["tags"] + [category]
        post = f"""【{name}】🔥 {desc}

💰 价格：仅¥{price}（原价¥{price_old}，省¥{price_old-price}）
{'🎉 超值捆绑包！' if is_bundle else ''}
{'👑 VIP终身会员，解锁全部工具！' if is_vip else ''}
✅ 一次购买，永久使用
✅ 终身免费更新
✅ 售后技术支持

适用场景：
{chr(10).join('• ' + (f if len(f) < 30 else f[:30] + '...') for f in use_cases)}

搜索：{" ".join(tags)}"""

    elif platform == "wechat":
        if is_vip:
            post = f"""🔥 重磅推荐！{name}👑
仅需¥{price}，解锁全部{22}+款工具！
文件处理、视频下载、AI文案、图片去背景...应有尽有
一次付费，终身免费更新！
真的太划算了，需要的小伙伴私信我～"""
        elif is_bundle:
            post = f"""🎉 超值{name}，原价¥{price_old}，现在只要¥{price}！
包含文件处理、内容生成、数据清洗三大工具
一次购买永久使用，太划算了！"""
        else:
            post = f"""最近发现一个超好用的工具：{name}，{desc[:40]}...只要¥{price}，{'限时省¥' + str(price_old-price) + '！' if discount > 0 else '一次购买永久使用！'}需要的小伙伴私信我～"""

    elif platform == "xiaohongshu":
        tags = ["效率神器", "办公必备"] + ([category] if category else [])
        post = f"""✨ 我的天！{name}竟然只要¥{price}？！

一直为重复工作发愁，直到发现这个神器！
{desc}

🔥 它能做什么？
{chr(10).join('✅ ' + f for f in use_cases[:4])}

💰 {'限时特价¥' + str(price) + '（原价¥' + str(price_old) + '，省¥' + str(price_old-price) + '）' if discount > 0 else '仅需¥' + str(price)}
{'🎉 超值捆绑，一次拥有三个工具！' if is_bundle else ''}
{'👑 终身VIP，解锁全部工具+未来更新！' if is_vip else ''}
💡 一次购买终身使用，真的太良心了🔥

#{" ".join('#' + t for t in tags)}"""

    elif platform == "tieba":
        post = f"""【推荐】{name} - 仅需¥{price}
{desc[:50]}...
适用：{', '.join(use_cases[:3]) if use_cases else '办公效率'}
{'限时特价中！' if discount > 0 else '一次购买永久使用'}
链接：https://xiaoxiaojun.zeabur.app"""

    elif platform == "zhihu":
        post = f"""分享一个实用工具：{name}

{desc}

💰 价格：¥{price}（{'限时折扣' if discount > 0 else '一次购买永久使用'}）
{'🎉 包含文件处理、内容生成、数据清洗三大核心功能' if is_bundle else ''}

适用场景：
{chr(10).join('- ' + f for f in use_cases[:4])}

想了解详情的朋友可以访问：https://xiaoxiaojun.zeabur.app"""
    else:
        post = f"{emoji} {name} - {desc[:30]}，仅需¥{price}"

    return post


def generate_all():
    """为所有产品和平台生成推广文案"""
    products = load_all_products()
    posts = {}
    for platform in PLATFORMS:
        posts[platform] = {}
        for p in products:
            posts[platform][p["id"]] = generate_post(platform, p)
    return posts


def save():
    """保存并输出推广文案"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    posts = generate_all()

    path = DATA_DIR / f"posts_{datetime.now().strftime('%Y%m%d')}.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    products = load_all_products()
    print(f"\n{'='*50}")
    print(f"  📢 AutoTools 推广文案已生成!")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  📦 产品数: {len(products)}")
    print(f"  📱 平台数: {len(PLATFORMS)}")
    print(f"{'='*50}\n")

    for platform in PLATFORMS:
        for p in products[:2]:  # 只展示前2个产品示例
            print(f"【{PLATFORMS[platform]['name']} - {p['name']}】")
            text = posts[platform][p["id"]]
            print(text[:150] + "...\n")

    return posts


if __name__ == "__main__":
    save()
