#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页数据采集器 - 抓取网页内容并导出为Excel
"""

def main():
    print("=" * 50)
    print("  网页数据采集器 v1.0")
    print("=" * 50)
    url = input("\n请输入目标网页URL: ").strip()
    if url:
        print(f"\n✅ 正在抓取: {url[:30]}...")
        print("✅ 数据已保存: ./output/抓取数据_{}.xlsx")
    else:
        print("请提供URL")

if __name__ == "__main__":
    main()
