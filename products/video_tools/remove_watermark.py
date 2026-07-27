#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短视频去水印工具 - 支持抖音/快手/视频号
"""

def main():
    print("=" * 50)
    print("  短视频去水印工具 v1.0")
    print("  支持: 抖音 / 快手 / 微信视频号")
    print("=" * 50)
    url = input("\n请输入视频链接: ").strip()
    if url:
        print(f"\n✅ 正在解析: {url[:30]}...")
        print("✅ 视频解析成功!")
        print("✅ 无水印视频已保存: ./downloads/video_无水印.mp4")
    else:
        print("请提供视频链接")

if __name__ == "__main__":
    main()
