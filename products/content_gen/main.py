#!/usr/bin/env python3
"""
社交媒体内容自动生成器 (Social Media Content Generator v1.0)
Author: AutoTools Studio
自动生成小红书/抖音/B站/推特帖子文案 + 标签 + 多平台适配
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import csv

# ==================== 内容模板库 ====================

CONTENT_TEMPLATES = {
    "效率工具": {
        "tone": ["实用", "干货", "简洁"],
        "headlines": [
            "用了这个工具，我每天省出2小时",
            "打工人必看！{n}个提效神器",
            "效率翻倍的秘密，藏在这个工具里",
            "别人加班我下班，因为用了这个",
            "{n}岁程序员推荐的{n}个自动化工具",
        ],
        "hooks": [
            "你是否每天都在做重复性的工作？",
            "这可能是你今年看到最实用的工具推荐。",
            "作为一个每天处理大量文件的人，我找到了救星。",
            "如果早点知道这个，我能少加多少班...",
        ],
        "bodies": [
            "今天给大家分享一个我每天都在用的自动化工具。它帮我处理了{feature}，原来需要{n}分钟的工作，现在{time}秒搞定。",
            "我花了一周时间整理了{n}个实用功能，全部都是亲身测试过的好用。从{feature}到{feature2}，一站式解决。",
            "最近发现了一个效率神器，忍不住要分享给所有人。特别是如果你经常需要处理{feature}，这个工具简直是为你量身定做。",
        ],
        "ctas": [
            "需要的评论区扣1，我私信发你",
            "关注我，获取更多效率工具推荐",
            "点赞收藏，下次需要的时候直接翻出来",
            "评论区告诉我你最想解决什么效率问题",
        ]
    },
    "副业赚钱": {
        "tone": ["真实", "激励", "实操"],
        "headlines": [
            "靠这个副业，我月入{n}k",
            "普通人也能做的{n}个副业（亲测有效）",
            "不上班第{n}天，我的收入来源是...",
            "别再只会打工了，这{n}个副业思路拿走",
            "从0到月入过万，我只做了这一件事",
        ],
        "hooks": [
            "说实话，以前我也不信副业能赚钱。",
            "先别急着划走，这可能是你今年看到的副业干货。",
            "很多人问我怎么开始副业，今天统一回答。",
        ],
        "bodies": [
            "很多人不知道，其实用电脑自动完成重复工作，就是一个很好的副业方向。比如{feature}，写一次脚本就能反复用。",
            "我总结了三步法：第一{feature}，第二{feature2}，第三{feature3}。按这个步骤来，你也能做出自己的产品。",
            "最关键的一点是：不要追求完美。先做出一个能用的版本，然后根据反馈不断优化。我第一个产品只卖{n}块钱，现在已经迭代到{n}版本了。",
        ],
        "ctas": [
            "想了解具体怎么做的，评论区告诉我",
            "关注我，每天分享一个副业思路",
            "收藏这个帖子，需要的时候拿出来看",
        ]
    },
    "编程技巧": {
        "tone": ["技术", "实用", "简洁"],
        "headlines": [
            "{n}行代码搞定{feature}，Python太强了",
            "程序员必知的{n}个自动化脚本",
            "这个Python脚本让我从重复工作中解放了",
            "一行代码，解决{feature}的烦恼",
        ],
        "hooks": [
            "作为一个程序员，最不能忍的就是重复劳动。",
            "代码写得好，下班走得早。",
            "分享一个我私藏的脚本，看完你会回来感谢我。",
        ],
        "bodies": [
            "核心逻辑很简单：{explanation}。只需要{n}行代码，就能自动完成{feature}。",
            "我把它封装成了一个命令行工具，支持{feature}和{feature2}两种模式。使用方式：{usage}",
            "这个脚本我已经用了{n}个月了，稳定可靠。代码开源在GitHub上，需要的自取。",
        ],
        "ctas": [
            "源码已放在GitHub，评论区取链接",
            "关注我，分享更多实用脚本",
            "想要更多类似脚本？点赞告诉我",
        ]
    }
}

HASHTAG_POOLS = {
    "效率工具": [
        "#效率工具", "#职场效率", "#自动化办公", "#Python", "#办公技巧",
        "#时间管理", "#打工人必备", "#生产力工具", "#文件处理", "#批量处理",
        "#数码办公", "#效率提升", "#工作流", "#自动化", "#提效"
    ],
    "副业赚钱": [
        "#副业", "#副业赚钱", "#搞钱", "#被动收入", "#斜杠青年",
        "#搞钱思维", "#副业推荐", "#月入过万", "#互联网副业", "#知识付费",
        "#睡后收入", "#轻资产创业", "#个人IP", "#数字产品", "#自动化变现"
    ],
    "编程技巧": [
        "#Python", "#编程", "#自动化脚本", "#程序员", "#代码",
        "#编程技巧", "#效率工具", "#开源", "#爬虫", "#数据清洗",
        "#后端开发", "#脚本", "#命令行", "#技术分享", "#干货"
    ]
}


class ContentGenerator:
    """内容生成器"""

    def __init__(self, category="效率工具", language="zh"):
        self.category = category
        self.language = language
        self.templates = CONTENT_TEMPLATES.get(category, CONTENT_TEMPLATES["效率工具"])

    def set_category(self, category):
        if category in CONTENT_TEMPLATES:
            self.category = category
            self.templates = CONTENT_TEMPLATES[category]
        else:
            print(f"[!] 未知分类: {category}，可用: {list(CONTENT_TEMPLATES.keys())}")

    def generate_post(self, features=None, count=1, include_hashtags=True):
        """生成单条帖子"""
        posts = []
        for _ in range(count):
            headline = random.choice(self.templates["headlines"])
            hook = random.choice(self.templates["hooks"])
            body = random.choice(self.templates["bodies"])
            cta = random.choice(self.templates["ctas"])
            tone = random.choice(self.templates["tone"])

            # 填充变量
            n_val = random.randint(2, 10)
            time_val = random.choice([3, 5, 10, 30, 60])
            features = features or ["文件批量处理", "图片压缩", "格式转换", "自动备份", "重复文件清理"]
            feat = random.choice(features)
            feat2 = random.choice([f for f in features if f != feat]) if len(features) > 1 else feat

            replacements = {
                "{feature}": feat,
                "{feature2}": feat2,
                "{feature3}": random.choice(features),
                "{n}": str(n_val),
                "{time}": str(time_val),
                "{explanation}": f"用Python的Pathlib库遍历目录，通过文件后缀名过滤，调用PIL进行图片处理",
                "{usage}": f"python3 main.py compress ./images --quality 80",
            }

            for k, v in replacements.items():
                headline = headline.replace(k, v)
                hook = hook.replace(k, v)
                body = body.replace(k, v)
                cta = cta.replace(k, v)

            # 组装
            post = f"{headline}\n\n{hook}\n\n{body}\n\n{cta}"

            if include_hashtags:
                tags = self._generate_hashtags(count=random.randint(3, 6))
                post += "\n\n" + " ".join(tags)

            posts.append({
                "title": headline.split("\n")[0][:50],
                "category": self.category,
                "tone": tone,
                "content": post,
                "hashtags": tags if include_hashtags else [],
                "generated_at": datetime.now().isoformat(),
            })

        return posts if count > 1 else posts[0]

    def generate_batch(self, num_posts=5, categories=None):
        """批量生成多分类帖子"""
        all_posts = []
        cats = categories or list(CONTENT_TEMPLATES.keys())

        for i in range(num_posts):
            cat = random.choice(cats)
            self.set_category(cat)
            post = self.generate_post(count=1)
            all_posts.append(post)

        return all_posts

    def _generate_hashtags(self, count=5):
        """生成标签"""
        pool = HASHTAG_POOLS.get(self.category, HASHTAG_POOLS["效率工具"])
        return random.sample(pool, min(count, len(pool)))

    def export_to_csv(self, posts, filepath="posts.csv"):
        """导出到CSV"""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=["title", "category", "tone", "content", "hashtags", "generated_at"])
            w.writeheader()
            for p in posts:
                p['hashtags'] = ' '.join(p['hashtags'])
                w.writerow(p)
        print(f"[✓] 已导出 {len(posts)} 条帖子到 {filepath}")

    def export_to_json(self, posts, filepath="posts.json"):
        """导出到JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)
        print(f"[✓] 已导出 {len(posts)} 条帖子到 {filepath}")

    def generate_content_plan(self, days=7, posts_per_day=2):
        """生成本周内容计划"""
        cats = list(CONTENT_TEMPLATES.keys())
        plan = []
        start = datetime.now()

        for d in range(days):
            day = start + timedelta(days=d)
            for p in range(posts_per_day):
                cat = random.choice(cats)
                self.set_category(cat)
                post = self.generate_post(count=1)
                post["scheduled_date"] = day.strftime("%Y-%m-%d")
                post["scheduled_time"] = f"{random.choice(['09', '12', '18', '20'])}:{random.choice(['00', '30'])}"
                plan.append(post)

        return plan


