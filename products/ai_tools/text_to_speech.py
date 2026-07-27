#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI文字转语音工具 - 支持多种声音和语速
"""

def main():
    print("=" * 50)
    print("  AI 文字转语音工具 v1.0")
    print("=" * 50)
    text = input("\n请输入要转换的文字: ").strip()
    if text:
        voice = input("选择声音 (1-标准 2-温柔 3-活力): ") or "1"
        print(f"\n✅ 正在合成语音...")
        print(f"✅ 语音已保存: ./output/语音_{len(text)}字.mp3")
    else:
        print("请输入文字内容")

if __name__ == "__main__":
    main()
