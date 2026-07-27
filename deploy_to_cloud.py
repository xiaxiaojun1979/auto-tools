#!/usr/bin/env python3
"""
云部署脚本 - 自动部署到 Railway.app
使用方法: python3 deploy_to_cloud.py
"""
import os, sys, subprocess, json, webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))

def check_files():
    required = ['requirements.txt', 'Procfile', 'railway.json', 'delivery/order_server.py']
    for f in required:
        if not os.path.exists(os.path.join(BASE, f)):
            print(f"❌ 缺少文件: {f}")
            return False
    print("✅ 所有部署文件就绪")
    return True

def show_guide():
    print("""
╔══════════════════════════════════════════════════╗
║     🚀 一键部署到云端指南                        ║
║     3分钟上线，无需任何技术知识                   ║
╚══════════════════════════════════════════════════╝

📋 部署步骤：

第一步 📦 上传代码到 GitHub
   1. 打开 https://github.com 注册账号（5分钟）
   2. 点击右上角 "+" → "New repository"
   3. 仓库名填: auto-business
   4. 创建后，把本文件夹所有文件拖入上传
   5. 点击 "Commit changes"

第二步 🚄 部署到 Railway
   1. 打开 https://railway.app 
   2. 用 GitHub 账号登录
   3. 点击 "New Project" → "Deploy from GitHub repo"
   4. 选择刚创建的 auto-business 仓库
   5. Railway 自动部署 ✅（2分钟）
   
   或使用一键部署按钮（如果有 GitHub 仓库后）:
   [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/auto-business)

第三步 🌐 获取公网地址
   1. 部署完成后点击 "Generate Domain"
   2. 你会得到一个 https://xxx.up.railway.app 地址
   3. 这就是你的产品网站！

📌 你的收款信息：
   💳 支付宝: 15156215580
   💚 微信: website/assets/wechat_pay.jpg

📊 管理后台: https://你的域名/admin

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
部署后有任何问题，随时问我！
""")

if __name__ == "__main__":
    print("\n🚀 AutoTools 云部署工具\n")
    if not check_files():
        sys.exit(1)
    show_guide()
    # Try to open the guides
    try:
        webbrowser.open('https://railway.app')
    except:
        pass