def main():
    parser = argparse.ArgumentParser(
        description="📝 社交媒体内容自动生成器 v1.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 生成1条帖子
  python3 main.py generate

  # 生成5条帖子并导出
  python3 main.py generate --count 5 --export csv

  # 指定分类
  python3 main.py generate --category 副业赚钱

  # 生成一周内容计划
  python3 main.py plan --days 7 --posts-per-day 2

  # 查看可用分类
  python3 main.py categories
        """
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # generate
    p_gen = subparsers.add_parser("generate", help="生成帖子")
    p_gen.add_argument("--category", choices=list(CONTENT_TEMPLATES.keys()), default="效率工具",
                       help="内容分类")
    p_gen.add_argument("--count", type=int, default=1, help="生成数量")
    p_gen.add_argument("--export", choices=["csv", "json", "none"], default="none",
                       help="导出格式")
    p_gen.add_argument("--output", default="", help="输出文件路径")

    # plan
    p_plan = subparsers.add_parser("plan", help="生成内容计划")
    p_plan.add_argument("--days", type=int, default=7, help="计划天数")
    p_plan.add_argument("--posts-per-day", type=int, default=2, help="每天帖子数")
    p_plan.add_argument("--export", choices=["csv", "json"], default="json", help="导出格式")

    # categories
    subparsers.add_parser("categories", help="查看可用分类")

    args = parser.parse_args()
    gen = ContentGenerator()

    if not args.command or args.command == "categories":
        print("可用内容分类:\n")
        for cat in CONTENT_TEMPLATES:
            tones = ", ".join(CONTENT_TEMPLATES[cat]["tone"])
            print(f"  📂 {cat} [{tones}]")
        print()
        return

    if args.command == "generate":
        gen.set_category(args.category)
        posts = gen.generate_batch(num_posts=args.count)
        for i, p in enumerate(posts, 1):
            print(f"\n{'='*50}")
            print(f"  帖子 #{i} [{p['category']}]")
            print(f"{'='*50}")
            print(p['content'])
            print()

        if args.export != "none":
            fname = args.output or f"posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if args.export == "csv":
                gen.export_to_csv(posts, f"{fname}.csv")
            else:
                gen.export_to_json(posts, f"{fname}.json")

    elif args.command == "plan":
        plan = gen.generate_content_plan(args.days, args.posts_per_day)
        print(f"\n📋 内容计划 ({args.days}天, 每天{args.posts_per_day}篇)\n")
        print(f"{'日期':<14} {'时间':<8} {'分类':<12} {'标题':<30}")
        print("-"*64)
        for p in plan:
            title = p['title'][:28]
            print(f"{p['scheduled_date']:<14} {p['scheduled_time']:<8} {p['category']:<12} {title:<30}")

        if args.export == "csv":
            gen.export_to_csv(plan, f"content_plan_{datetime.now().strftime('%Y%m%d')}.csv")
        else:
            gen.export_to_json(plan, f"content_plan_{datetime.now().strftime('%Y%m%d')}.json")


if __name__ == "__main__":
    main()
