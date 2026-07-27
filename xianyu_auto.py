#!/usr/bin/env python3
"""
闲鱼自动发布系统
- 自动从网站获取产品
- 生成商品图
- 通过浏览器自动发布到闲鱼
"""

import json, os, subprocess, random, time, base64
from datetime import datetime

NODE = "/Users/tianmengpiaoxiang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
XB = "/Users/tianmengpiaoxiang/.qclaw/skills/xbrowser/scripts/xb.cjs"
PRODUCTS_DIR = "/Users/tianmengpiaoxiang/auto_business/products"
LOG_FILE = "/tmp/xianyu_auto.log"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def run_xb(cmd):
    """执行xbrowser命令"""
    full_cmd = f'"{NODE}" {XB} run --browser chrome {cmd}'
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=30)
    return result.stdout

def generate_product_image(name, price, idx, features, desc_text):
    """生成网页风格的截图"""
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.new('RGB', (1200, 900), '#f5f7fa')
    draw = ImageDraw.Draw(img)
    
    # 头部渐变 (模仿网站header)
    for i in range(250):
        r = int(102 + i * 0.3)
        g = int(126 - i * 0.1)
        b = int(234 - i * 0.4)
        draw.rectangle([(0, i), (1200, i)], fill=(r, g, b) if r > 0 and g > 0 and b > 0 else (102, 126, 234))
    
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 48)
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 36)
        font_desc = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 28)
        font_feature = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 26)
        font_price = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 60)
        font_url = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
    except:
        font_large = font_title = font_desc = font_feature = font_price = font_url = ImageFont.load_default()
    
    # 产品名
    draw.text((600, 100), name, fill='white', font=font_large, anchor='mm')
    draw.text((600, 160), desc_text[:40], fill='#c4b5fd', font=font_desc, anchor='mm')
    
    # 白色卡片
    draw.rounded_rectangle([(50, 230), (1150, 800)], radius=16, fill='white')
    draw.rounded_rectangle([(50, 230), (1150, 800)], radius=16, outline='#e0e0e0', width=1)
    
    draw.text((100, 270), "功能列表", fill='#333', font=font_title)
    
    y = 340
    for feat in features[:8]:
        draw.text((120, y), f"\u2713  {feat}", fill='#444', font=font_feature)
        y += 48
    
    y_price = 660
    draw.text((100, y_price), f"\u00a5{price}", fill='#e74c3c', font=font_price)
    
    btn_y = 720
    draw.rounded_rectangle([(100, btn_y), (1100, btn_y + 50)], radius=12, fill='#667eea')
    draw.text((600, btn_y + 25), f"\u7acb\u5373\u8d2d\u4e70 - \u00a5{price}", fill='white', font=font_title, anchor='mm')
    
    draw.text((600, 830), "\u66f4\u591a\u5de5\u5177\u8bf7\u8bbf\u95ee: xiaxiaojun.zeabur.app", fill='#999', font=font_url, anchor='mm')
    
    path = f"/tmp/xianyu_product_{idx}.png"
    img.save(path)
    return path


def generate_description(name, price, features, desc_text):
    """生成详细的商品描述"""
    desc = f"""【{name}】{desc_text}

【功能介绍】
"""
    for i, f in enumerate(features[:8], 1):
        desc += f"{i}. {f}\n"
    desc += f"""
【价格说明】
原价\u00a5{int(price*1.5)}，现仅需\u00a5{price}
购买后自动发送下载链接和激活码

【更多工具】
请访问官网查看更多AI办公工具：
xiaxiaojun.zeabur.app

【关键词】
{name} 办公效率 AI工具 电脑工具 软件推荐 办公自动化"""
    return desc

def generate_description(name, price, features):
    """生成商品描述"""
    desc = f"""{name}

功能列表：
"""
    for f in features[:5]:
        desc += f"- {f}\n"
    desc += f"\n原价¥{int(price*1.5)}，现仅需¥{price}\n\n购买后自动发下载链接\n\n更多工具请访问: xiaxiaojun.zeabur.app"
    return desc

def get_products():
    """从网站获取产品列表"""
    import requests
    try:
        r = requests.get("http://localhost:8000/", timeout=5)
        import re
        html = r.text
        products = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        prices = re.findall(r'¥(\d+\.?\d*)', html)
        
        result = []
        for i, (name, price) in enumerate(zip(products, prices)):
            p = float(price)
            if 9 <= p <= 99:  # 只取9-99元的产品
                result.append({
                    "name": name.strip()[:30],
                    "price": int(p),
                    "features": [name.strip()[:20]]
                })
        return result[:50]
    except:
        log("WARNING: 无法连接网站，使用默认产品")
        return [
            {"name": "文件批处理大师", "price": 19, "features": ["批量处理文件", "自动重命名", "格式转换"]},
            {"name": "数据清洗工具", "price": 19, "features": ["自动清洗数据", "去重处理", "格式标准化"]},
            {"name": "Excel宏工具包", "price": 14, "features": ["自动生成报表", "数据透视", "公式批量处理"]},
        ]

