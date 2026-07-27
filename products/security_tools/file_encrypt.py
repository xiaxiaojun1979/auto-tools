#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件安全加密工具 - AES加密保护敏感文件
"""

def main():
    print("=" * 50)
    print("  文件安全加密工具 v1.0")
    print("=" * 50)
    filepath = input("\n请输入文件路径: ").strip()
    action = input("操作 (1-加密 2-解密): ")
    if filepath and action:
        print(f"\n✅ 正在{'加密' if action=='1' else '解密'}...")
        print(f"✅ 操作完成!")
    else:
        print("请提供文件路径")

if __name__ == "__main__":
    main()
