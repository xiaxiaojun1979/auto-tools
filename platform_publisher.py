#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoTools 多平台自动发布系统
支持：今日头条、百家号
定时每晚20:00自动发布
"""

import json, os, subprocess, sys, re, time, random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "daily_report"
DATA_DIR = BASE_DIR / "promotion" / "data"
XB_PATH = os.path.expanduser("~/.qclaw/skills/xbrowser/scripts/xb.cjs")
NODE_BIN = os.path.expanduser("~/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node")
DATA_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = {
    "engineering": {"name": "工程行业趋势", "keywords": ["BIM技术", "智慧工地", "装配式建筑", "工程人", "项目经理"]},
    "tech": {"name": "科技科普", "keywords": ["人工智能", "自动化工具", "效率提升", "办公技巧"]},
    "health": {"name": "健康养生", "keywords": ["工程人健康", "职业病预防", "养生之道", "体力恢复"]}
}

BAIJIAHAO_PHONE = "15156215580"

def log(msg):
    log_file = LOG_DIR / "platform_publisher.log"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(line + "\n")

def xb(*args, timeout=30):
    cmd = [NODE_BIN, XB_PATH, "run", "--browser", "chrome", "--timeout", str(timeout)] + list(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        output = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return None, "Exit code %d: %s" % (result.returncode, err[:200])
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def parse_xb_output(output) -> dict:
    if not output:
        return {"ok": False, "error": "No output"}
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"ok": False, "error": "Parse failed: %s" % output[:100]}

def generate_article(category=None):
    if not category:
        category = random.choice(list(CATEGORIES.keys()))
    
    titles = {
        "engineering": [
            "工程人必看：%s正在改变行业格局" % random.choice(CATEGORIES["engineering"]["keywords"]),
            "做了20年工程，才发现%s才是未来" % random.choice(CATEGORIES["engineering"]["keywords"]),
            "工地上最吃香的岗位，不是项目经理而是它",
            "一个老工程人的真实感受：技术才是硬道理",
            "告别工地搬砖，这些技能让你身价翻倍",
        ],
        "tech": [
            "打工人必看！这些工具让你效率翻倍",
            "别再手动重复了，自动化才是你的救星",
            "AI时代来了，你的工作方式该升级了",
            "效率提升10倍的秘诀，今天告诉你",
        ],
        "health": [
            "工程人注意！这些习惯正在毁掉你的身体",
            "干工地的都看看，身体比赚钱更重要",
            "老工程人的养生经：干了20年工地身体还很好",
        ]
    }
    
    bodies = {
        "engineering": [
            "做了这么多年工程，越来越感觉到行业在悄悄变化。以前靠关系拿项目、靠经验管工地的日子，正在被新技术和新模式取代。\n\n拿BIM技术来说，现在稍微大点的项目，甲方第一个问题就是「有没有BIM应用能力」。会BIM的工程师月薪两万起步还不一定招得到人。更别提智慧工地、装配式建筑这些新方向，懂的人少，价格自然高。\n\n去年一个老同事，干了十几年施工员，累死累活一个月也就一万出头。后来花半年学了BIM，跳槽到咨询公司，直接翻倍。不是他多厉害，是市场缺人。\n\n所以工程人要明白，埋头苦干不如选对方向。门槛越高、人越少的岗位，才是真香。",
            "工地上有个奇怪的现象：项目经理看起来最风光，但实际上最累、最操心、还容易背锅。反而是那些「隐形冠军」岗位，干得轻松赚得多。\n\n商务经理就是典型。平时看着不起眼，但项目上的合同、结算、索赔全得靠他。一个项目干下来，光是变更索赔就能多出几百万的效益，老板自然愿意给高薪。\n\n安全总监也是。以前觉得这就是个背锅岗位，现在新安全生产法一出来，企业安全主体责任压得死死的。真正懂安全管理的，年薪三五十万很正常。\n\n还有测量工程师，全站仪、GPS、无人机航测，会的人真不多。测量是工程的眼睛，从开工到竣工全程都在，经验越老越值钱。\n\n说到底，选对方向比埋头苦干重要一万倍。",
            "工地上摸爬滚打这些年，发现一个规律：那些真正赚到钱的人，不是最辛苦的，而是最会用工具的。\n\n今年开工的项目，甲方明确要求必须上智慧工地系统。劳务实名制、环境监测、塔吊监控、质量巡检...一套系统下来几十万。谁会用这些系统？谁就值钱。\n\n再说说资料员。以前觉得资料员就是抄抄写写，没啥技术含量。现在不一样了，全过程资料管理、电子档案归档、竣工资料整理，专业资料员工资早就过万了。\n\n最让我感慨的是，很多工友宁愿在工地上风吹日晒，也不愿意花点时间学新东西。其实现在网上免费教程一大堆，每天学半小时，半年就能掌握一门新技术。\n\n时代变化太快了，不学习，真的会被淘汰。",
        ],
        "tech": [
            "每天坐在电脑前，总有做不完的表格、写不完的报告、回不完的消息。你有没有想过，这些重复劳动其实都可以自动化？\n\n我认识一个做行政的朋友，每天光整理Excel就要花两个小时。后来我用Python给她写了个脚本，一键完成数据清洗、格式统一、报表生成。现在她每天多出一小时学习。\n\n其实很多工作都是这样：80%的时间在做20%有创造价值的事，剩下80%的时间全在重复劳动。把这些重复劳动交给工具，你就能专注于真正重要的事。\n\n现在的AI工具越来越强大，从文案写作到图片处理再到数据分析，几乎覆盖了所有办公场景。关键是要会用，用对了工具效率提升10倍不是梦。\n\n别再说什么「没时间学习了」，每天少刷半小时短视频，足够你掌握一个能省下几小时工作的技巧。这笔账，怎么算都划算。",
            "打工人最怕什么？最怕加班。但更怕的是，加班干的全是重复劳动。\n\n你有没有这样的经历：同样的报表每周做一遍，同样的数据每天复制粘贴，同样的格式每次手动调整。这些工作，其实都能用工具自动完成。\n\n我见过最离谱的是，有人每天花4小时手动处理Excel，但一个VBA宏或者Python脚本就能在30秒内搞定。这中间的差距，就是工具的力量。\n\n现在的自动化工具已经很成熟了。文件批量处理、内容自动生成、数据清洗分析，都有现成的工具。关键是要敢用、会用。",
        ],
        "health": [
            "工地上干了十几年，见过太多拿命换钱的兄弟。其实工程人最该投资的，不是技术不是人脉，而是自己的身体。\n\n先说腰。长期弯腰干活、搬重物，腰椎间盘突出几乎是工程人的职业病。别等到疼得直不起腰才重视，现在开始：搬东西用腿不用腰、每隔一小时伸直腰板、晚上热敷理疗。\n\n再说膝盖。每天上万步是常态，但很多人走路姿势不对，膝盖磨损严重。买双好点的减震鞋，比什么都管用。\n\n还有肩膀。长期用电脑画图、看手机，肩颈问题越来越年轻化。每天做三组扩胸运动，坚持一个月，效果立竿见影。\n\n身体是革命的本钱，这话老套但真实。工程人，请善待自己的身体。",
        ]
    }
    
    title = random.choice(titles.get(category, titles["engineering"]))
    body = random.choice(bodies.get(category, bodies["engineering"]))
    
    # ===== 推广融入 =====
    # 根据文章分类自然融入推广CTA
    promo_footers = {
        "engineering": (
            "\n\n💡 想了解更多工程行业趋势？提升职场竞争力？\n"
            "我整理了一套「工程人效率工具包」，包含BIM学习资料、办公自动化脚本、"
            "一键生成报表工具等，让工作效率翻倍。\n"
            "👉 访问 https://xiaxiaojun.zeabur.app 免费获取"
        ),
        "tech": (
            "\n\n🚀 觉得这些技巧有用？\n"
            "我开发了一套「自动化工具集」，包含文件批量处理、内容自动生成、"
            "数据清洗分析等20+款效率工具，永久使用。\n"
            "👉 访问 https://xiaxiaojun.zeabur.app 了解更多"
        ),
        "health": (
            "\n\n💪 工程人的身体是革命的本钱！\n"
            "除了注意身体健康，工作效率也要提升。我整理的自动化工具"
            "帮你减少重复劳动，准时下班少加班。\n"
            "👉 访问 https://xiaxiaojun.zeabur.app 免费工具等你拿"
        )
    }
    
    # 50%概率融入推广尾注（避免每篇都推太刻意）
    if random.random() < 0.9:
        footer = promo_footers.get(category, promo_footers["engineering"])
        # 有时在正文中也自然提及（10%概率）
        if random.random() < 0.4:
            mid_insert = (
                "\n\n对了，我最近用了一个自动化工具集还挺好用的，"
                "批量处理文件、自动生成报表啥的都能搞定，省了不少时间。"
                "有兴趣的可以去 https://xiaxiaojun.zeabur.app 看看。"
            )
            # 插入到中间段落
            paras = body.split('\n\n')
            insert_pos = max(1, len(paras) // 2)
            paras.insert(insert_pos, mid_insert.strip())
            body = '\n\n'.join(paras)
        body = body + footer
    
    return {
        "title": title,
        "body": body.strip(),
        "category": category,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def generate_toutiao_article():
    return generate_article()

def generate_baijiahao_article():
    return generate_article()

def save_article(article, platform):
    platform_dir = DATA_DIR / platform
    platform_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = platform_dir / ("article_%s.json" % ts)
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    txt = platform_dir / ("article_%s.txt" % ts)
    txt.write_text("%s\n\n%s" % (article['title'], article['body']))
    return fp

def load_latest_article(platform):
    platform_dir = DATA_DIR / platform
    if not platform_dir.exists():
        return None
    files = sorted(platform_dir.glob("article_*.json"))
    if not files:
        return None
    try: return json.loads(files[-1].read_text())
    except: return None

def publish_toutiao(article=None):
    if not article:
        article = generate_toutiao_article()
        save_article(article, "toutiao")
    
    log("Starting Toutiao publish: %s" % article['title'])
    
    try:
        out, err = xb("open", "https://mp.toutiao.com/profile_v4/graphic/publish")
        if err:
            return {"ok": False, "platform": "toutiao", "error": "Open failed: %s" % err}
        
        time.sleep(3)
        xb("wait", "--load", "networkidle")
        
        out, err = xb("snapshot", "-i")
        if err:
            return {"ok": False, "platform": "toutiao", "error": "Snapshot failed: %s" % err}
        
        data = parse_xb_output(out)
        refs = data.get("data", {}).get("result", {}).get("data", {}).get("refs", {})
        
        # Check if login page
        for r in refs.values():
            if "登录" in (r.get("name", "") or ""):
                return {"ok": False, "platform": "toutiao", "error": "Need login", "action_required": "login"}
        
        # Find inputs
        title_ref = body_ref = publish_ref = None
        for rid, info in refs.items():
            n = info.get("name", "")
            r = info.get("role", "")
            if r == "textbox" and ("标题" in n or n == "" or "title" in n.lower()):
                if not title_ref: title_ref = rid
            if r == "button" and ("发布" in n or "发表" in n):
                publish_ref = rid
        
        if not title_ref:
            return {"ok": False, "platform": "toutiao", "error": "Cannot find title input"}
        
        xb("fill", title_ref, "'%s'" % article['title'])
        time.sleep(1)
        
        if publish_ref:
            xb("click", publish_ref)
            time.sleep(3)
        
        log("Toutiao published: %s" % article['title'])
        return {"ok": True, "platform": "toutiao", "title": article['title'], "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        log("Toutiao error: %s" % e)
        return {"ok": False, "platform": "toutiao", "error": str(e)}

def publish_baijiahao(article=None, sms_code=None):
    if not article:
        article = generate_baijiahao_article()
        save_article(article, "baijiahao")
    
    log("Starting Baijiahao publish: %s" % article['title'])
    
    try:
        out, err = xb("open", "https://baijiahao.baidu.com/")
        if err:
            return {"ok": False, "platform": "baijiahao", "error": "Open failed: %s" % err}
        
        time.sleep(3)
        xb("wait", "--load", "networkidle")
        
        out, err = xb("snapshot", "-i")
        data = parse_xb_output(out)
        refs = data.get("data", {}).get("result", {}).get("data", {}).get("refs", {})
        
        # Try to find and click login button
        login_btn = None
        for rid, info in refs.items():
            n = info.get("name", "")
            r = info.get("role", "")
            if r == "button" and "登录" in n:
                login_btn = rid
                break
        
        if login_btn:
            xb("click", login_btn)
            time.sleep(2)
            xb("wait", "--load", "networkidle")
            
            out, _ = xb("snapshot", "-i")
            data = parse_xb_output(out)
            refs = data.get("data", {}).get("result", {}).get("data", {}).get("refs", {})
        
        # Check for SMS login option
        phone_input = send_btn = None
        for rid, info in refs.items():
            n = info.get("name", "")
            r = info.get("role", "")
            if "短信" in n:
                # Click SMS tab
                xb("click", rid)
                time.sleep(1)
                xb("wait", "--load", "networkidle")
                out2, _ = xb("snapshot", "-i")
                data2 = parse_xb_output(out2)
                for rid2, info2 in data2.get("data", {}).get("result", {}).get("data", {}).get("refs", {}).items():
                    n2 = info2.get("name", "")
                    r2 = info2.get("role", "")
                    if r2 == "textbox" and "手机" in n2:
                        phone_input = rid2
                    if r2 == "button" and "发送" in n2:
                        send_btn = rid2
                break
        
        if phone_input and send_btn:
            xb("fill", phone_input, BAIJIAHAO_PHONE)
            time.sleep(1)
            # Check agree checkbox
            for rid, info in refs.items():
                if info.get("role") == "checkbox":
                    xb("click", rid)
                    time.sleep(0.5)
                    break
            xb("click", send_btn)
            time.sleep(1)
            
            if sms_code:
                out3, _ = xb("snapshot", "-i")
                data3 = parse_xb_output(out3)
                for rid, info in data3.get("data", {}).get("result", {}).get("data", {}).get("refs", {}).items():
                    if info.get("role") == "textbox" and "验证码" in info.get("name", ""):
                        xb("fill", rid, sms_code)
                        time.sleep(1)
                        break
                for rid, info in data3.get("data", {}).get("result", {}).get("data", {}).get("refs", {}).items():
                    if info.get("role") == "button" and info.get("name", "") == "登录":
                        xb("click", rid)
                        time.sleep(3)
                        break
            else:
                return {"ok": False, "platform": "baijiahao", "error": "Need SMS code", "action_required": "sms_code", "phone": BAIJIAHAO_PHONE}
        
        # Try to navigate to publish page
        xb("open", "https://baijiahao.baidu.com/builder/rc/edit")
        time.sleep(3)
        xb("wait", "--load", "networkidle")
        
        out, _ = xb("snapshot", "-i")
        data = parse_xb_output(out)
        refs = data.get("data", {}).get("result", {}).get("data", {}).get("refs", {})
        
        # Find publish elements
        title_ref = submit_ref = None
        for rid, info in refs.items():
            n = info.get("name", "")
            r = info.get("role", "")
            if r == "textbox" and ("标题" in n or n == ""):
                if not title_ref: title_ref = rid
            if r == "button" and "发布" in n:
                submit_ref = rid
        
        if not title_ref:
            return {"ok": False, "platform": "baijiahao", "error": "Cannot find editor fields", "action_required": "manual"}
        
        xb("fill", title_ref, "'%s'" % article['title'])
        time.sleep(1)
        
        if submit_ref:
            xb("click", submit_ref)
            time.sleep(3)
        
        log("Baijiahao published: %s" % article['title'])
        return {"ok": True, "platform": "baijiahao", "title": article['title'], "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    except Exception as e:
        log("Baijiahao error: %s" % e)
        return {"ok": False, "platform": "baijiahao", "error": str(e)}

def run_publish_all(sms_code=None):
    results = {}
    ta = generate_toutiao_article()
    save_article(ta, "toutiao")
    results["toutiao"] = publish_toutiao(ta)
    ba = generate_baijiahao_article()
    save_article(ba, "baijiahao")
    results["baijiahao"] = publish_baijiahao(ba, sms_code)
    
    record = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "results": results}
    record_file = DATA_DIR / "publish_log.json"
    logs = []
    if record_file.exists():
        try:
            logs = json.loads(record_file.read_text())
            if not isinstance(logs, list): logs = []
        except: logs = []
    logs.append(record)
    record_file.write_text(json.dumps(logs, ensure_ascii=False, indent=2))
    return results

def get_publish_history(days=7):
    record_file = DATA_DIR / "publish_log.json"
    if not record_file.exists(): return []
    try:
        logs = json.loads(record_file.read_text())
        if not isinstance(logs, list): return []
        cutoff = datetime.now().timestamp() - days * 86400
        results = []
        for entry in logs:
            try:
                dt = datetime.strptime(entry.get("timestamp", ""), "%Y-%m-%d %H:%M:%S")
                if dt.timestamp() > cutoff: results.append(entry)
            except: pass
        return results
    except: return []

def get_publish_stats():
    history = get_publish_history(30)
    total = len(history)
    success = sum(1 for h in history if all(r.get("ok") for r in h.get("results", {}).values()))
    toutiao_ok = sum(1 for h in history if h.get("results", {}).get("toutiao", {}).get("ok"))
    baijiahao_ok = sum(1 for h in history if h.get("results", {}).get("baijiahao", {}).get("ok"))
    return {
        "total_publish": total, "success": success, "failed": total - success,
        "toutiao_published": toutiao_ok, "baijiahao_published": baijiahao_ok,
        "last_publish": history[-1]["timestamp"] if history else "无"
    }

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "publish"
    code = sys.argv[2] if len(sys.argv) > 2 else None
    if cmd == "publish":
        print(json.dumps(run_publish_all(code), ensure_ascii=False, indent=2))
    elif cmd == "generate":
        print(json.dumps(generate_article(), ensure_ascii=False, indent=2))
    elif cmd == "stats":
        print(json.dumps(get_publish_stats(), ensure_ascii=False, indent=2))
    else:
        print("Usage: python3 platform_publisher.py [publish|generate|stats]")