def publish_product(product, idx):
    """发布单个商品到闲鱼"""
    name = product["name"]
    price = product["price"]
    
    log(f"开始发布 [{idx+1}] {name} ¥{price}")
    
    # 1. 生成商品图
    img_path = generate_product_image(name, price, idx, product['features'], product.get('desc', name))
    with open(img_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    # 2. 打开发布页
    run_xb(f"open 'https://www.goofish.com/publish'")
    time.sleep(2)
    
    # 3. 获取最新引用
    run_xb("snapshot -i")
    time.sleep(0.5)
    
    # 4. 生成描述(无emoji)
    desc = generate_description(name, price, product["features"], product.get("desc", name))
    
    # 5. 通过eval一次性设置所有内容
    js_code = f"""
(function(){{
    var r = [];
    
    // 设置描述
    var editor = document.querySelector("[class*=editor]");
    if(editor) {{
        editor.focus();
        editor.innerHTML = "";
        editor.appendChild(document.createTextNode({json.dumps(desc)}));
        editor.dispatchEvent(new Event('input', {{bubbles: true}}));
        editor.dispatchEvent(new Event('change', {{bubbles: true}}));
        r.push('desc ok');
    }}
    
    // 设置价格
    var inputs = document.querySelectorAll("input.ant-input");
    if(inputs.length >= 2) {{
        var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(inputs[0], '{price}');
        inputs[0].dispatchEvent(new Event('input', {{bubbles: true}}));
        nativeSetter.call(inputs[1], '{int(price*1.5)}');
        inputs[1].dispatchEvent(new Event('input', {{bubbles: true}}));
        r.push('price ok');
    }}
    
    // 选择无需邮寄
    var radios = document.querySelectorAll("input.ant-radio-input");
    if(radios.length >= 4) {{
        radios[3].click();
        radios[3].dispatchEvent(new Event('change', {{bubbles: true}}));
        r.push('shipping ok');
    }}
    
    // 上传图片
    var fileInput = document.querySelector("input[type=file]");
    if(fileInput) {{
        var b64 = '{img_b64}';
        var bc = atob(b64);
        var ba = new Uint8Array(bc.length);
        for(var i=0; i<bc.length; i++) ba[i] = bc.charCodeAt(i);
        var blob = new Blob([ba], {{type: 'image/png'}});
        var file = new File([blob], 'p{idx}.png', {{type: 'image/png'}});
        var dt = new DataTransfer();
        dt.items.add(file);
        var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'files').set;
        ns.call(fileInput, dt.files);
        fileInput.dispatchEvent(new Event('input', {{bubbles: true}}));
        fileInput.dispatchEvent(new Event('change', {{bubbles: true}}));
        r.push('img ok');
    }}
    
    return r.join(', ');
}})()
"""
    result = run_xb(f"eval '{js_code}'")
    log(f"  表单填写: {result[:100]}")
    time.sleep(1)
    
    # 6. 获取snapshot找发布按钮
    snap = run_xb("snapshot -i")
    time.sleep(0.5)
    
    # 7. 点击发布
    for ref_num in [9, 8, 7]:  # 尝试不同的ref编号
        result = run_xb(f"click e{ref_num}")
        if '"ok": true' in result:
            log(f"  点击发布按钮 e{ref_num}")
            break
    time.sleep(3)
    
    # 8. 检查结果
    check = run_xb("eval 'window.location.href'")
    log(f"  发布结果: {check[:150]}")
    
    if "item?id=" in check:
        item_id = check.split("item?id=")[1].split("&")[0]
        log(f"  ✅ 发布成功! ID: {item_id}")
        return True
    else:
        log(f"  ❌ 发布失败")
        return False

def main():
    log("=" * 50)
    log("闲鱼自动发布系统启动")
    
    products = get_products()
    log(f"获取到 {len(products)} 个产品")
    
    success = 0
    fail = 0
    
    for i, product in enumerate(products[:5]):  # 每次最多发5个
        try:
            if publish_product(product, i):
                success += 1
            else:
                fail += 1
            # 间隔随机时间 30-60秒
            delay = random.randint(30, 60)
            log(f"  等待 {delay}秒 后发布下一个...")
            time.sleep(delay)
        except Exception as e:
            log(f"  错误: {e}")
            fail += 1
    
    log(f"\n完成! 成功: {success}, 失败: {fail}")

if __name__ == "__main__":
    main()
