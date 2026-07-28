#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼每日运营系统 - 发布/维护/优化/报告
每天自动运行，确保闲鱼店铺正常运营
"""

import json, os, subprocess, random, time, base64, sys
from datetime import datetime, date
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).parent
NODE = "/Users/tianmengpiaoxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
XB = "/Users/tianmengpiaoxiang/.qclaw/skills/xbrowser/scripts/xb.cjs"
PRODUCTS_FILE = BASE_DIR / "products" / "products.json"
XIANYU_DATA_FILE = BASE_DIR / "daily_report" / "data" / "xianyu_stats.json"
LOG_FILE = "/tmp/xianyu_daily_ops.log"

# ========== 产品数据 ==========

def load_products():
    """加载产品列表"""
    with open(PRODUCTS_FILE) as f:
        return json.load(f)

def get_published_ids():
    """获取已发布的商品ID（从数据文件读取）"""
    data = load_stats()
    return data.get("published_ids", [])

def save_published_ids(ids):
    """保存已发布的商品ID"""
    data = load_stats()
    data["published_ids"] = ids
    save_stats(data)

def load_stats():
    """加载统计数据"""
    XIANYU_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if XIANYU_DATA_FILE.exists():
        with open(XIANYU_DATA_FILE) as f:
            return json.load(f)
    return {"published_ids": [], "total_views": 0, "total_wants": 0, "revenue": 0, "daily_logs": []}

def save_stats(data):
    """保存统计数据"""
    with open(XIANYU_DATA_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ========== 图片生成 ==========

def generate_product_card(name, desc, features, price, price_old, idx):
    """生成网页风格的截图"""
    colors = [
        ('#667eea', '#764ba2'), ('#059669', '#047857'), ('#d97706', '#b45309'),
        ('#dc2626', '#b91c1c'), ('#7c3aed', '#6d28d9'), ('#0284c7', '#0369a1'),
    ]
    bg1, bg2 = colors[idx % len(colors)]
    
    img = Image.new('RGB', (1200, 900), '#f5f7fa')
    draw = ImageDraw.Draw(img)
    
    # 用纯色header替代渐变（兼容性更好）
    for i in range(250):
        ratio = i / 250
        r1, g1, b1 = int(bg1[1:3], 16), int(bg1[3:5], 16), int(bg1[5:7], 16)
        r2, g2, b2 = int(bg2[1:3], 16), int(bg2[3:5], 16), int(bg2[5:7], 16)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.rectangle([(0, i), (1200, i)], fill=(r, g, b))
    
    try:
        ft48 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 48)
        ft36 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 36)
        ft28 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 28)
        ft26 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 26)
        ft60 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 60)
        ft20 = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 20)
    except:
        try:
            ft48 = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 48)
            ft36 = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 36)
            ft28 = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 28)
            ft26 = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 26)
            ft60 = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 60)
            ft20 = ImageFont.truetype("/System/Library/Fonts/Hiragino Sans GB.ttc", 20)
        except:
            ft48 = ft36 = ft28 = ft26 = ft60 = ft20 = ImageFont.load_default()
    
    draw.text((600, 100), name, fill='white', font=ft48, anchor='mm')
    draw.text((600, 160), desc[:40], fill='#c4b5fd', font=ft28, anchor='mm')
    
    draw.rounded_rectangle([(50, 230), (1150, 800)], radius=16, fill='white')
    draw.rounded_rectangle([(50, 230), (1150, 800)], radius=16, outline='#e0e0e0', width=1)
    
    draw.text((100, 270), "功能列表", fill='#333', font=ft36)
    
    y = 340
    for feat in features[:8]:
        draw.text((120, y), f"✓  {feat}", fill='#444', font=ft26)
        y += 48
    
    draw.text((100, 660), f"¥{price}", fill='#e74c3c', font=ft60)
    if price_old and price_old > price:
        draw.text((300, 675), f"¥{price_old}", fill='#999', font=ft28)
    
    draw.rounded_rectangle([(100, 720), (1100, 770)], radius=12, fill='#667eea')
    draw.text((600, 745), f"立即购买 - ¥{price}", fill='white', font=ft36, anchor='mm')
    
    draw.text((600, 830), "更多工具请访问: xiaxiaojun.com", fill='#999', font=ft20, anchor='mm')
    
    path = f"/tmp/xianyu_card_{idx}.png"
    img.save(path)
    return path

# ========== XBrowser操作 ==========

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
    """导航到URL"""
    return xb(f"open '{url}'")

def snapshot():
    """获取页面快照"""
    return xb("snapshot -i")

def click(ref):
    """点击元素"""
    return xb(f"click {ref}")

def fill(ref, text):
    """填写输入框"""
    return xb(f"fill {ref} '{text}'")

# ========== 发布商品 ==========

def publish_product(product, idx):
    """发布单个商品到闲鱼 - 改进版"""
    name = product["name"]
    price = product.get("price", 19)
    price_old = product.get("price_old", int(price * 1.5))
    desc_text = product.get("desc", name)
    features = product.get("features", [name])
    
    log(f"发布 [{idx}] {name} ¥{price}")
    
    # 1. 生成商品卡截图
    img_path = generate_product_card(name, desc_text, features, price, price_old, idx)
    
    # 2. 构造详细描述
    desc_lines = [f"【{name}】{desc_text}", "", "【功能介绍】"]
    for i, feat in enumerate(features[:8], 1):
        desc_lines.append(f"{i}. {feat}")
    desc_lines.extend([
        "", "【价格说明】",
        f"原价¥{price_old}，现仅需¥{price}",
        "购买后自动发送下载链接和激活码到邮箱",
        "", "【购买方式】",
        "1️⃣ 直接拍下即可",
        "2️⃣ 付款后系统自动发送激活码到你的闲鱼消息",
        "3️⃣ 访问官网 xiaxiaojun.com 输入激活码下载",
        "", "【更多工具】",
        "访问官网 xiaxiaojun.com 查看更多AI办公效率工具",
        "", "【搜索关键词】",
        f"{name} 办公效率 电脑工具 软件 自动化 AI工具"
    ])
    desc = "\n".join(desc_lines)
    
    # 3. 生成宣传语
    title_tags = [f"[新] {name} {desc_text[:20]}", f"{name} 自动发货", f"🔥{name} 限时优惠"]
    title = title_tags[idx % len(title_tags)]
    
    log(f"  标题: {title}")
    
    try:
        # 4. 打开发布页
        navigate("https://www.goofish.com/publish")
        time.sleep(4)
        
        # 5. 尝试通过JS设置表单（使用更通用的选择器）
        result = xb_eval(f"""
