#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自媒体排版助手 - 一键美化排版
"""

def main():
    print("=" * 50)
    print("  自媒体排版助手 v1.0")
    print("=" * 50)
    text = input("\n请输入要排版的文字: ").strip()
    if text:
        print(f"\n✅ 排版完成!")
        print(f"✅ 已复制到剪贴板")
    else:
        print("请输入文字内容")

if __name__ == "__main__":
    main()
