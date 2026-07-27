#!/usr/bin/env python3
"""
自动营销引擎 - 自动生成内容 + 排期 + 发布跟踪
"""

import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
import sys
import random

# 加入上级目录
sys.path.insert(0, str(Path(__file__).parent.parent / "products" / "content_gen"))
from main import ContentGenerator


class AutoMarketing:
    """自动营销引擎"""

    def __init__(self):
        self.generator = ContentGenerator()
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)

        # 发布平台配置（等你授权后填写）
        self.platforms = {
            "xiaohongshu": {"enabled": False, "api_key": ""},
            "douyin": {"enabled": False, "api_key": ""},
            "bilibili": {"enabled": False, "api_key": ""},
            "twitter": {"enabled": False, "api_key": ""},
        }

    def generate_weekly_plan(self, days=7):
        """生成一周内容计划"""
        print(f"\n📋 正在生成 {days} 天内容计划...")
        plan = self.generator.generate_content_plan(days=days, posts_per_day=2)
        return plan

    def save_plan(self, plan):
        """保存计划"""
        filepath = self.data_dir / f"plan_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        print(f"[✓] 内容计划已保存: {filepath}")
        return filepath

    def show_pending_posts(self):
        """显示待发布的帖子"""
        plans = sorted(self.data_dir.glob("plan_*.json"), reverse=True)
        if not plans:
            print("[!] 没有待发布的内容计划")
            return []

        today = datetime.now().strftime("%Y-%m-%d")
        pending = []

        for plan_file in plans[:1]:
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan = json.load(f)

            for post in plan:
                if post.get("scheduled_date") >= today:
                    pending.append(post)

        if pending:
            print(f"\n📆 待发布内容 ({len(pending)} 条):\n")
            print(f"{'日期':<14} {'时间':<8} {'分类':<12} {'标题':<30}")
            print("-"*64)
            for p in pending:
                print(f"{p['scheduled_date']:<14} {p['scheduled_time']:<8} "
                      f"{p['category']:<12} {p['title'][:28]:<30}")
        else:
            print("[!] 当天没有待发布内容")

        return pending

    def export_marketing_report(self, plan, filepath=None):
        """导出营销报告"""
        if filepath is None:
            filepath = self.data_dir / f"report_{datetime.now().strftime('%Y%m%d')}.md"

        cats = {}
        for p in plan:
            cat = p['category']
            cats[cat] = cats.get(cat, 0) + 1

        report = f"""# 自动营销周报

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 本周内容概览

| 分类 | 数量 |
|------|------|
"""
        for cat, count in cats.items():
            report += f"| {cat} | {count} |\n"

        report += f"\n总计: {len(plan)} 条内容\n"

        report += f"""
## 📅 发布日历

| 日期 | 时间 | 分类 | 标题 |
|------|------|------|------|
"""
        for p in plan:
            report += f"| {p['scheduled_date']} | {p['scheduled_time']} | {p['category']} | {p['title']} |\n"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"[✓] 营销报告已导出: {filepath}")
        return filepath

    def configure_platform(self, platform, api_key):
        """配置发布平台（等你提供信息）"""
        if platform in self.platforms:
            self.platforms[platform]["api_key"] = api_key
            self.platforms[platform]["enabled"] = True
            # 保存配置
            config_path = self.data_dir / "platforms.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.platforms, f, ensure_ascii=False, indent=2)
            print(f"[✓] {platform} 配置完成")
        else:
            print(f"[X] 未知平台: {platform}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🚀 自动营销引擎")
    subparsers = parser.add_subparsers(dest="command")

    p_plan = subparsers.add_parser("plan", help="生成内容计划")
    p_plan.add_argument("--days", type=int, default=7, help="计划天数")

    subparsers.add_parser("pending", help="查看待发布内容")
    subparsers.add_parser("report", help="导出营销报告")

    args = parser.parse_args()

    engine = AutoMarketing()

    if args.command == "plan":
        plan = engine.generate_weekly_plan(args.days)
        engine.save_plan(plan)
        engine.show_pending_posts()
        engine.export_marketing_report(plan)

    elif args.command == "pending":
        engine.show_pending_posts()

    elif args.command == "report":
        plans = sorted(engine.data_dir.glob("plan_*.json"), reverse=True)
        if plans:
            with open(plans[0], 'r', encoding='utf-8') as f:
                plan = json.load(f)
            engine.export_marketing_report(plan)
        else:
            print("[!] 没有内容计划，请先生成: python3 auto_publisher.py plan")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
