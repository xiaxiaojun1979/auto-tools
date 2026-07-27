#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 AutoTools 高价值服务目录
目标：提升客单价，创造更高收益
"""

SERVICES = [
    {
        "id": "deploy_service",
        "emoji": "\\U0001f4e6",
        "name": "代部署服务",
        "desc": "帮你把工具部署到自己的电脑上，远程安装调试一条龙",
        "features": [
            "远程协助安装配置",
            "环境依赖自动安装",
            "使用教程一对一讲解",
            "常见问题排查",
            "保证正常运行"
        ],
        "price": 99,
        "price_old": 199,
        "type": "service",
        "revenue_priority": 3,
    },
    {
        "id": "custom_dev",
        "emoji": "\\U0001f3ed",
        "name": "定制开发",
        "desc": "根据你的需求定制专属工具，完全按你的业务场景设计",
        "features": [
            "需求分析与方案设计",
            "专属工具开发",
            "测试与优化",
            "部署安装",
            "7天售后维护"
        ],
        "price": 499,
        "price_old": 999,
        "type": "service",
        "revenue_priority": 5,
    },
    {
        "id": "enterprise_pkg",
        "emoji": "\\U0001f3e2",
        "name": "企业批量部署",
        "desc": "为团队/公司批量部署工具，含统一管理和培训",
        "features": [
            "多台电脑批量部署",
            "统一配置管理",
            "团队使用培训",
            "专属售后服务群",
            "月度使用报告"
        ],
        "price": 999,
        "price_old": 1999,
        "type": "service",
        "revenue_priority": 5,
    },
    {
        "id": "maintenance",
        "emoji": "\\U0001f527",
        "name": "年度维护套餐",
        "desc": "全年技术支持 + 免费更新 + 优先响应",
        "features": [
            "全年不限次技术支持",
            "所有工具免费更新",
            "4小时内响应",
            "数据备份与恢复",
            "专属技术支持群"
        ],
        "price": 299,
        "price_old": 599,
        "type": "subscription",
        "revenue_priority": 4,
    },
    {
        "id": "vip_custom",
        "emoji": "\\U0001f451",
        "name": "企业VIP定制",
        "desc": "全套工具 + 定制开发 + 年度维护 + 专属客服",
        "features": [
            "全部现有工具授权",
            "2次定制开发额度",
            "全年技术支持",
            "优先响应(2小时)",
            "专属客户经理"
        ],
        "price": 2999,
        "price_old": 5999,
        "type": "enterprise",
        "revenue_priority": 5,
    }
]

def get_high_value_services():
    """获取高收益服务"""
    return sorted(SERVICES, key=lambda x: x["revenue_priority"], reverse=True)

def get_total_revenue_potential():
    """所有服务一次购买的总金额"""
    return sum(s["price"] for s in SERVICES)

if __name__ == "__main__":
    total = get_total_revenue_potential()
    print("高价值服务目录:")
    print("=" * 40)
    for s in SERVICES:
        print("  {} {}  ¥{}{}".format(
            s["emoji"] if s["emoji"].startswith("\\U") else "🔹",
            s["name"], s["price"],
            " (高收益优先)" if s["revenue_priority"] >= 4 else ""))
    print("=" * 40)
    print("  全套服务总价值: ¥{}".format(total))