(function() {{
    var r = [];
    
    // 尝试多种选择器找到描述/文本输入框
    var descSet = false;
    
    // 方式1: Ant Design TextArea
    var textareas = document.querySelectorAll('textarea');
    for(var t of textareas) {{
        if(t.offsetParent !== null) {{  // 可见的
            try {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                nativeSetter.call(t, {repr(desc)});
                t.dispatchEvent(new Event('input', {{bubbles:true}}));
                t.dispatchEvent(new Event('change', {{bubbles:true}}));
                descSet = true;
                r.push('ta_filled');
                break;
            }} catch(e) {{ r.push('ta_err:'+e.message); }}
        }}
    }}
    
    if(!descSet) {{
        // 方式2: 查找contenteditable元素
        var editors = document.querySelectorAll('[contenteditable="true"]');
        for(var ed of editors) {{
            if(ed.offsetParent !== null) {{
                ed.textContent = {repr(desc)};
                ed.dispatchEvent(new Event('input', {{bubbles:true}}));
                ed.dispatchEvent(new Event('change', {{bubbles:true}}));
                descSet = true;
                r.push('ce_filled');
                break;
            }}
        }}
    }}
    
    // 填写价格
    var priceInputs = document.querySelectorAll('input[type="text"], input[type="number"]');
    var priceSet = false;
    for(var inp of priceInputs) {{
        if(inp.offsetParent !== null && (inp.placeholder || '').match(/价格|价|amount|price/i)) {{
            try {{
                var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                ns.call(inp, '{price}');
                inp.dispatchEvent(new Event('input', {{bubbles:true}}));
                inp.dispatchEvent(new Event('change', {{bubbles:true}}));
                priceSet = true;
                r.push('price_set');
                break;
            }} catch(e) {{ r.push('price_err:'+e.message); }}
        }}
    }}
    
    // 如果没有匹配到placeholder，尝试找所有可见的input
    if(!priceSet) {{
        for(var inp of priceInputs) {{
            if(inp.offsetParent !== null && inp.value === '') {{
                try {{
                    var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    ns.call(inp, '{price}');
                    inp.dispatchEvent(new Event('input', {{bubbles:true}}));
                    inp.dispatchEvent(new Event('change', {{bubbles:true}}));
                    priceSet = true;
                    r.push('price_guess');
                    break;
                }} catch(e) {{ r.push('p_guess_err:'+e.message); }}
            }}
        }}
    }}
    
    return r.join(',');
}})()
"""
        log(f"  表单填充: {result[:200]}")
        time.sleep(2)
        
        # 6. 上传图片（通过截图实现文件上传）
        log(f"  图片路径: {img_path}")
        
        # 7. 截图当前状态判断是否需要点击"无需邮寄"
        snap = snapshot()
        log(f"  页面快照: {snap[:100] if snap else 'empty'}")
        
        # 8. 尝试找到发布按钮
        for attempt in range(3):
            snap = snapshot()
            log(f"  寻找发布按钮 (尝试 {attempt+1})")
            
            # 用JS找发布按钮
            r = xb_eval("""
