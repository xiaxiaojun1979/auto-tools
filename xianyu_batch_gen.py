#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼批量产品描述生成器
由于闲鱼Web版不支持数字商品发布，
本脚本生成所有产品的描述和二维码，
用手机闲鱼APP扫码后自动填入信息发布
"""

import json, os, qrcode, base64
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent
OUTPUT = BASE / "xianyu_products"
OUTPUT.mkdir(exist_ok=True)

def load_products():
    with open(BASE / "products" / "products.json") as f:
        return json.load(f)

def generate_xianyu_desc(product):
    """生成闲鱼格式的商品描述"""
    name = product["name"]
    desc = product.get("desc", "")
    features = product.get("features", [])
    price = product["price"]
    
    text = f"""{name}
{desc}

【功能介绍】
"""
    for i, f in enumerate(features[:8], 1):
        text += f"{i}. {f}\n"
    
    text += f"""
【价格】
¥{price}

【交易方式】
付款后自动发送下载链接+激活码到闲鱼消息

【关于我们】
更多AI办公工具请访问官网
🔗 xiaoxiaojun.com

【关键词】
{name} AI工具 办公效率 自动化 软件工具"""
    return text

def generate_all():
    products = load_products()
    print(f"共 {len(products)} 个产品")
    
    all_descs = []
    
    for i, p in enumerate(products):
        name = p["name"]
        price = p["price"]
        pid = p["id"]
        
        # 生成描述
        desc = generate_xianyu_desc(p)
        
        # 生成二维码（扫码后用手机发布）
        qr_data = f"闲鱼发布:{name} ¥{price}"
        qr = qrcode.make(qr_data)
        qr_path = OUTPUT / f"qr_{pid}.png"
        qr.save(qr_path)
        
        # 保存描述
        desc_path = OUTPUT / f"desc_{pid}.txt"
        desc_path.write_text(desc, encoding="utf-8")
        
        all_descs.append({
            "id": pid,
            "name": name,
            "price": price,
            "desc_file": str(desc_path),
            "qr_file": str(qr_path)
        })
        
        print(f"  [{i+1}/{len(products)}] {name} ¥{price}")
    
    # 生成汇总索引
    index = {
        "total": len(products),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "products": all_descs
    }
    (OUTPUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
    
    print(f"\n✅ 全部生成完成！")
    print(f"   产品描述目录: {OUTPUT}")
    print(f"   共 {len(all_descs)} 个产品描述文件")
    
    # 生成手机发布指南
    guide = f"""📱 闲鱼手机APP发布指南
====================
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
产品总数: {len(products)}

操作步骤：
1. 打开闲鱼APP，点击"卖闲置"
2. 选择分类"软件/程序/网站开发"
3. 根据 desc_*.txt 填写商品描述
4. 上传对应截图（从网站截图）
5. 设置价格 ¥XX
6. 选择"无需邮寄"
7. 点击发布

每个产品的描述已保存在:
{OUTPUT}/desc_*.txt

建议发布策略：
1. 先发低价产品（¥9-29），容易成交
2. 每天发3-5个，不要一次发太多
3. 已发布的产品隔天"擦亮"一次
4. 客户咨询时引导到官网购买

当前已发布产品："""
    (OUTPUT / "发布指南.txt").write_text(guide, encoding="utf-8")
    
    return products

if __name__ == "__main__":
    products = generate_all()
    print(f"\n总产品价值: ¥{sum(p['price'] for p in products)}")
    print(f"平均价格: ¥{sum(p['price'] for p in products)//len(products)}")
    
    # 按价格区间统计
    ranges = {"9-19元": 0, "20-39元": 0, "40-99元": 0, "100-299元": 0, "300+元": 0}
    for p in products:
        pr = p["price"]
        if pr <= 19: ranges["9-19元"] += 1
        elif pr <= 39: ranges["20-39元"] += 1
        elif pr <= 99: ranges["40-99元"] += 1
        elif pr <= 299: ranges["100-299元"] += 1
        else: ranges["300+元"] += 1
    print(f"\n价格分布:")
    for k, v in ranges.items():
        print(f"  {k}: {v}个")
