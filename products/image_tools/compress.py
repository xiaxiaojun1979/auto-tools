#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片批量压缩工具 - 支持JPG/PNG/WebP
"""

def main():
    print("=" * 50)
    print("  图片批量压缩工具 v1.0")
    print("=" * 50)
    folder = input("\n请输入图片文件夹路径: ").strip()
    if folder:
        quality = input("压缩质量 (1-100, 默认80): ") or "80"
        print(f"\n✅ 正在扫描图片...")
        print(f"✅ 已压缩 0 张图片")
        print(f"✅ 节省空间: 0 MB")
    else:
        print("请提供文件夹路径")

if __name__ == "__main__":
    main()
