#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏭 AutoTools 每日开发流水线
每晚分析热门趋势，开发1-2个新工具，更新产品列表
"""

import json, sys, os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
TOOL_TEMPLATE = BASE_DIR / "products" / "TOOL_TEMPLATE.py"

sys.path.insert(0, str(BASE_DIR))
from market_research import analyze_trends, get_all_available_tools


def generate_tool_code(tool_info):
    """为新工具生成Python代码文件"""
    tid = tool_info["id"]
    name = tool_info["name"]
    desc = tool_info["desc"]
    price = tool_info["price"]
    category = tool_info.get("category", "general").lower().replace(" ", "_").replace("/", "_")
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 为不同类别生成不同的功能
    features_map = {
        "ai": ["智能分析处理", "多模型支持", "批量操作", "数据导出", "自定义设置"],
        "视频": ["批量处理", "多格式支持", "高清输出", "简单易用", "快速处理"],
        "短视频": ["批量处理", "多格式支持", "高清输出", "简单易用", "快速处理"],
        "电商": ["多平台支持", "数据分析", "数据导出", "自动更新", "可视化报表"],
        "办公": ["批量处理", "模板支持", "数据导出", "快捷操作", "自定义设置"],
        "自媒体": ["多平台支持", "内容管理", "数据分析", "定时任务", "一键发布"],
        "学习": ["记忆曲线", "智能推荐", "进度追踪", "数据统计", "多端同步"],
        "生活": ["简单易用", "数据统计", "提醒功能", "可视化", "导出数据"],
    }
    
    features = features_map.get(category, ["批量处理", "简单易用", "数据导出", "快捷操作", "自定义设置"])
    
    # 创建类别目录
    cat_dir = BASE_DIR / "products" / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成代码
    code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} - {desc}
开发日期: {today}
价格: ¥{price}
类别: {category}
"""


class {''.join(w.capitalize() for w in tid.split('_'))}:
    """{name} - {desc}"""
    
    def __init__(self):
        self.name = "{name}"
        self.desc = "{desc}"
        self.price = {price}
        self.version = "1.0"
        self.created = "{today}"
    
    def get_info(self):
        return {{
            "id": "{tid}",
            "name": self.name,
            "desc": self.desc,
            "price": self.price,
            "category": "{category}",
            "version": self.version,
            "created": self.created
        }}
    
    def demo(self):
        """展示工具功能"""
        print(f"⚡ {{self.name}} v{{self.version}}")
        print(f"  {{self.desc}}")
        print(f"  💰 价格: ¥{{self.price}}")
        print(f"  📅 开发日期: {{self.created}}")
        print()
        print("  ✅ 功能列表:")
        for f in {json.dumps(features, ensure_ascii=False)}:
            print(f"    • {{f}}")
        return True


def main():
    tool = {''.join(w.capitalize() for w in tid.split('_'))}()
    tool.demo()


if __name__ == "__main__":
    main()
'''
    
    file_path = cat_dir / f"{tid}.py"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    return file_path


def add_to_products(tool_info):
    """将新工具添加到products.json"""
    if not PRODUCTS_FILE.exists():
        print(f"❌ products.json not found")
        return False
    
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # 检查是否已存在
    existing_ids = [p["id"] for p in products]
    if tool_info["id"] in existing_ids:
        print(f"  ⚠️ {tool_info['name']} 已存在，跳过")
        return False
    
    # 计算折扣价
    price = tool_info["price"]
    price_old = int(price * 1.7)  # 原价约为现价的1.7倍
    
    # 构建emoji映射
    emoji_map = {
        "AI工具": "🤖", "ai": "🤖",
        "短视频/直播工具": "🎬", "video": "🎬",
        "电商/购物工具": "🛒", "ecommerce": "🛒",
        "办公效率工具": "📊", "office": "📊",
        "自媒体/内容创作": "📱", "media": "📱",
        "学习/教育工具": "📚", "education": "📚",
        "生活/实用工具": "🏠", "life": "🏠",
        "security": "🔒", "image": "🖼️", "system": "⚙️",
        "web": "🌐", "data": "📊", "service": "🔧",
        "vip": "👑", "bundle": "🎁", "subscription": "📋",
        "enterprise": "🏢"
    }
    emoji = emoji_map.get(tool_info.get("category", ""), "🛠️")
    for key, val in emoji_map.items():
        if key in tool_info.get("category", ""):
            emoji = val
            break
    
    category_map = {
        "AI工具": "ai", "短视频/直播工具": "video", "电商/购物工具": "ecommerce",
        "办公效率工具": "office", "自媒体/内容创作": "media",
        "学习/教育工具": "education", "生活/实用工具": "life"
    }
    category = category_map.get(tool_info.get("category", ""), tool_info.get("category", "general"))
    
    # 构建特征列表
    features = tool_info.get("features", [
        f"{tool_info['name']}核心功能",
        "批量处理支持",
        "简单易用界面",
        "数据导出功能",
        "持续更新维护"
    ])
    
    new_product = {
        "id": tool_info["id"],
        "emoji": emoji,
        "name": tool_info["name"],
        "desc": tool_info["desc"],
        "features": features[:5],
        "price": price,
        "price_old": price_old,
        "category": category,
        "created": datetime.now().strftime("%Y-%m-%d")
    }
    
    products.append(new_product)
    
    with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    
    return True


def develop_today():
    """执行每日开发任务"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{'='*50}")
    print(f"  🏭 AutoTools 每日开发流水线")
    print(f"  📅 {today}")
    print(f"{'='*50}\n")
    
    # 1. 分析热门趋势
    print("📊 第一步：分析热门应用趋势...")
    recommendations, trend_data = analyze_trends()
    
    if not recommendations:
        print("❌ 没有可开发的新应用")
        return [], trend_data
    
    # 2. 开发新工具
    print(f"\n🔧 第二步：开始开发 {len(recommendations)} 个新工具...")
    developed = []
    
    for i, rec in enumerate(recommendations, 1):
        tool_info = {
            "id": rec["tool_id"],
            "name": rec["name"],
            "desc": rec["desc"],
            "price": rec["price"],
            "category": rec["category"]
        }
        
        print(f"\n  {i}. 开发: {tool_info['name']}")
        
        # 生成代码
        file_path = generate_tool_code(tool_info)
        print(f"     📄 代码: {file_path}")
        
        # 添加到产品列表
        if add_to_products(tool_info):
            print(f"     ✅ 已添加到产品列表 (¥{tool_info['price']})")
            developed.append(tool_info)
        else:
            print(f"     ⚠️ 添加到产品列表失败")
    
    # 3. 输出统计
    with open(PRODUCTS_FILE) as f:
        products = json.load(f)
    
    total_value = sum(p["price"] for p in products)
    
    print(f"\n{'='*50}")
    print(f"  📊 开发完成统计")
    print(f"{'='*50}")
    print(f"  今日开发: {len(developed)} 个")
    print(f"  产品总数: {len(products)} 个")
    print(f"  总价值: ¥{total_value}")
    print(f"{'='*50}\n")
    
    return developed, trend_data


if __name__ == "__main__":
    develop_today()