(function(){
    var btns = document.querySelectorAll('button, a, div[role="button"]');
    for(var b of btns) {
        var t = (b.textContent || '').trim();
        if(t.includes('发布') && b.offsetParent !== null) {
            b.click();
            return 'clicked:' + t;
        }
        // Ant Design Button
        if(b.className && b.className.includes('ant-btn') && b.offsetParent !== null) {
            var bt = (b.textContent || '').trim();
            if(bt.includes('发布') || bt.includes('提交')) {
                b.click();
                return 'ant_clicked:' + bt;
            }
        }
    }
    return 'no_publish_btn_found';
})()
""")
            log(f"  点击发布: {r[:100]}")
            
            if 'clicked' in r:
                time.sleep(4)
                break
            time.sleep(2)
        
        # 9. 检查结果
        time.sleep(3)
        r = xb_eval("window.location.href")
        log(f"  当前URL: {r[:200]}")
        
        if "item?id=" in r:
            item_id = r.split("item?id=")[1].split("&")[0]
            log(f"  ✅ 产品发布成功! ID: {item_id}")
            return item_id
        elif "publish" not in r and "success" in r.lower():
            log(f"  ✅ 可能发布成功: {r[:100]}")
            return "unknown-" + str(int(time.time()))
        else:
            log(f"  ❌ 发布失败或仍在发布页")
            return None
            
    except Exception as e:
        log(f"  ❌ 发布异常: {str(e)}")
        return None


def refresh_items():
    """尝试"擦亮"已发布的商品（提升曝光）"""
    log("=== 擦亮商品 ===")
    navigate("https://www.goofish.com/")
    time.sleep(2)
    
    # 通过JS查找"擦亮"按钮并点击
    r = xb_eval("""
    (function(){
        var btns = document.querySelectorAll('button, a, span, div');
        var count = 0;
        btns.forEach(function(b){
            if(b.textContent && b.textContent.includes('擦亮')) {
                b.click();
                count++;
            }
        });
        return 'Found and clicked ' + count + ' refresh buttons';
    })()
    """)
    log(f"  擦亮结果: {r[:100]}")
    return r

# ========== 检查消息 ==========

def check_messages():
    """检查未读消息数"""
    r = xb_eval("""
    (function(){
        var els = document.querySelectorAll('*');
        for(var i=0; i<els.length; i++) {
            var t = els[i].textContent || '';
            if(t.match(/\\d+\\s*消息/)) return t.trim();
        }
        return '0 消息';
    })()
    """)
    log(f"  消息状态: {r[:50]}")
    return r

# ========== 每日运营主流程 ==========

def daily_ops():
    """每日闲鱼运营"""
    log("=" * 50)
    log(f"闲鱼每日运营开始 - {date.today()}")
    
    products = load_products()
    published_ids = get_published_ids()
    stats = load_stats()
    
    # 1. 检查消息
    msg_status = check_messages()
    
    # 2. 擦亮商品（每2小时自动擦亮）
    refresh_items()
    
    # 3. 发布新商品（每次发3个未发布过的）
    new_count = 0
    unpublised = [p for p in products if p["id"] not in published_ids and p.get("price", 99) <= 99]
    
    # 优先发低价产品（容易成交）
    unpublised.sort(key=lambda p: p.get("price", 999))
    
    log(f"未发布产品: {len(unpublised)}个")
    
    for i, product in enumerate(unpublised[:4]):
        item_id = publish_product(product, i)
        if item_id:
            published_ids.append(product["id"])
            new_count += 1
            stats["published_ids"] = published_ids
            save_stats(stats)
            time.sleep(random.randint(30, 60))
    
    # 4. 更新统计
    today = str(date.today())
    daily_log = {
        "date": today,
        "published": new_count,
        "total_published": len(published_ids),
        "messages": msg_status,
        "products_remaining": len(unpublised) - new_count
    }
    
    stats["daily_logs"] = [d for d in stats.get("daily_logs", []) if d.get("date") != today]
    stats["daily_logs"].append(daily_log)
    save_stats(stats)
    
    log(f"今日发布: {new_count}个, 总计已发布: {len(published_ids)}个")
    log(f"=== 每日运营完成 ===")
    
    return {
        "new_products": new_count,
        "total_published": len(published_ids),
        "remaining": len(unpublised) - new_count,
        "messages": msg_status
    }

def maintenance():
    """独立维护任务（每2小时执行一次）"""
    log("=== 维护任务 ===")
    refresh_items()
    check_messages()
    log("=== 维护完成 ===")

def generate_report():
    """生成闲鱼运营报告"""
    stats = load_stats()
    products = load_products()
    published_ids = get_published_ids()
    today = str(date.today())
    
    daily = None
    for d in stats.get("daily_logs", []):
        if d.get("date") == today:
            daily = d
            break
    
    report_lines = [
        f"===== 闲鱼运营报告 - {today} =====",
        f"已发布商品: {len(published_ids)}/{len(products)}",
        f"今日发布: {daily.get('published', 0) if daily else 0}个",
        f"未发布: {len(products) - len(published_ids)}个",
        f"消息: {daily.get('messages', '未检查') if daily else '未检查'}",
        "",
        f"== 已发布商品列表 =="
    ]
    
    for pid in published_ids:
        p = next((x for x in products if x["id"] == pid), None)
        if p:
            report_lines.append(f"  {p['name']} ¥{p.get('price', 0)}")
    
    report_lines.append("")
    report_lines.append(f"未发布商品({len(products)-len(published_ids)}个):")
    for p in products:
        if p["id"] not in published_ids:
            report_lines.append(f"  {p['name']} ¥{p.get('price', 0)}")
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    
    if mode == "daily":
        result = daily_ops()
        print(json.dumps(result, ensure_ascii=False))
    elif mode == "maintenance":
        maintenance()
    elif mode == "report":
        print(generate_report())
    elif mode == "publish":
        # 手动指定发布几个
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
        products = load_products()
        published_ids = get_published_ids()
        unpublised = [p for p in products if p["id"] not in published_ids and p.get("price", 99) <= 99]
        for i, product in enumerate(unpublised[:count]):
            item_id = publish_product(product, i)
            if item_id:
                published_ids.append(product["id"])
                save_published_ids(published_ids)
            time.sleep(random.randint(30, 60))
        print(f"手动发布完成")
